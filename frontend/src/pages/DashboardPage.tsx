import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Session,
  FileInfo,
  getSessions,
  getFiles,
  createSession,
  heartbeatSession
} from '../api/client';
import { SessionCard } from '../components/SessionCard';
import { FileUpload } from '../components/FileUpload';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [recentFiles, setRecentFiles] = useState<FileInfo[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isCreatingSession, setIsCreatingSession] = useState(false);

  const fetchSessions = useCallback(async () => {
    try {
      const sessions = await getSessions();
      setSessions(sessions);
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const fetchRecentFiles = useCallback(async () => {
    try {
      const files = await getFiles();
      // Sort by modified date descending and take top 3
      const sorted = files.sort((a, b) => 
        new Date(b.modified_at).getTime() - new Date(a.modified_at).getTime()
      );
      setRecentFiles(sorted.slice(0, 3));
    } catch (err) {
      console.error('Failed to fetch files', err);
    }
  }, []);

  const activeSession = sessions.find(s => s.status === 'RUNNING');

  useEffect(() => {
    fetchSessions();
    fetchRecentFiles();
    
    // Poll for session updates every 10 seconds if there's a running session
    const interval = setInterval(() => {
      fetchSessions();
      if (activeSession) {
        heartbeatSession(activeSession.id).catch(console.error);
      }
    }, 10000);
    
    return () => clearInterval(interval);
  }, [fetchSessions, fetchRecentFiles, activeSession]);

  const handleCreateSession = async () => {
    setIsCreatingSession(true);
    try {
      await createSession();
      await fetchSessions();
    } catch (err) {
      console.error('Failed to create session', err);
      alert('Failed to launch GnuCash. Please try again.');
    } finally {
      setIsCreatingSession(false);
    }
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-header mb-lg">
        <h1 className="page-title">Welcome back!</h1>
        <p className="text-secondary">Here's an overview of your GnuCash workspace.</p>
      </div>

      <div className="dashboard-grid">
        <div className="main-column">
          <section className="dashboard-section mb-lg">
            <div className="section-header">
              <h2>Active Session</h2>
            </div>
            
            {isLoadingSessions ? (
              <div className="glass-card flex-center py-xl">
                <span className="spinner"></span>
              </div>
            ) : activeSession ? (
              <SessionCard session={activeSession} onStatusChange={fetchSessions} />
            ) : (
              <div className="empty-state glass-card">
                <div className="empty-state-icon">🖥️</div>
                <h3 className="mb-sm">No Active Session</h3>
                <p className="mb-md text-secondary">Launch GnuCash to start managing your finances.</p>
                <button 
                  onClick={handleCreateSession} 
                  className="btn btn-primary"
                  disabled={isCreatingSession}
                >
                  {isCreatingSession ? 'Launching...' : 'Launch GnuCash'}
                </button>
              </div>
            )}
          </section>

          <section className="dashboard-section">
            <div className="section-header">
              <h2>Quick Upload</h2>
            </div>
            <FileUpload onUploadSuccess={fetchRecentFiles} />
          </section>
        </div>

        <div className="side-column">
          <div className="glass-card stats-card mb-md">
            <h3>Member Since</h3>
            <p className="stat-value text-accent">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </p>
          </div>

          <div className="glass-card recent-files-card">
            <div className="flex-between mb-md">
              <h3>Recent Files</h3>
              <Link to="/files" className="text-accent text-sm">View All</Link>
            </div>
            
            {recentFiles.length > 0 ? (
              <ul className="recent-files-list">
                {recentFiles.map(file => (
                  <li key={file.filename} className="recent-file-item">
                    <span className="file-icon">📄</span>
                    <span className="file-name truncate">{file.filename}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-secondary text-sm">No files uploaded yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
