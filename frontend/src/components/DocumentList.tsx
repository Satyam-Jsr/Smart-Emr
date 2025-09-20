import React, { useState, useEffect } from 'react';
import API from '../api/api';

interface Document {
  id: number;
  original_filename: string;
  file_type: string;
  processing_status: string;
  ocr_confidence: number | null;
  uploaded_at: string;
  processed_at: string | null;
  has_text: boolean;
  text_preview: string | null;
}

interface DocumentSummary {
  success: boolean;
  summary?: any;
  ai_provider?: string;
  source_confidence?: number;
  error?: string;
}

interface DocumentListProps {
  patientId: number;
  refreshTrigger?: number;
}

export default function DocumentList({ patientId, refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDoc, setExpandedDoc] = useState<number | null>(null);
  const [documentDetails, setDocumentDetails] = useState<{[key: number]: any}>({});
  const [summaries, setSummaries] = useState<{[key: number]: DocumentSummary}>({});
  const [summarizing, setSummarizing] = useState<{[key: number]: boolean}>({});

  useEffect(() => {
    fetchDocuments();
  }, [patientId, refreshTrigger]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await API.get(`/patients/${patientId}/documents`);
      setDocuments(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching documents:', err);
      setError(err.response?.data?.detail || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocumentDetails = async (documentId: number) => {
    try {
      const response = await API.get(`/patients/${patientId}/documents/${documentId}`);
      setDocumentDetails(prev => ({
        ...prev,
        [documentId]: response.data
      }));
    } catch (err: any) {
      console.error('Error fetching document details:', err);
    }
  };

  const handleExpand = (documentId: number) => {
    if (expandedDoc === documentId) {
      setExpandedDoc(null);
    } else {
      setExpandedDoc(documentId);
      if (!documentDetails[documentId]) {
        fetchDocumentDetails(documentId);
      }
    }
  };

  const handleSummarize = async (documentId: number) => {
    setSummarizing(prev => ({ ...prev, [documentId]: true }));
    
    try {
      const response = await API.post(`/patients/${patientId}/documents/${documentId}/summarize`);
      setSummaries(prev => ({
        ...prev,
        [documentId]: response.data
      }));
    } catch (err: any) {
      console.error('Error summarizing document:', err);
      setSummaries(prev => ({
        ...prev,
        [documentId]: {
          success: false,
          error: err.response?.data?.detail || 'Summarization failed'
        }
      }));
    } finally {
      setSummarizing(prev => ({ ...prev, [documentId]: false }));
    }
  };

  const handleDelete = async (documentId: number, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      await API.delete(`/patients/${patientId}/documents/${documentId}`);
      setDocuments(docs => docs.filter(doc => doc.id !== documentId));
      
      // Clean up state
      if (expandedDoc === documentId) {
        setExpandedDoc(null);
      }
      setDocumentDetails(prev => {
        const newDetails = { ...prev };
        delete newDetails[documentId];
        return newDetails;
      });
      setSummaries(prev => {
        const newSummaries = { ...prev };
        delete newSummaries[documentId];
        return newSummaries;
      });
    } catch (err: any) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document: ' + (err.response?.data?.detail || 'Unknown error'));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '⏳';
      case 'failed': return '❌';
      case 'pending': return '⏸️';
      default: return '❓';
    }
  };

  const getDocTypeIcon = (docType: string) => {
    switch (docType) {
      case 'lab_report': return '🧪';
      case 'blood_test': return '🩸';
      case 'xray': return '🩻';
      case 'prescription': return '💊';
      default: return '📄';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          Loading documents...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="text-center py-8">
          <div className="text-red-600 mb-2">❌ Error loading documents</div>
          <div className="text-sm text-gray-600">{error}</div>
          <button 
            onClick={fetchDocuments}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Medical Documents</h3>
        <p className="text-sm text-gray-600 mt-1">
          {documents.length} document{documents.length !== 1 ? 's' : ''} uploaded
        </p>
      </div>

      {documents.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          <div className="text-4xl mb-2">📁</div>
          <div>No documents uploaded yet</div>
          <div className="text-sm mt-1">Upload medical images to get started</div>
        </div>
      ) : (
        <div className="divide-y">
          {documents.map((doc) => (
            <div key={doc.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getDocTypeIcon(doc.file_type)}</span>
                    <span className="font-medium text-gray-900">{doc.original_filename}</span>
                    <span className="text-sm">{getStatusIcon(doc.processing_status)}</span>
                  </div>
                  
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                    <span>Type: {doc.file_type.replace('_', ' ')}</span>
                    {doc.ocr_confidence && (
                      <span>Confidence: {doc.ocr_confidence.toFixed(1)}%</span>
                    )}
                    <span>Uploaded: {formatDate(doc.uploaded_at)}</span>
                  </div>

                  {doc.text_preview && (
                    <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-2 rounded">
                      {doc.text_preview}
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  {doc.has_text && doc.processing_status === 'completed' && (
                    <button
                      onClick={() => handleSummarize(doc.id)}
                      disabled={summarizing[doc.id]}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      {summarizing[doc.id] ? '⏳' : '🤖'} Summarize
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleExpand(doc.id)}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    {expandedDoc === doc.id ? 'Collapse' : 'Expand'}
                  </button>
                  
                  <button
                    onClick={() => handleDelete(doc.id, doc.original_filename)}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedDoc === doc.id && (
                <div className="mt-4 space-y-4">
                  {/* Full Text */}
                  {documentDetails[doc.id]?.ocr_text && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Extracted Text</h4>
                      <div className="bg-gray-50 p-3 rounded border max-h-64 overflow-y-auto text-sm">
                        <pre className="whitespace-pre-wrap font-mono">
                          {documentDetails[doc.id].ocr_text}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* AI Summary */}
                  {summaries[doc.id] && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">AI Summary</h4>
                      {summaries[doc.id].success ? (
                        <div className="bg-blue-50 p-3 rounded border">
                          <div className="font-medium text-blue-900 mb-2">
                            {summaries[doc.id].summary?.one_line}
                          </div>
                          {summaries[doc.id].summary?.bullets && (
                            <ul className="text-sm text-blue-800 space-y-1">
                              {summaries[doc.id].summary.bullets.map((bullet: string, idx: number) => (
                                <li key={idx} className="flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{bullet}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                          <div className="text-xs text-blue-600 mt-2">
                            Generated by: {summaries[doc.id].ai_provider} • 
                            Source confidence: {summaries[doc.id].source_confidence?.toFixed(1)}%
                          </div>
                        </div>
                      ) : (
                        <div className="bg-red-50 p-3 rounded border text-red-700">
                          ❌ {summaries[doc.id].error || 'Summarization failed'}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}