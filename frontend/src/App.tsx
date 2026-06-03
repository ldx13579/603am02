import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import RepoManagement from './pages/RepoManagement';
import ReportDetail from './pages/ReportDetail';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>Git Habits</h2>
          </div>
          <nav>
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/repos">Repositories</NavLink>
          </nav>
        </aside>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/repos" element={<RepoManagement />} />
            <Route path="/repos/:repoId" element={<ReportDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
