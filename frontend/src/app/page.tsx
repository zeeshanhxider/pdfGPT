'use client';

import React, { useState } from 'react';
import { PDFUpload } from '@/components/PDFUpload';
import { ChatInterface } from '@/components/ChatInterface';
import { PDFUploadResponse, Document } from '@/types';
import { FileText, MessageSquare, AlertCircle, CheckCircle } from 'lucide-react';

export default function HomePage() {
  const [currentDocument, setCurrentDocument] = useState<Document | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const [uploadSuccess, setUploadSuccess] = useState<string>('');

  const handleUploadSuccess = (response: PDFUploadResponse) => {
    const document: Document = {
      id: response.document_id,
      filename: response.filename,
      upload_date: new Date(),
      pages_processed: response.pages_processed,
      chunks_created: response.chunks_created,
    };

    setCurrentDocument(document);
    setUploadError('');
    setUploadSuccess(
      `Successfully processed "${response.filename}" - ${response.pages_processed} pages, ${response.chunks_created} chunks created`
    );

    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(''), 5000);
  };

  const handleUploadError = (error: string) => {
    setUploadError(error);
    setUploadSuccess('');
    
    // Clear error message after 10 seconds
    setTimeout(() => setUploadError(''), 10000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">PDF ChatBot</h1>
                <p className="text-sm text-gray-500">Ask questions about your documents</p>
              </div>
            </div>
            
            {currentDocument && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <FileText className="h-4 w-4" />
                <span className="font-medium">{currentDocument.filename}</span>
                <span className="text-gray-400">•</span>
                <span>{currentDocument.pages_processed} pages</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success/Error Messages */}
        {uploadSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <p className="text-green-800">{uploadSuccess}</p>
            </div>
          </div>
        )}

        {uploadError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-red-800">{uploadError}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">Upload Document</h2>
              </div>
              
              <PDFUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                disabled={false}
              />
            </div>

            {/* Document Info */}
            {currentDocument && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Information</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Filename:</span>
                    <span className="font-medium">{currentDocument.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Upload Date:</span>
                    <span className="font-medium">
                      {currentDocument.upload_date.toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Pages Processed:</span>
                    <span className="font-medium">{currentDocument.pages_processed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Text Chunks:</span>
                    <span className="font-medium">{currentDocument.chunks_created}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Chat Section */}
          <div className="lg:h-[600px]">
            <div className="bg-white rounded-lg shadow-sm border h-full flex flex-col">
              <div className="flex items-center space-x-2 p-6 border-b">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">Chat with Document</h2>
              </div>
              
              <div className="flex-1 overflow-hidden">
                <ChatInterface
                  documentId={currentDocument?.id}
                  documentName={currentDocument?.filename}
                  disabled={!currentDocument}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        {!currentDocument && (
          <div className="mt-12 bg-white rounded-lg shadow-sm border p-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">How to Use</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold">1</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Upload PDF</h4>
                <p className="text-sm text-gray-600">
                  Upload your PDF document (max 10MB) to get started
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold">2</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Processing</h4>
                <p className="text-sm text-gray-600">
                  We'll analyze your document and create searchable chunks
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-blue-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 font-bold">3</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Ask Questions</h4>
                <p className="text-sm text-gray-600">
                  Chat with your document and get intelligent answers
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500">
            <p className="text-sm">
              PDF ChatBot - Powered by RAG (Retrieval-Augmented Generation)
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
