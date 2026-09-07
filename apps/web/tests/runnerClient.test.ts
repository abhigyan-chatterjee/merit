import { describe, it, expect } from 'vitest';
import { runTestCasesInWorker } from '../src/workers/runnerClient';

describe('Sandboxed Code Runner (D6)', () => {
  it('correctly executes a passing solution and passes all test cases', async () => {
    const code = `
      function twoSum(nums, target) {
        const map = new Map();
        for (let i = 0; i < nums.length; i++) {
          const comp = target - nums[i];
          if (map.has(comp)) return [map.get(comp), i];
          map.set(nums[i], i);
        }
        return [];
      }
    `;

    const testCases = [
      { input: [[2, 7, 11, 15], 9], expected: [0, 1] },
      { input: [[3, 2, 4], 6], expected: [1, 2] },
      { input: [[3, 3], 6], expected: [0, 1] },
    ];

    const { results, allPassed } = await runTestCasesInWorker(code, 'twoSum', testCases);
    expect(allPassed).toBe(true);
    expect(results.length).toBe(3);
    expect(results.every((r) => r.passed)).toBe(true);
  });

  it('detects incorrect logic and returns failure', async () => {
    const wrongCode = `
      function twoSum(nums, target) {
        return [0, 0]; // wrong
      }
    `;

    const testCases = [{ input: [[2, 7, 11, 15], 9], expected: [0, 1] }];

    const { results, allPassed } = await runTestCasesInWorker(wrongCode, 'twoSum', testCases);
    expect(allPassed).toBe(false);
    expect(results[0].passed).toBe(false);
    expect(results[0].actual).toEqual([0, 0]);
  });

  it('captures syntax errors and runtime exceptions gracefully', async () => {
    const brokenCode = `
      function twoSum(nums, target) {
        throw new Error('Exploded unexpectedly');
      }
    `;

    const testCases = [{ input: [[1, 2], 3], expected: [0, 1] }];

    const { results, allPassed } = await runTestCasesInWorker(brokenCode, 'twoSum', testCases);
    expect(allPassed).toBe(false);
    expect(results[0].error).toMatch(/Exploded unexpectedly/);
  });
});
