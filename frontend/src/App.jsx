import { Routes, Route, Link, useLocation } from 'react-router-dom';
import Onboarding from './pages/Onboarding';
import Recommendations from './pages/Recommendations';

function App() {
  const location = useLocation();

  return (
    <div className="app">
      <header className="app-header">
        <div className="container flex items-center justify-between">
          <div className="logo">
            <span className="logo-dot"></span>
            CineMatch
          </div>
          <nav className="nav-links">
            <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>Discover</Link>
            <Link to="/recommendations" className={`nav-link ${location.pathname === '/recommendations' ? 'active' : ''}`}>My Matches</Link>
          </nav>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Onboarding />} />
          <Route path="/recommendations" element={<Recommendations />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
