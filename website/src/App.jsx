import { useState } from 'react';
import './App.css';
import EmailForm from './components/EmailForm';
import AnalyticsDashboard from './components/AnalyticsDashboard';

function App() {
  const [activeTab, setActiveTab] = useState('sender');

  return (
    <>
      <nav className="top-nav">
        <div className="nav-brand">Harish Critical Care Classes</div>
        <div className="nav-tabs">
          <button
            type="button"
            className={`nav-tab ${activeTab === 'sender' ? 'active' : ''}`}
            onClick={() => setActiveTab('sender')}
          >
            Email Sender
          </button>
          <button
            type="button"
            className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            Analytics Data
          </button>
        </div>
      </nav>

      <div className="form-bg-wrapper">
        {activeTab === 'sender' ? <EmailForm /> : <AnalyticsDashboard />}
      </div>

      <footer className="footer-powered">
        Powered By{' '}
        <a
          href="https://www.krintix.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="footer-link"
        >
          krintix.com
        </a>
      </footer>
    </>
  );
}

export default App;
