import { useState, useEffect } from 'react';
import { BASE_URL } from '../api';
import './AnalyticsDashboard.css';

const AnalyticsDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BASE_URL}/api/analytics`);
      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }
      const jsonData = await response.json();
      setData(jsonData);
      setError(null);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Could not load analytics. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner" />
        <p>Loading analytics data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <p>{error}</p>
        <button type="button" onClick={fetchAnalytics}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h2>Analytics Dashboard</h2>
        <button type="button" className="refresh-btn" onClick={fetchAnalytics}>
          <span className="icon">↻</span> Refresh
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-title">Total Campaigns</div>
          <div className="stat-value">{data.total_campaigns}</div>
        </div>
        <div className="stat-card blue">
          <div className="stat-title">Emails Attempted</div>
          <div className="stat-value">{data.total_emails_attempted}</div>
        </div>
        <div className="stat-card green">
          <div className="stat-title">Successful Emails</div>
          <div className="stat-value">{data.total_emails_sent}</div>
        </div>
        <div className="stat-card red">
          <div className="stat-title">Failed Emails</div>
          <div className="stat-value">{data.total_emails_failed}</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-title">Success Rate</div>
          <div className="stat-value">{data.success_rate}%</div>
        </div>
      </div>

      <div className="recent-campaigns">
        <h3>Recent Campaigns</h3>
        {data.recent_campaigns && data.recent_campaigns.length > 0 ? (
          <div className="table-responsive">
            <table className="campaigns-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Subject</th>
                  <th>Total</th>
                  <th>Sent</th>
                  <th>Failed</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_campaigns.map((camp) => {
                  const date = new Date(camp.timestamp);
                  const formattedDate =
                    date.toLocaleDateString() +
                    ' ' +
                    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                  return (
                    <tr key={camp.id}>
                      <td>{formattedDate}</td>
                      <td className="subject-cell">{camp.subject}</td>
                      <td>{camp.total_attempted}</td>
                      <td className="success-text">{camp.successful}</td>
                      <td className="error-text">{camp.failed}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="no-data">
            <p>No email campaigns have been sent yet.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
