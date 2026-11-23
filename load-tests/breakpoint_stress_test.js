import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('custom_error_rate');
const healthDuration = new Trend('health_req_duration', true);
const problemsListDuration = new Trend('problems_list_duration', true);
const problemDetailDuration = new Trend('problem_detail_duration', true);
const pathsDuration = new Trend('paths_duration', true);
const questionsDuration = new Trend('questions_duration', true);
const visualizersDuration = new Trend('visualizers_duration', true);

const TARGET_URL = __ENV.TARGET_URL || 'http://127.0.0.1:8000';

export const options = {
  stages: [
    { duration: '15s', target: 5 },   // Phase 1: Baseline warm-up (5 VUs)
    { duration: '30s', target: 20 },  // Phase 2: Moderate load (20 VUs)
    { duration: '30s', target: 50 },  // Phase 3: High load (50 VUs)
    { duration: '30s', target: 100 }, // Phase 4: Stress load (100 VUs)
    { duration: '30s', target: 150 }, // Phase 5: Peak breakpoint test (150 VUs)
    { duration: '15s', target: 0 },   // Phase 6: Recovery cooldown (0 VUs)
  ],
  thresholds: {
    // Record failures if error rate spikes beyond 10% or p95 latency exceeds 2.5s
    http_req_failed: ['rate<0.10'],
    http_req_duration: ['p(95)<2500'],
  },
};

const SAMPLE_PROBLEMS = [
  'two-sum',
  'valid-parentheses',
  'reverse-linked-list',
  'best-time-to-buy-and-sell-stock',
  'contains-duplicate',
  '3sum',
  'binary-search',
];

export default function () {
  const headers = {
    'Accept': 'application/json',
    'User-Agent': 'k6-load-simulator/1.0',
  };

  // 1. Health check baseline (fast in-memory endpoint)
  const healthRes = http.get(`${TARGET_URL}/api/v1/health`, { headers });
  healthDuration.add(healthRes.timings.duration);
  const healthOk = check(healthRes, {
    'health status is 200': (r) => r.status === 200,
  });
  errorRate.add(!healthOk);
  sleep(0.1);

  // 2. Problem catalog list (database query)
  const problemsRes = http.get(`${TARGET_URL}/api/v1/problems`, { headers });
  problemsListDuration.add(problemsRes.timings.duration);
  const problemsOk = check(problemsRes, {
    'problems list status is 200': (r) => r.status === 200,
    'problems list has items': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body) && body.length > 0;
      } catch (e) {
        return false;
      }
    },
  });
  errorRate.add(!problemsOk);
  sleep(0.2);

  // 3. Problem detail (database lookup by slug)
  const randomProblem = SAMPLE_PROBLEMS[Math.floor(Math.random() * SAMPLE_PROBLEMS.length)];
  const detailRes = http.get(`${TARGET_URL}/api/v1/problems/${randomProblem}`, { headers });
  problemDetailDuration.add(detailRes.timings.duration);
  const detailOk = check(detailRes, {
    'problem detail status is 200': (r) => r.status === 200,
    'problem detail has correct slug': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && body.slug === randomProblem;
      } catch (e) {
        return false;
      }
    },
  });
  errorRate.add(!detailOk);
  sleep(0.2);

  // 4. Learning paths catalog
  const pathsRes = http.get(`${TARGET_URL}/api/v1/paths`, { headers });
  pathsDuration.add(pathsRes.timings.duration);
  const pathsOk = check(pathsRes, {
    'paths status is 200': (r) => r.status === 200,
  });
  errorRate.add(!pathsOk);
  sleep(0.2);

  // 5. Visualizers catalog
  const visualizersRes = http.get(`${TARGET_URL}/api/v1/visualizers`, { headers });
  visualizersDuration.add(visualizersRes.timings.duration);
  const visualizersOk = check(visualizersRes, {
    'visualizers status is 200': (r) => r.status === 200,
  });
  errorRate.add(!visualizersOk);
  sleep(0.1);

  // 6. Quiz questions sampler (sampling query)
  const questionsRes = http.get(`${TARGET_URL}/api/v1/questions?limit=10`, { headers });
  questionsDuration.add(questionsRes.timings.duration);
  const questionsOk = check(questionsRes, {
    'questions status is 200': (r) => r.status === 200,
  });
  errorRate.add(!questionsOk);
  sleep(0.3);
}
