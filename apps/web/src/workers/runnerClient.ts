export interface ExecutionResult {
  passed: boolean;
  actual: any;
  expected: any;
  timeMs: number;
  error?: string;
}

export interface TestCaseInput {
  input: any[];
  expected: any;
}

const WORKER_CODE = `
self.onmessage = function(e) {
  var code = e.data.code;
  var functionName = e.data.functionName;
  var inputs = e.data.inputs;

  try {
    var runner = new Function(
      '"use strict";\\n' +
      code + ';\\n' +
      'if (typeof ' + functionName + ' === "function") return ' + functionName + ';\\n' +
      'if (typeof solve === "function") return solve;\\n' +
      'throw new Error("Function \`" + functionName + "\` is not defined.");'
    )();

    var result = runner.apply(null, inputs);
    self.postMessage({ success: true, result: result });
  } catch (err) {
    self.postMessage({
      success: false,
      error: err && err.message ? err.message : String(err)
    });
  }
};
`;

function deepEqual(a: any, b: any): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export async function runTestCasesInWorker(
  code: string,
  functionName: string,
  testCases: TestCaseInput[],
  timeoutMs: number = 3000
): Promise<{ results: ExecutionResult[]; allPassed: boolean }> {
  const results: ExecutionResult[] = [];
  let allPassed = true;

  // Check if Worker is supported in environment (browser vs node/jsdom)
  const isWorkerSupported = typeof Worker !== 'undefined';

  for (const tc of testCases) {
    const clonedInputs = JSON.parse(JSON.stringify(tc.input));
    const start = performance.now();

    if (!isWorkerSupported) {
      // Direct sandboxed eval fallback for non-worker test environments
      try {
        const runner = new Function(
          `"use strict";
           ${code};
           if (typeof ${functionName} === 'function') return ${functionName};
           if (typeof solve === 'function') return solve;
           throw new Error("Function '${functionName}' is not defined.");`
        )();
        const actual = runner(...clonedInputs);
        const end = performance.now();
        const passed = deepEqual(actual, tc.expected);
        if (!passed) allPassed = false;

        results.push({
          passed,
          actual,
          expected: tc.expected,
          timeMs: Math.max(0.1, Number((end - start).toFixed(2))),
        });
      } catch (err: any) {
        allPassed = false;
        results.push({
          passed: false,
          actual: null,
          expected: tc.expected,
          timeMs: 0,
          error: err?.message || 'Runtime Error',
        });
      }
      continue;
    }

    // Browser Web Worker execution
    let worker: Worker | null = null;
    try {
      const blob = new Blob([WORKER_CODE], { type: 'application/javascript' });
      const blobUrl = URL.createObjectURL(blob);
      worker = new Worker(blobUrl);

      const runPromise = new Promise<{ success: boolean; result?: any; error?: string }>(
        (resolve) => {
          worker!.onmessage = (e) => resolve(e.data);
          worker!.onerror = (e) => resolve({ success: false, error: e.message || 'Worker Error' });
        }
      );

      worker.postMessage({
        code,
        functionName,
        inputs: clonedInputs,
      });

      const timeoutPromise = new Promise<{ success: boolean; error: string }>((resolve) => {
        setTimeout(() => {
          resolve({ success: false, error: `Time Limit Exceeded (>${timeoutMs}ms limit)` });
        }, timeoutMs);
      });

      const outcome = await Promise.race([runPromise, timeoutPromise]);
      const end = performance.now();

      if (!outcome.success) {
        allPassed = false;
        results.push({
          passed: false,
          actual: null,
          expected: tc.expected,
          timeMs: Number((end - start).toFixed(2)),
          error: outcome.error,
        });
      } else {
        const passed = deepEqual(outcome.result, tc.expected);
        if (!passed) allPassed = false;
        results.push({
          passed,
          actual: outcome.result,
          expected: tc.expected,
          timeMs: Math.max(0.1, Number((end - start).toFixed(2))),
        });
      }
    } finally {
      if (worker) {
        worker.terminate();
      }
    }
  }

  return { results, allPassed };
}
