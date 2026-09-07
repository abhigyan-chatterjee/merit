/**
 * Sandboxed Web Worker Code Runner
 * Runs code off the main thread with no access to DOM (window, document) or localStorage.
 */

self.onmessage = (e: MessageEvent<{ code: string; functionName: string; inputs: any[] }>) => {
  const { code, functionName, inputs } = e.data;

  try {
    // Restrict global access inside worker
    const runner = new Function(
      `"use strict";
       ${code};
       if (typeof ${functionName} === 'function') {
         return ${functionName};
       }
       if (typeof solve === 'function') {
         return solve;
       }
       throw new Error('Function "${functionName}" is not defined.');`
    )();

    const result = runner(...inputs);
    self.postMessage({ success: true, result });
  } catch (err: any) {
    self.postMessage({
      success: false,
      error: err?.message || String(err) || 'Runtime Error',
    });
  }
};
