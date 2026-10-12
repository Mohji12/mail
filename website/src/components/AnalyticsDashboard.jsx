import { useState, useEffect } from 'react';
import { BASE_URL } from '../api';
import './AnalyticsDashboard.css';

function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return (
    date.toLocaleDateString() +
    ' ' +
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  );
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function downloadCsv(filename, rows) {
  const escape = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = rows.map((r) => r.map(escape).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const AnalyticsDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [view, setView] = useState('today'); // today | week | all

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
      setError('Could not load admin report. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const exportTodayReport = () => {
    if (!data?.today) return;
    const rows = [
      ['Report Date', data.today.date],
      ['Campaigns Today', data.today.campaigns],
      ['Emails Attempted', data.today.attempted],
      ['Emails Sent Successfully', data.today.sent],
      ['Emails Failed', data.today.failed],
      ['Success Rate %', data.today.success_rate],
      [],
      ['Time', 'Subject', 'Attempted', 'Sent', 'Failed', 'Success Rate %'],
      ...(data.today.campaigns_list || []).map((c) => [
        formatDateTime(c.timestamp),
        c.subject,
        c.total_attempted,
        c.successful,
        c.failed,
        c.success_rate,
      ]),
    ];
    downloadCsv(`daily-email-report-${data.today.date}.csv`, rows);
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner" />
        <p>Loading admin report...</p>
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

  const today = data.today || {
    date: '—',
    campaigns: 0,
    attempted: 0,
    sent: 0,
    failed: 0,
    success_rate: 0,
    campaigns_list: [],
  };

  const guide = data.metric_guide || {};

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <div>
          <h2>Admin Daily Report</h2>
          <p className="report-subtitle">
            Daily email campaign summary for admins · Generated{' '}
            {formatDateTime(data.report_generated_at)}
          </p>
        </div>
        <div className="header-actions">
          <button type="button" className="refresh-btn" onClick={exportTodayReport}>
            Download today&apos;s CSV
          </button>
          <button type="button" className="refresh-btn" onClick={fetchAnalytics}>
            <span className="icon">↻</span> Refresh
          </button>
        </div>
      </div>

      <section className="report-section today-section">
        <div className="section-heading">
          <h3>Today&apos;s Report</h3>
          <span className="date-badge">{formatDate(today.date)}</span>
        </div>

        <div className="stats-grid">
          <div className="stat-card" title={guide.campaigns}>
            <div className="stat-title">Campaigns today</div>
            <div className="stat-value">{today.campaigns}</div>
            <div className="stat-hint">Bulk send jobs run today</div>
          </div>
          <div className="stat-card blue" title={guide.attempted}>
            <div className="stat-title">Emails attempted</div>
            <div className="stat-value">{today.attempted}</div>
            <div className="stat-hint">Recipients tried today</div>
          </div>
          <div className="stat-card green" title={guide.sent}>
            <div className="stat-title">Sent successfully</div>
            <div className="stat-value">{today.sent}</div>
            <div className="stat-hint">Accepted by mail provider</div>
          </div>
          <div className="stat-card red" title={guide.failed}>
            <div className="stat-title">Failed</div>
            <div className="stat-value">{today.failed}</div>
            <div className="stat-hint">Send errors today</div>
          </div>
          <div className="stat-card purple" title={guide.success_rate}>
            <div className="stat-title">Success rate</div>
            <div className="stat-value">{today.success_rate}%</div>
            <div className="stat-hint">Sent ÷ attempted</div>
          </div>
        </div>

        <h4 className="table-title">Campaigns sent today</h4>
        {today.campaigns_list?.length > 0 ? (
          <div className="table-responsive">
            <table className="campaigns-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Email subject</th>
                  <th>Attempted</th>
                  <th>Sent</th>
                  <th>Failed</th>
                  <th>Success %</th>
                </tr>
              </thead>
              <tbody>
                {today.campaigns_list.map((camp) => (
                  <tr key={camp.id}>
                    <td>{formatDateTime(camp.timestamp)}</td>
                    <td className="subject-cell">{camp.subject}</td>
                    <td>{camp.total_attempted}</td>
                    <td className="success-text">{camp.successful}</td>
                    <td className="error-text">{camp.failed}</td>
                    <td>{camp.success_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="no-data">
            <p>No campaigns sent today yet.</p>
          </div>
        )}
      </section>

      <section className="report-section">
        <div className="section-heading">
          <h3>What each number means</h3>
        </div>
        <ul className="metric-guide">
          <li>
            <strong>Campaigns</strong> — {guide.campaigns || 'One send action from the Email Sender tab.'}
          </li>
          <li>
            <strong>Emails attempted</strong> — {guide.attempted || 'Total recipients in the list after filtering.'}
          </li>
          <li>
            <strong>Sent successfully</strong> — {guide.sent || 'Accepted by ZeptoMail without an immediate error.'}
          </li>
          <li>
            <strong>Failed</strong> — {guide.failed || 'Could not be sent (API, network, or auth error).'}
          </li>
          <li>
            <strong>Success rate</strong> — {guide.success_rate || 'sent ÷ attempted × 100.'}
          </li>
        </ul>
      </section>

      <section className="report-section">
        <div className="section-heading">
          <h3>Last 7 days</h3>
        </div>
        {data.daily_breakdown?.length > 0 ? (
          <div className="table-responsive">
            <table className="campaigns-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Campaigns</th>
                  <th>Attempted</th>
                  <th>Sent</th>
                  <th>Failed</th>
                  <th>Success %</th>
                </tr>
              </thead>
              <tbody>
                {data.daily_breakdown.map((day) => (
                  <tr key={day.date}>
                    <td>{formatDate(day.date)}</td>
                    <td>{day.campaigns}</td>
                    <td>{day.attempted}</td>
                    <td className="success-text">{day.sent}</td>
                    <td className="error-text">{day.failed}</td>
                    <td>{day.success_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="no-data">
            <p>No activity in the last 7 days.</p>
          </div>
        )}
      </section>

      <section className="report-section">
        <div className="section-heading">
          <h3>All-time overview</h3>
          <div className="view-tabs">
            <button
              type="button"
              className={view === 'today' ? 'active' : ''}
              onClick={() => setView('today')}
            >
              Focus today
            </button>
            <button
              type="button"
              className={view === 'all' ? 'active' : ''}
              onClick={() => setView('all')}
            >
              Recent campaigns
            </button>
          </div>
        </div>

        <div className="stats-grid compact">
          <div className="stat-card">
            <div className="stat-title">Total campaigns</div>
            <div className="stat-value">{data.total_campaigns}</div>
          </div>
          <div className="stat-card blue">
            <div className="stat-title">Total attempted</div>
            <div className="stat-value">{data.total_emails_attempted}</div>
          </div>
          <div className="stat-card green">
            <div className="stat-title">Total sent</div>
            <div className="stat-value">{data.total_emails_sent}</div>
          </div>
          <div className="stat-card red">
            <div className="stat-title">Total failed</div>
            <div className="stat-value">{data.total_emails_failed}</div>
          </div>
          <div className="stat-card purple">
            <div className="stat-title">Overall success</div>
            <div className="stat-value">{data.success_rate}%</div>
          </div>
        </div>

        {view === 'all' && (
          <>
            <h4 className="table-title">Recent campaigns (last 20)</h4>
            {data.recent_campaigns?.length > 0 ? (
              <div className="table-responsive">
                <table className="campaigns-table">
                  <thead>
                    <tr>
                      <th>Date &amp; time</th>
                      <th>Email subject</th>
                      <th>Attempted</th>
                      <th>Sent</th>
                      <th>Failed</th>
                      <th>Success %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_campaigns.map((camp) => (
                      <tr key={camp.id}>
                        <td>{formatDateTime(camp.timestamp)}</td>
                        <td className="subject-cell">{camp.subject}</td>
                        <td>{camp.total_attempted}</td>
                        <td className="success-text">{camp.successful}</td>
                        <td className="error-text">{camp.failed}</td>
                        <td>{camp.success_rate}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="no-data">
                <p>No email campaigns have been sent yet.</p>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
};

export default AnalyticsDashboard;
