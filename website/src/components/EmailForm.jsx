import { useState } from 'react';
import { sendEmails } from '../api';
import './EmailForm.css';

const LoaderModal = ({ show }) => {
  if (!show) return null;
  return (
    <div className="modal-backdrop">
      <div className="modal-loader">
        <div className="spinner" />
        <div>Sending emails, please wait...</div>
      </div>
    </div>
  );
};

const EmailForm = () => {
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [bannerFiles, setBannerFiles] = useState([]);
  const [csvFile, setCsvFile] = useState(null);
  const [manualEmails, setManualEmails] = useState('');
  const [mode, setMode] = useState('file');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [filterSimilar, setFilterSimilar] = useState(true);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!bannerFiles.length) {
      setMessage('Please select at least one banner image or PDF.');
      return;
    }
    setLoading(true);
    setMessage('');
    const formData = new FormData();
    formData.append('subject', subject);
    formData.append('content', content);
    formData.append('filter_similar', filterSimilar ? 'true' : 'false');
    bannerFiles.forEach((file) => {
      formData.append('banners', file);
    });
    if (mode === 'file') {
      formData.append('csv_file', csvFile);
    } else {
      const emails = manualEmails.split(/[,;\n]+/).map((em) => em.trim()).filter(Boolean);
      const csvContent = 'email\n' + emails.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      formData.append('csv_file', blob, 'manual_emails.csv');
    }
    try {
      const response = await sendEmails(formData);
      const data = await response.json();
      let msg = data.message || 'Emails sent successfully!';
      if (data.filtered_out > 0) {
        const bits = [];
        if (data.skipped_invalid?.length) bits.push(`${data.skipped_invalid.length} invalid`);
        if (data.skipped_duplicate?.length) bits.push(`${data.skipped_duplicate.length} duplicate`);
        if (data.skipped_similar?.length) bits.push(`${data.skipped_similar.length} similar`);
        if (data.skipped_suspicious?.length) bits.push(`${data.skipped_suspicious.length} suspicious`);
        if (bits.length) msg += ` (${bits.join(', ')})`;
      }
      setMessage(msg);
    } catch (err) {
      setMessage(err.message || 'Error sending emails. Please try again.');
      console.error('Error sending emails:', err);
    }
    setLoading(false);
  };

  return (
    <>
      <LoaderModal show={loading} />
      <form className="email-form" onSubmit={handleSubmit}>
        <div className="form-header">
          <h2>Harish Critical Care Classes</h2>
          <p className="subtitle">Bulk Email Automation</p>
        </div>
        <div>
          <label htmlFor="email-subject">Subject:</label>
          <input
            id="email-subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="email-content">Content:</label>
          <textarea
            id="email-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="email-banner">Banner images / PDFs:</label>
          <p className="field-hint">
            Select one or more images and/or PDFs. PDFs are linked in the email and attached for download.
          </p>
          <input
            id="email-banner"
            type="file"
            accept="image/*,.pdf,application/pdf"
            multiple
            onChange={(e) => setBannerFiles(Array.from(e.target.files || []))}
            required
          />
        </div>
        <div>
          <span className="label-like">Choose Email Input Method:</span>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="mode"
                value="file"
                checked={mode === 'file'}
                onChange={() => setMode('file')}
              />
              Upload CSV/Excel
            </label>
            <label className="radio-label-second">
              <input
                type="radio"
                name="mode"
                value="manual"
                checked={mode === 'manual'}
                onChange={() => setMode('manual')}
              />
              Enter Emails Manually
            </label>
          </div>
        </div>
        {mode === 'file' ? (
          <div>
            <label htmlFor="email-csv">CSV/Excel File:</label>
            <input
              id="email-csv"
              type="file"
              accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
              onChange={(e) => setCsvFile(e.target.files[0])}
              required
            />
          </div>
        ) : (
          <div>
            <label htmlFor="email-manual">Emails (comma, semicolon, or newline separated):</label>
            <textarea
              id="email-manual"
              value={manualEmails}
              onChange={(e) => setManualEmails(e.target.value)}
              required
            />
          </div>
        )}
        <div>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={filterSimilar}
              onChange={(e) => setFilterSimilar(e.target.checked)}
            />
            Filter similar &amp; duplicate emails before sending
          </label>
          <p className="field-hint">
            Skips invalid addresses, exact duplicates, fake patterns like{' '}
            <code>23mohangola89@gmail.com</code>, and near-matches like{' '}
            <code>1mohangola47@gmail.com</code> when <code>mohangola47@gmail.com</code> is present.
          </p>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send Emails'}
        </button>
        {message && <div className="form-message">{message}</div>}
      </form>
    </>
  );
};

export default EmailForm;
