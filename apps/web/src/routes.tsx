import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { VisualizersListPage } from './pages/VisualizersListPage';
import { VisualizerDetailPage } from './pages/VisualizerDetailPage';
import { ProblemListPage } from './pages/ProblemListPage';
import { ProblemDetailPage } from './pages/ProblemDetailPage';
import { QuizPage } from './pages/QuizPage';
import { GuidedPathsPage } from './pages/GuidedPathsPage';
import { GuidedPathDetailPage } from './pages/GuidedPathDetailPage';

import { NotFound } from './components/NotFound';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/visualizers" element={<VisualizersListPage />} />
      <Route path="/visualizers/:id" element={<VisualizerDetailPage />} />
      <Route path="/learn" element={<GuidedPathsPage />} />
      <Route path="/learn/:id" element={<GuidedPathDetailPage />} />
      <Route path="/problems/:topic" element={<ProblemListPage />} />
      <Route path="/problems/:topic/:slug" element={<ProblemDetailPage />} />
      <Route path="/quiz/:topic" element={<QuizPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};
