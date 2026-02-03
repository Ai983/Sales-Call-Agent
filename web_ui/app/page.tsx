'use client';

import { useEffect, useMemo, useState } from 'react';

type Job = {
  job_id: string;
  status: string;
  error?: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [backend, setBackend] = useState<'faster' | 'openai'>('openai');
  const [job, setJob] = useState<Job | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [polling, setPolling] = useState(false);

  const jobId = job?.job_id;
  const status = job?.status;
  const error = job?.error;

  const downloadPdfUrl = useMemo(() => {
    if (!jobId || status !== 'done') return '';
    return `${API_BASE}/download/${jobId}/report.pdf`;
  }, [jobId, status]);

  const downloadJsonUrl = useMemo(() => {
    if (!jobId || status !== 'done') return '';
    return `${API_BASE}/download/${jobId}/report.json`;
  }, [jobId, status]);

  useEffect(() => {
    if (!jobId || !polling) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${jobId}`);
        const data = await res.json();
        setJob(data);
        if (data.status === 'done' || data.status === 'error') {
          setPolling(false);
        }
      } catch (err) {
        setPolling(false);
        setJob((prev) => ({
          job_id: prev?.job_id || 'unknown',
          status: 'error',
          error: 'Failed to poll job status.'
        }));
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, polling]);

  const onAnalyze = async () => {
    if (!file) return;
    setIsUploading(true);
    setJob(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('backend', backend);

      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        body: form
      });
      const data = await res.json();
      if (!res.ok) {
        setJob({
          job_id: data.job_id || 'unknown',
          status: 'error',
          error: data.message || data.detail || 'Upload failed.'
        });
        setIsUploading(false);
        return;
      }
      setJob(data);
      setPolling(true);
    } catch (err) {
      setJob({
        job_id: 'unknown',
        status: 'error',
        error: 'Upload failed. Check API connectivity.'
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Sales Call Analyzer</h1>
        <p style={styles.subtitle}>Upload a recording to generate a report.</p>

        <label style={styles.label}>Recording</label>
        <input
          type="file"
          accept=".mp3,.wav,.m4a,.aac"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          style={styles.input}
        />

        <label style={styles.label}>Backend</label>
        <select
          value={backend}
          onChange={(e) => setBackend(e.target.value as 'faster' | 'openai')}
          style={styles.select}
        >
          <option value="faster">faster</option>
          <option value="openai">openai</option>
        </select>

        <button
          onClick={onAnalyze}
          disabled={!file || isUploading}
          style={{
            ...styles.button,
            opacity: !file || isUploading ? 0.6 : 1
          }}
        >
          {isUploading ? 'Uploading...' : 'Analyze'}
        </button>

        <div style={styles.statusBox}>
          <h2 style={styles.sectionTitle}>Status</h2>
          {job ? (
            <div style={styles.statusDetails}>
              <div><strong>job_id:</strong> {job.job_id}</div>
              <div><strong>status:</strong> {job.status}</div>
              {job.error ? (
                <div style={styles.errorBox}>{job.error}</div>
              ) : null}
            </div>
          ) : (
            <div style={styles.muted}>No job yet.</div>
          )}

          {status === 'done' ? (
            <div style={styles.downloads}>
              <a href={downloadPdfUrl} target="_blank" rel="noreferrer" style={styles.linkButton}>
                Download PDF
              </a>
              <a href={downloadJsonUrl} target="_blank" rel="noreferrer" style={styles.linkButton}>
                Download JSON
              </a>
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'flex-start',
    backgroundColor: '#f6f7f9',
    padding: '40px 16px',
    fontFamily: 'Arial, sans-serif'
  },
  card: {
    width: '100%',
    maxWidth: '640px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 10px 24px rgba(0,0,0,0.08)'
  },
  title: {
    margin: 0,
    fontSize: '24px'
  },
  subtitle: {
    margin: '8px 0 24px',
    color: '#666'
  },
  label: {
    display: 'block',
    fontSize: '14px',
    marginBottom: '6px',
    color: '#333'
  },
  input: {
    width: '100%',
    marginBottom: '16px'
  },
  select: {
    width: '100%',
    padding: '8px',
    marginBottom: '16px'
  },
  button: {
    width: '100%',
    padding: '10px 12px',
    border: 'none',
    backgroundColor: '#1f6feb',
    color: '#fff',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 600
  },
  statusBox: {
    marginTop: '24px',
    padding: '16px',
    border: '1px solid #e3e6ea',
    borderRadius: '8px'
  },
  sectionTitle: {
    margin: 0,
    fontSize: '16px'
  },
  statusDetails: {
    marginTop: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  muted: {
    marginTop: '12px',
    color: '#888'
  },
  errorBox: {
    marginTop: '8px',
    padding: '10px',
    backgroundColor: '#ffe8e8',
    border: '1px solid #f2b6b6',
    borderRadius: '6px',
    color: '#8a1f1f'
  },
  downloads: {
    marginTop: '16px',
    display: 'flex',
    gap: '12px'
  },
  linkButton: {
    display: 'inline-block',
    padding: '8px 12px',
    backgroundColor: '#0f766e',
    color: '#fff',
    borderRadius: '6px',
    textDecoration: 'none'
  }
};
