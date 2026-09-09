import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';

import { LandingPage } from './pages/LandingPage';
import { NotFound } from './components/NotFound';

// Code splitting / lazy-loaded routes for performance & modular chunking
const DashboardPage = lazy(() =>
  import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const VisualizersListPage = lazy(() =>
  import('./pages/VisualizersListPage').then((m) => ({ default: m.VisualizersListPage }))
);
const VisualizerDetailPage = lazy(() =>
  import('./pages/VisualizerDetailPage').then((m) => ({ default: m.VisualizerDetailPage }))
);
const ProblemListPage = lazy(() =>
  import('./pages/ProblemListPage').then((m) => ({ default: m.ProblemListPage }))
);
const ProblemDetailPage = lazy(() =>
  import('./pages/ProblemDetailPage').then((m) => ({ default: m.ProblemDetailPage }))
);
const QuizPage = lazy(() =>
  import('./pages/QuizPage').then((m) => ({ default: m.QuizPage }))
);
const GuidedPathsPage = lazy(() =>
  import('./pages/GuidedPathsPage').then((m) => ({ default: m.GuidedPathsPage }))
);
const GuidedPathDetailPage = lazy(() =>
  import('./pages/GuidedPathDetailPage').then((m) => ({ default: m.GuidedPathDetailPage }))
);
const ExamsPage = lazy(() =>
  import('./pages/ExamsPage').then((m) => ({ default: m.ExamsPage }))
);
const ExamDetailPage = lazy(() =>
  import('./pages/ExamDetailPage').then((m) => ({ default: m.ExamDetailPage }))
);
const LoginPage = lazy(() =>
  import('./pages/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const RegisterPage = lazy(() =>
  import('./pages/RegisterPage').then((m) => ({ default: m.RegisterPage }))
);
const AdminPage = lazy(() =>
  import('./pages/AdminPage').then((m) => ({ default: m.AdminPage }))
);
const ProfilePage = lazy(() =>
  import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);

const RouteLoadingFallback: React.FC = () => (
  <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 space-y-3">
    <RefreshCw className="w-6 h-6 text-mint animate-spin" />
    <span className="text-xs font-mono text-muted">Loading module...</span>
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/visualizers" element={<VisualizersListPage />} />
        <Route path="/visualizers/:id" element={<VisualizerDetailPage />} />
        <Route path="/learn" element={<GuidedPathsPage />} />
        <Route path="/learn/:id" element={<GuidedPathDetailPage />} />
        <Route path="/problems/:topic" element={<ProblemListPage />} />
        <Route path="/problems/:topic/:slug" element={<ProblemDetailPage />} />
        <Route path="/quiz/:topic" element={<QuizPage />} />
        <Route path="/exams" element={<ExamsPage />} />
        <Route path="/exams/:id" element={<ExamDetailPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
};
