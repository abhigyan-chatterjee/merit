import { BrowserRouter } from 'react-router-dom';
import { ProgressProvider } from './store/ProgressContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { AppRoutes } from './routes';

export function App() {
  return (
    <ProgressProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-canvas text-ink selection:bg-mint/20 selection:text-mint">
          <Navbar />
          <main className="flex-1">
            <AppRoutes />
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </ProgressProvider>
  );
}

export default App;
