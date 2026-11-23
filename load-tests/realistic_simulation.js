import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('custom_error_rate');
const readDuration = new Trend('read_duration', true);
const submitDuration = new Trend('submit_duration', true);

const TARGET_URL = __ENV.TARGET_URL || 'http://127.0.0.1:8000';
const VUS = parseInt(__ENV.VUS || '10', 10);
const DURATION = __ENV.DURATION || '20s';

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    http_req_failed: ['rate<0.10'], // Less than 10% errors
    http_req_duration: ['p(95)<3000'], // 95% under 3s
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

const PYTHON_TWO_SUM = `def solve(nums, target):
    lookup = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in lookup:
            return [lookup[diff], i]
        lookup[n] = i
`;

export default function () {
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'User-Agent': 'k6-load-sim/1.0',
  };

  // Weighted behavior: ~70% Read Heavy, 30% Problem Submissions
  const rand = Math.random();

  if (rand < 0.70) {
    // 70% Read Heavy User: Problems, Visualizers, Paths, Mock Quizzes
    const subAction = Math.random();

    if (subAction < 0.30) {
      // Problem catalog & detail
      const problem = SAMPLE_PROBLEMS[Math.floor(Math.random() * SAMPLE_PROBLEMS.length)];
      const res = http.get(`${TARGET_URL}/api/v1/problems/${problem}`, { headers });
      readDuration.add(res.timings.duration);
      const ok = check(res, { 'problem detail 200': (r) => r.status === 200 });
      errorRate.add(!ok);
    } else if (subAction < 0.55) {
      // Visualizer catalog
      const res = http.get(`${TARGET_URL}/api/v1/visualizers`, { headers });
      readDuration.add(res.timings.duration);
      const ok = check(res, { 'visualizers 200': (r) => r.status === 200 });
      errorRate.add(!ok);
    } else if (subAction < 0.80) {
      // Learning paths
      const res = http.get(`${TARGET_URL}/api/v1/paths`, { headers });
      readDuration.add(res.timings.duration);
      const ok = check(res, { 'paths 200': (r) => r.status === 200 });
      errorRate.add(!ok);
    } else {
      // Quizzes / Mock exam questions
      const res = http.get(`${TARGET_URL}/api/v1/questions?limit=10`, { headers });
      readDuration.add(res.timings.duration);
      const ok = check(res, { 'questions 200': (r) => r.status === 200 });
      errorRate.add(!ok);
    }
  } else {
    // 30% Problem Submissions (Judge Run / Execution via Cloud Run)
    const payload = JSON.stringify({
      problem_slug: 'two-sum',
      language: 'python',
      code: PYTHON_TWO_SUM,
    });

    const res = http.post(`${TARGET_URL}/api/v1/judge/run`, payload, { headers });
    submitDuration.add(res.timings.duration);
    const ok = check(res, {
      'judge run 200': (r) => r.status === 200,
      'judge run AC': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body && body.verdict === 'AC';
        } catch (e) {
          return false;
        }
      },
    });
    errorRate.add(!ok);
  }

  // Think time between actions
  sleep(0.5);
}
