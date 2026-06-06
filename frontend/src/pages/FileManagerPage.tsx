import { useEffect, useState, useCallback } from 'react';
import { FileList } from '../components/FileList';
import { FileUpload } from '../components/FileUpload';
import { FileInfo, getFiles } from '../api/client';

export function FileManagerPage() {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [, setError] = useState<string | null>(null);
  
  const fetchFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const files = await getFiles();
      setFiles(files);
    } catch (err) {
      console.error('Failed to fetch files', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  return (
    <div className="page-container">
      <div className="flex-between mb-lg align-center">
        <div>
          <h1 className="page-title">File Manager</h1>
          <p className="text-secondary">Upload and manage your GnuCash files.</p>
        </div>
        <button onClick={fetchFiles} className="btn btn-secondary btn-sm" disabled={isLoading}>
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="dashboard-grid">
        <div className="main-column">
          <section className="mb-lg">
            <FileList files={files} onFileDeleted={fetchFiles} />
          </section>
        </div>
        
        <div className="side-column">
          <div className="glass-card mb-md text-center">
            <h3 className="mb-sm">Storage Stats</h3>
            <div className="stat-circle mb-sm mx-auto">
              <span className="stat-number">{files.length}</span>
            </div>
            <p className="text-secondary">Total Files</p>
          </div>
          
          <section>
            <h3 className="mb-sm">Upload New File</h3>
            <FileUpload onUploadSuccess={fetchFiles} />
          </section>
        </div>
      </div>
    </div>
  );
}
