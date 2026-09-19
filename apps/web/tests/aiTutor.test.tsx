import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AiTutor } from '../src/components/AiTutor';

const TEST_KEY = 'sk-test-sentinel-9f8e7d6c5b4a';
const MODELS = ['gpt-4o-mini', 'gpt-4o'];
const REPLY = 'Think about what a hash map gives you.';

function jsonOk(payload: unknown): Response {
  return { ok: true, status: 200, json: async () => payload } as Response;
}

interface CapturedCall {
  url: string;
  init?: RequestInit;
}

/** Route mocked fetch by URL. Unhandled paths (e.g. judge submissions) get `fallback`. */
function mockFetch(
  routes: Record<'models' | 'chat', (body: Record<string, unknown>) => unknown>,
  calls: CapturedCall[],
  fallback: unknown = []
) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input);
    calls.push({ url, init });
    if (url.includes('/api/v1/tutor/models')) {
      const body = JSON.parse(String((init as RequestInit)?.body ?? '{}'));
      return jsonOk(routes.models(body));
    }
    if (url.includes('/api/v1/tutor/chat')) {
      const body = JSON.parse(String((init as RequestInit)?.body ?? '{}'));
      return jsonOk(routes.chat(body));
    }
    return jsonOk(fallback);
  });
}

function expandPanel() {
  fireEvent.click(screen.getByRole('button', { name: /ask the tutor/i }));
}

describe('AiTutor (BYOK tutor panel)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it('renders the key prompt empty: no key stored, remember unchecked', () => {
    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();

    expect(screen.getByLabelText(/api key/i)).toHaveValue('');
    expect(screen.getByLabelText(/provider base url/i)).toHaveValue(
      'https://api.openai.com/v1'
    );
    expect(screen.getByLabelText(/remember on this device/i)).not.toBeChecked();
    expect(
      screen.getByText(/key stays on your device \+ provider/i)
    ).toBeInTheDocument();
    expect(window.localStorage.getItem('merit_tutor_api_key')).toBeNull();
  });

  it('keeps the key memory-only by default; persists only with opt-in remember', async () => {
    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();

    fireEvent.change(screen.getByLabelText(/api key/i), {
      target: { value: TEST_KEY },
    });
    expect(window.localStorage.getItem('merit_tutor_api_key')).toBeNull();

    fireEvent.click(screen.getByLabelText(/remember on this device/i));
    await waitFor(() => {
      expect(window.localStorage.getItem('merit_tutor_api_key')).toBe(TEST_KEY);
    });
  });

  it('lists models on mocked fetch (Check models button)', async () => {
    const calls: CapturedCall[] = [];
    let modelsBody: Record<string, unknown> = {};
    mockFetch(
      {
        models: (body) => {
          modelsBody = body;
          return { models: MODELS };
        },
        chat: () => ({ reply: REPLY }),
      },
      calls
    );

    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();

    fireEvent.change(screen.getByLabelText(/api key/i), {
      target: { value: TEST_KEY },
    });
    fireEvent.click(screen.getByRole('button', { name: /check models/i }));

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'gpt-4o-mini' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'gpt-4o' })).toBeInTheDocument();
    });
    // Frozen 5.1 contract: { base_url, api_key } in, { models } out.
    expect(modelsBody).toMatchObject({
      base_url: 'https://api.openai.com/v1',
      api_key: TEST_KEY,
    });
    expect(calls.some((c) => c.url.includes(TEST_KEY))).toBe(false);
  });

  it('sends chat with {problem_slug, model} and shows the reply', async () => {
    const calls: CapturedCall[] = [];
    let chatBody: Record<string, unknown> = {};
    mockFetch(
      {
        models: () => ({ models: MODELS }),
        chat: (body) => {
          chatBody = body;
          return { reply: REPLY };
        },
      },
      calls
    );

    render(<AiTutor problemSlug="two-sum" code="def solve(): pass" />);
    expandPanel();

    fireEvent.change(screen.getByLabelText(/api key/i), {
      target: { value: TEST_KEY },
    });
    fireEvent.click(screen.getByRole('button', { name: /check models/i }));
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'gpt-4o-mini' })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText(/^model$/i), {
      target: { value: 'gpt-4o-mini' },
    });
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: 'I am stuck on brute force, what next?' },
    });
    fireEvent.click(screen.getByRole('button', { name: /send question/i }));

    await waitFor(() => {
      expect(screen.getByText(REPLY)).toBeInTheDocument();
    });
    expect(chatBody).toMatchObject({
      problem_slug: 'two-sum',
      model: 'gpt-4o-mini',
      base_url: 'https://api.openai.com/v1',
      api_key: TEST_KEY,
      code: 'def solve(): pass',
      question: 'I am stuck on brute force, what next?',
      failed_attempts: 0,
    });
    expect(screen.getByText('I am stuck on brute force, what next?')).toBeInTheDocument();
  });

  it('derives failed_attempts from the judge submissions data flow', async () => {
    const calls: CapturedCall[] = [];
    let chatBody: Record<string, unknown> = {};
    mockFetch(
      {
        models: () => ({ models: MODELS }),
        chat: (body) => {
          chatBody = body;
          return { reply: REPLY };
        },
      },
      calls,
      [{ verdict: 'WA' }, { verdict: 'AC' }, { verdict: 'TLE' }]
    );

    render(<AiTutor problemSlug="two-sum" />);
    expandPanel();

    fireEvent.change(screen.getByLabelText(/api key/i), {
      target: { value: TEST_KEY },
    });
    // Submissions fetch fires on expand: 2 of 3 are non-AC failures.
    await waitFor(() => {
      expect(
        calls.some((c) => c.url.includes('/api/v1/judge/submissions/two-sum'))
      ).toBe(true);
    });

    fireEvent.click(screen.getByRole('button', { name: /check models/i }));
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'gpt-4o-mini' })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/^model$/i), {
      target: { value: 'gpt-4o-mini' },
    });
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: 'Give me a nudge.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /send question/i }));

    await waitFor(() => {
      expect(screen.getByText(REPLY)).toBeInTheDocument();
    });
    expect(chatBody.failed_attempts).toBe(2);
  });

  it('NEVER renders the key value into the DOM', async () => {
    const calls: CapturedCall[] = [];
    mockFetch(
      {
        models: () => ({ models: MODELS }),
        chat: () => ({ reply: REPLY }),
      },
      calls
    );

    const { container } = render(<AiTutor problemSlug="two-sum" />);
    expandPanel();

    fireEvent.change(screen.getByLabelText(/api key/i), {
      target: { value: TEST_KEY },
    });
    fireEvent.click(screen.getByRole('button', { name: /check models/i }));
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'gpt-4o-mini' })).toBeInTheDocument();
    });
    fireEvent.change(screen.getByLabelText(/^model$/i), {
      target: { value: 'gpt-4o-mini' },
    });
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: 'Help me think.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /send question/i }));
    await waitFor(() => {
      expect(screen.getByText(REPLY)).toBeInTheDocument();
    });

    expect(container.innerHTML).not.toContain(TEST_KEY);
    expect(document.body.textContent ?? '').not.toContain(TEST_KEY);
    // Key travels in POST bodies only — never in request URLs.
    for (const c of calls) {
      expect(c.url).not.toContain(TEST_KEY);
    }
  });
});
