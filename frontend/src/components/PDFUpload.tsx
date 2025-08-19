'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiService } from '@/lib/api';
import { PDFUploadResponse, UploadStatus } from '@/types';
import { formatFileSize } from '@/lib/utils';

interface PDFUploadProps {
  onUploadSuccess: (response: PDFUploadResponse) => void;
  onUploadError: (error: string) => void;
  disabled?: boolean;
}

export function PDFUpload({ onUploadSuccess, onUploadError, disabled = false }: PDFUploadProps) {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    uploading: false,
    progress: 0,
    filename: '',
  });

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      
      // Validate file type
      if (file.type !== 'application/pdf') {
        onUploadError('Please select a PDF file');
        return;
      }

      // Validate file size (10MB max)
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        onUploadError('File size must be less than 10MB');
        return;
      }

      setUploadStatus({
        uploading: true,
        progress: 0,
        filename: file.name,
      });

      try {
        const response = await apiService.uploadPDF(file, (progress) => {
          setUploadStatus(prev => ({
            ...prev,
            progress,
          }));
        });

        if (response.success) {
          onUploadSuccess(response);
        } else {
          onUploadError(response.message || 'Upload failed');
        }
      } catch (error: any) {
        console.error('Upload error:', error);
        onUploadError(
          error.response?.data?.detail || 
          error.message || 
          'Failed to upload file'
        );
      } finally {
        setUploadStatus({
          uploading: false,
          progress: 0,
          filename: '',
        });
      }
    },
    [onUploadSuccess, onUploadError]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: disabled || uploadStatus.uploading,
  });

  if (uploadStatus.uploading) {
    return (
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center bg-gray-50">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-center mb-4">
            <FileText className="h-8 w-8 text-blue-500 animate-pulse" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Uploading {uploadStatus.filename}
          </h3>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadStatus.progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-500">
            {uploadStatus.progress}% completed
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive && !isDragReject 
          ? 'border-blue-400 bg-blue-50' 
          : isDragReject 
          ? 'border-red-400 bg-red-50' 
          : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      
      <div className="max-w-md mx-auto">
        <div className="flex items-center justify-center mb-4">
          {isDragReject ? (
            <AlertCircle className="h-12 w-12 text-red-500" />
          ) : (
            <Upload className="h-12 w-12 text-gray-400" />
          )}
        </div>
        
        {isDragActive ? (
          isDragReject ? (
            <div>
              <h3 className="text-lg font-medium text-red-900 mb-2">
                Invalid file type
              </h3>
              <p className="text-sm text-red-600">
                Please drop a PDF file
              </p>
            </div>
          ) : (
            <div>
              <h3 className="text-lg font-medium text-blue-900 mb-2">
                Drop your PDF here
              </h3>
              <p className="text-sm text-blue-600">
                Release to upload
              </p>
            </div>
          )
        ) : (
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Upload a PDF document
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Drag and drop your PDF file here, or click to browse
            </p>
            <Button variant="outline" disabled={disabled}>
              <Upload className="h-4 w-4 mr-2" />
              Choose File
            </Button>
            <p className="text-xs text-gray-400 mt-2">
              Maximum file size: 10MB
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
