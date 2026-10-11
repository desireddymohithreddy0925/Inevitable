
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import Landing from './pages/Landing';
import Console from './pages/Console';
import CustomCursor from './components/CustomCursor';
import './index.css';

function App() {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div>
      <CustomCursor />
      {/* Navigation Header */}
      <header className="app-header">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div className="brand">
            <div className="brand-icon">I</div>
            <div className="brand-title">Inevitable</div>
          </div>
        </Link>
        <nav className="nav-links">
          <Link to="/" className={`nav-link ${path === '/' ? 'active' : ''}`}>Overview</Link>
          <Link to="/console" className={`nav-link ${path === '/console' ? 'active' : ''}`}>Verification Console</Link>
        </nav>
      </header>

      {/* Main Content Area */}
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/console" element={<Console />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
