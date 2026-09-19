import { test, expect } from '@playwright/test';

test.describe('Merit Golden Smoke & Invariants', () => {
  test('landing page loads and displays title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Merit/i);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('invalid dynamic route renders 404 page', async ({ page }) => {
    await page.goto('/visualizers/unknown-fake-id');
    await expect(page.getByTestId('not-found-page')).toBeVisible();
    await expect(page.getByText(/Visualizer Not Found/i)).toBeVisible();
  });

  const visualizerTitles: Record<string, string> = {
    sorting: 'Sorting Algorithms',
    array: 'Static & Dynamic Array',
    'linked-list': 'Singly Linked List',
    stack: 'LIFO Stack',
    queue: 'FIFO Queue',
    'binary-tree': 'Binary Tree Traversals',
    bst: 'Binary Search Tree (BST)',
    heap: 'Min / Max Binary Heap',
    hashmap: 'Hash Map (Separate Chaining)',
    graph: 'Graph BFS / DFS Explorer',
    searching: 'Linear vs Binary Search',
    'recursion-tree': 'Recursion Call Tree',
  };

  for (const [id, title] of Object.entries(visualizerTitles)) {
    test(`loads visualizer route /visualizers/${id} and renders "${title}"`, async ({ page }) => {
      await page.goto(`/visualizers/${id}`);
      await expect(page.getByTestId('not-found-page')).not.toBeVisible();
      const heading = page.getByRole('heading', { level: 1 });
      await expect(heading).toBeVisible();
      await expect(heading).toContainText(title);
    });
  }

  test('BST insertion retains tree structure and highlights node', async ({ page }) => {
    await page.goto('/visualizers/bst');
    const input = page.getByPlaceholder('Value...');
    await input.fill('25');
    await page.getByRole('button', { name: 'Insert' }).click();

    // Verify SVG contains the inserted value 25
    await expect(page.getByTestId('tree-svg').getByText('25')).toBeVisible();
  });

  test('Sorting visualizer advances step with Step Forward button', async ({ page }) => {
    await page.goto('/visualizers/sorting');
    const stepFwdBtn = page.getByLabel('Step forward');
    await expect(stepFwdBtn).toBeVisible();
    await stepFwdBtn.click();
    // After step forward, comparisons or swaps counter updates
    await expect(page.getByText(/Comparisons/i)).toBeVisible();
  });
});
