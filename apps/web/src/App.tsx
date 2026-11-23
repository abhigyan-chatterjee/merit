import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './store/AuthContext';
import { ProgressProvider } from './store/ProgressContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { AppRoutes } from './routes';

export function App() {
  return (
    <AuthProvider>
      <ProgressProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-canvas text-ink selection:bg-mint/20 selection:text-mint">
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-3 focus:py-2 focus:rounded-lg focus:bg-mint focus:text-canvas focus:font-mono focus:text-xs"
            >
              Skip to content
            </a>
            <Navbar />
            <main id="main-content" className="flex-1">
              <AppRoutes />
            </main>
            <Footer />
          </div>
        </BrowserRouter>
      </ProgressProvider>
    </AuthProvider>
  );
}

export default App;
