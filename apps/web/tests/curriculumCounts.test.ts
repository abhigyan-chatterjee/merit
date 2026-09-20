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

const bankCounts = (): Record<string, number> => {
  const counts: Record<string, number> = {};
  for (const file of readdirSync(problemsDir)) {
    if (!file.endsWith('.json') || file.startsWith('scrap-')) continue;
    const data = JSON.parse(readFileSync(path.join(problemsDir, file), 'utf-8'));
    const status = data.reviewStatus ?? data.review_status ?? 'verified';
    if (status === 'draft') continue;
    counts[data.topic] = (counts[data.topic] ?? 0) + 1;
  }
  return counts;
};

describe('curriculum TOPICS problemCount', () => {
  it('matches the verified problem bank per topic (140 total)', () => {
    const counts = bankCounts();
    const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
    expect(total).toBe(140);

    const topicSlugs = new Set(TOPICS.map((t) => t.slug));
    for (const slug of Object.keys(counts)) {
      expect(topicSlugs.has(slug), `bank topic "${slug}" missing from TOPICS`).toBe(true);
    }
    for (const topic of TOPICS) {
      expect(topic.problemCount, `topic ${topic.slug}`).toBe(counts[topic.slug] ?? 0);
    }
  });
});
