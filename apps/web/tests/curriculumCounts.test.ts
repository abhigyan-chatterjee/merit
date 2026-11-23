// @vitest-environment node
import { readFileSync, readdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { describe, expect, it } from 'vitest';
import { TOPICS } from '../src/data/curriculum';

const problemsDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../../content/problems'
);

const bankTopics = (): Set<string> => {
  const topics = new Set<string>();
  for (const file of readdirSync(problemsDir)) {
    if (!file.endsWith('.json') || file.startsWith('scrap-')) continue;
    const data = JSON.parse(readFileSync(path.join(problemsDir, file), 'utf-8'));
    const status = data.reviewStatus ?? data.review_status ?? 'verified';
    if (status === 'draft') continue;
    topics.add(data.topic);
  }
  return topics;
};

describe('curriculum TOPICS taxonomy coverage', () => {
  // Every problem is filed under a topic slug, and the problem list renders one
  // section per TOPICS entry. A problem carrying a slug that is not in TOPICS
  // would be counted in the totals but rendered in no section, so it would be
  // silently unreachable. Per-topic totals are not asserted here: the list page
  // counts problems live from the bank, so a stale number cannot drift in the UI.
  it('covers every topic used by the verified problem bank', () => {
    const topicSlugs = new Set(TOPICS.map((t) => t.slug));
    for (const slug of bankTopics()) {
      expect(topicSlugs.has(slug), `bank topic "${slug}" missing from TOPICS`).toBe(true);
    }
  });

  it('has unique, well-formed topic slugs', () => {
    const seen = TOPICS.map((t) => t.slug);
    expect(new Set(seen).size).toBe(seen.length);
    for (const slug of seen) {
      expect(slug).toMatch(/^[a-z0-9-]+$/);
    }
  });
});
