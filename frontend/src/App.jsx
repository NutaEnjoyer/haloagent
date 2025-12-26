import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import LaunchDemo from './components/LaunchDemo'
import StatusDemo from './components/StatusDemo'
import Analytics from './components/Analytics'
import History from './components/History'
import Templates from './components/Templates'
import Settings from './components/Settings'

function Navigation() {
  const location = useLocation()

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <header className="app-header">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>HALO</h1>
          <p className="subtitle">Платформа AI Ассистента</p>
        </div>

        <nav className="nav-links">
          <Link
            to="/"
            className={`nav-link ${isActive('/') && location.pathname === '/' ? 'active' : ''}`}
          >
            Главная
          </Link>
          <Link
            to="/launch"
            className={`nav-link ${isActive('/launch') ? 'active' : ''}`}
          >
            Запустить демо
          </Link>
          <Link
            to="/history"
            className={`nav-link ${isActive('/history') ? 'active' : ''}`}
          >
            История
          </Link>
          <Link
            to="/templates"
            className={`nav-link ${isActive('/templates') ? 'active' : ''}`}
          >
            Шаблоны
          </Link>
          <Link
            to="/settings"
            className={`nav-link ${isActive('/settings') ? 'active' : ''}`}
          >
            Настройки
          </Link>
        </nav>
      </div>
    </header>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />

        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/launch" element={<LaunchDemo />} />
            <Route path="/status/:sessionId" element={<StatusDemo />} />
            <Route path="/analytics/:sessionId" element={<Analytics />} />
            <Route path="/history" element={<History />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <p>© 2025 HALO by GINAI. Developed by Maxim Dolgov. All rights reserved. | Premium AI Voice Assistant</p>
        </footer>
      </div>
    </Router>
  )
}

export default App
