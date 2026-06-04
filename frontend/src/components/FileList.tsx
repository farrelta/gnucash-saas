import React from 'react';
import { FileInfo } from '../api/client';
import client from '../api/client';

interface FileListProps {
  files: FileInfo[];
  onFileDeleted: () => void;
}

export function FileList({ files, onFileDeleted }: FileListProps) {
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDownload = async (filename: string) => {
    try {
      const response = await client.downloadFile(filename);
      // Create a blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed', err);
      alert('Failed to download file.');
    }
  };

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;
    
    try {
      await client.deleteFile(filename);
      onFileDeleted();
    } catch (err) {
      console.error('Delete failed', err);
      alert('Failed to delete file.');
    }
  };

  if (files.length === 0) {
    return (
      <div className="empty-state glass-card">
        <div className="empty-icon">📁</div>
        <h3>No files found</h3>
        <p>Upload your GnuCash files to get started.</p>
      </div>
    );
  }

  return (
    <div className="file-list-container glass-card">
      <table className="file-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Modified Date</th>
            <th className="actions-cell">Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.filename}>
              <td className="file-name">{file.filename}</td>
              <td>{formatSize(file.size)}</td>
              <td>{new Date(file.modified_at).toLocaleString()}</td>
              <td className="actions-cell">
                <button 
                  onClick={() => handleDownload(file.filename)} 
                  className="btn btn-secondary btn-sm mr-sm"
                  title="Download"
                >
                  ↓
                </button>
                <button 
                  onClick={() => handleDelete(file.filename)} 
                  className="btn btn-danger btn-sm"
                  title="Delete"
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
