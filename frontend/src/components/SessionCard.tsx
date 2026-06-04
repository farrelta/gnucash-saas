import React, { useState } from 'react';
import { SessionResponse } from '../api/client';
import client from '../api/client';

interface SessionCardProps {
  session: SessionResponse;
  onStatusChange: () => void;
}

export function SessionCard({ session, onStatusChange }: SessionCardProps) {
  const [isStopping, setIsStopping] = useState(false);
  const isRunning = session.status === 'RUNNING';

  const handleStop = async () => {
    if (!window.confirm('Are you sure you want to stop this session? Unsaved work may be lost.')) return;
    
    setIsStopping(true);
    try {
      await client.deleteSession(session.id);
      onStatusChange();
    } catch (err) {
      console.error('Failed to stop session', err);
      alert('Failed to stop session. Please try again.');
    } finally {
      setIsStopping(false);
    }
  };

  const handleOpen = () => {
    if (session.url) {
      window.open(session.url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className={`session-card glass-card ${isRunning ? 'active-glow' : ''}`}>
      <div className="session-header">
        <div className="session-status">
          <span className={`status-dot ${isRunning ? 'running pulse' : 'stopped'}`}></span>
          <span className="status-text">{session.status}</span>
        </div>
        <div className="session-id">Session #{session.id}</div>
      </div>

      <div className="session-body">
        <div className="info-row">
          <span className="info-label">Container:</span>
          <span className="info-value">{session.container_name || 'N/A'}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Created:</span>
          <span className="info-value">{new Date(session.created_at).toLocaleString()}</span>
        </div>
        {session.last_activity && (
          <div className="info-row">
            <span className="info-label">Last Activity:</span>
            <span className="info-value">{new Date(session.last_activity).toLocaleString()}</span>
          </div>
        )}
      </div>

      <div className="session-actions">
        {isRunning && (
          <button 
            onClick={handleOpen} 
            className="btn btn-primary btn-full"
          >
            Open GnuCash
          </button>
        )}
        
        {isRunning && (
          <button 
            onClick={handleStop} 
            className="btn btn-danger btn-full mt-sm"
            disabled={isStopping}
          >
            {isStopping ? 'Stopping...' : 'Stop Session'}
          </button>
        )}
      </div>
    </div>
  );
}
