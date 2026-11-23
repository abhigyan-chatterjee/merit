import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { LessonNav } from '../src/components/LessonNav';
import { LEARNING_PATHS } from '../src/data/learningPaths';
import { VisualizerDetailPage } from '../src/pages/VisualizerDetailPage';
import { GuidedPathDetailPage } from '../src/pages/GuidedPathDetailPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { AuthProvider } from '../src/store/AuthContext';

function mockGuestFetch() {
  vi.spyOn(global, 'fetch').mockImplementation(async (url) => {
    const u = String(url);
    if (u.includes('/auth/me') || u.includes('/auth/refresh')) {
      return new Response(
        JSON.stringify({ error: { code: 'UNAUTHORIZED', message: 'Not logged in' } }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      );
    }
    if (u.includes('/api/v1/paths/')) {
      return new Response(JSON.stringify({ detail: { code: 'PATH_NOT_FOUND' } }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    if (u.includes('/api/v1/progress/')) {
      return new Response(JSON.stringify({}), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return new Response(JSON.stringify({}), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  });
}

function renderComponent(ui: React.ReactElement, initialEntry = '/') {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
          {ui}
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>
  );
}

describe('LessonNav & Unblocked Guided Path Flow', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
    mockGuestFetch();
  });

  it('renders LessonNav when arriving through a path link (?path=&step=)', async () => {
    renderComponent(<VisualizerDetailPage />, '/visualizers/array?path=foundation&step=0');

    // Should render LessonNav path back link and step indicator.
    // /visualizers/array matches several foundation steps; the first match wins.
    expect(await screen.findByText('Foundation')).toBeInTheDocument();
    expect(screen.getByText(/Step \d+ of \d+/)).toBeInTheDocument();
    expect(screen.getByText(/Next:/i)).toBeInTheDocument();
  });

  it('hides LessonNav on standalone visits without path params', async () => {
    renderComponent(<VisualizerDetailPage />, '/visualizers/array');

    await screen.findByText('Static & Dynamic Array');
    expect(screen.queryByLabelText('Path navigation')).not.toBeInTheDocument();
    expect(screen.queryByText('Foundation')).not.toBeInTheDocument();
  });

  it('allows manual changing of steps in GuidedPathDetailPage without pointer-events-none blocking', () => {
    renderComponent(<GuidedPathDetailPage />, '/learn/foundation');

    // All steps should be rendered and have valid links without pointer-events-none
    const stepLinks = screen.getAllByRole('link');
    const problemLinks = stepLinks.filter(l => l.getAttribute('href')?.includes('/problems/'));
    expect(problemLinks.length).toBeGreaterThan(0);

    // Assert that the second and third steps do NOT have pointer-events-none or aria-disabled
    for (const link of problemLinks) {
      expect(link).not.toHaveClass('pointer-events-none');
      expect(link).not.toHaveAttribute('aria-disabled', 'true');
    }
  });

  it('allows opening step dropdown in LessonNav and seeing curriculum', async () => {
    renderComponent(<VisualizerDetailPage />, '/visualizers/array?path=foundation&step=0');

    const stepButton = await screen.findByRole('button', { name: /Step \d+ of \d+/i });
    expect(stepButton).toBeInTheDocument();

    fireEvent.click(stepButton);
    expect(screen.getByText(/Foundation · Curriculum/i)).toBeInTheDocument();
  });

  it('shows the step summary guide in the path detail list', () => {
    renderComponent(<GuidedPathDetailPage />, '/learn/foundation');

    // Summaries come from the synced JSON mirror, not just titles.
    expect(
      screen.getByText(/contiguously for O\(1\) indexed access/i)
    ).toBeInTheDocument();
    // Further-reading links render alongside visualizer steps.
    expect(screen.getAllByText(/Further reading →/i).length).toBeGreaterThanOrEqual(1);
  });

  it('does not nest anchors in the step list (no <a> inside <a>) on /learn/foundation', () => {
    const { container } = renderComponent(<GuidedPathDetailPage />, '/learn/foundation');
    // External "Further reading" links must live outside the step <Link> so
    // anchors never nest -- the root cause of React's DOM nesting warning.
    expect(container.querySelector('a a')).toBeNull();
  });

  it('builds mock-step navigation links with a single ? separator', async () => {
    const path = LEARNING_PATHS.find((p) => p.id === 'targeted')!;
    const mockIndex = path.steps.findIndex((s) => s.type === 'mock');
    const currentStep = path.steps[mockIndex - 1];
    const expected = `/quiz/mixed?mock=true&path=targeted&step=${mockIndex}`;

    const LocationProbe = () => {
      const location = useLocation();
      return <div data-testid="nav-location">{location.pathname}{location.search}</div>;
    };

    render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter initialEntries={[`/quiz/${currentStep.id}?path=${path.id}&step=${mockIndex - 1}`]}>
            <LocationProbe />
            <LessonNav currentType="quiz" currentId={currentStep.id} />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );

    fireEvent.click(await screen.findByRole('button', { name: /Next:/i }));
    expect(screen.getByTestId('nav-location')).toHaveTextContent(expected);
    expect((screen.getByTestId('nav-location').textContent || '').match(/\?/g)).toHaveLength(1);

    fireEvent.click(await screen.findByRole('button', { name: /Step \d+ of \d+/i }));
    expect(screen.getByRole('link', { name: /Targeted placement mock/i })).toHaveAttribute(
      'href',
      expected
    );
  });
});
