import React, { useCallback, useState, useRef } from 'react';
import client from '../api/client';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['.gnucash', '.qif', '.ofx', '.csv'];

  const validateFile = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      throw new Error(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
    }
    if (file.size > 50 * 1024 * 1024) {
      throw new Error('File too large. Maximum size is 50MB.');
    }
  };

  const handleUpload = async (file: File) => {
    try {
      setError(null);
      validateFile(file);
      setIsUploading(true);
      setUploadProgress(10);
      
      await client.uploadFile(file);
      
      setUploadProgress(100);
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        onUploadSuccess();
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
      // Reset input so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="file-upload-container">
      {error && <div className="error-message shake mb-md">{error}</div>}
      
      <div 
        className={`drop-zone glass-card ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={onFileSelect}
          style={{ display: 'none' }}
          accept=".gnucash,.qif,.ofx,.csv"
        />
        
        {isUploading ? (
          <div className="upload-progress-container">
            <div className="loading-spinner mb-sm"></div>
            <p>Uploading... {uploadProgress}%</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
            </div>
          </div>
        ) : (
          <div className="drop-zone-content">
            <div className="upload-icon">☁️</div>
            <h3>Drag & Drop</h3>
            <p>or click to browse files</p>
            <div className="allowed-types mt-sm">
              <span className="type-badge">.gnucash</span>
              <span className="type-badge">.qif</span>
              <span className="type-badge">.ofx</span>
              <span className="type-badge">.csv</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
