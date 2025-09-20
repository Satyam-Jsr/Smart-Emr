import React, { useState, useRef } from 'react';
import API from '../api/api';

interface DocumentUploadProps {
  patientId: number;
  onUploadComplete?: (result: any) => void;
}

interface UploadResult {
  success: boolean;
  document_id?: number;
  filename?: string;
  doc_type?: string;
  ocr_text?: string;
  confidence?: number;
  processing_status?: string;
  error?: string;
  message?: string;
}

export default function DocumentUpload({ patientId, onUploadComplete }: DocumentUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('default');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const docTypes = [
    { value: 'default', label: 'Auto-detect' },
    { value: 'lab_report', label: 'Lab Report' },
    { value: 'blood_test', label: 'Blood Test' },
    { value: 'xray', label: 'X-ray Report' },
    { value: 'prescription', label: 'Prescription' },
  ];

  const handleFileSelect = (selectedFile: File) => {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'application/pdf'];
    if (!allowedTypes.includes(selectedFile.type)) {
      alert('Please select a valid image file (JPG, PNG, TIFF, BMP) or PDF');
      return;
    }

    // Validate file size (10MB)
    if (selectedFile.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    setFile(selectedFile);
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);
      formData.append('description', description);

      const response = await API.post(`/patients/${patientId}/upload-document`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      if (onUploadComplete) {
        onUploadComplete(response.data);
      }

      // Reset form on success
      if (response.data.success) {
        setFile(null);
        setDescription('');
        setDocType('default');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      setResult({
        success: false,
        error: error.response?.data?.detail || 'Upload failed',
        message: 'Failed to upload document'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">Upload Medical Document</h3>
      
      {/* File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.tiff,.bmp,.pdf"
          onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
          className="hidden"
        />
        
        {file ? (
          <div className="text-green-600">
            <div className="text-lg">📄 {file.name}</div>
            <div className="text-sm text-gray-500 mt-1">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </div>
          </div>
        ) : (
          <div className="text-gray-500">
            <div className="text-lg">📤</div>
            <div className="mt-2">
              Drag & drop a medical document here, or click to browse
            </div>
            <div className="text-sm mt-1">
              Supports: Lab reports, X-rays, prescriptions, blood tests
            </div>
            <div className="text-xs text-gray-400 mt-1">
              Formats: JPG, PNG, TIFF, BMP, PDF (max 10MB)
            </div>
          </div>
        )}
      </div>

      {/* Document Type Selection */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Type
        </label>
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {docTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Description */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description (Optional)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add any additional context about this document..."
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={2}
        />
      </div>

      {/* Upload Button */}
      <div className="mt-4">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full py-2 px-4 rounded-md font-medium ${
            !file || uploading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {uploading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Processing...
            </div>
          ) : (
            'Upload & Process'
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className={`mt-4 p-4 rounded-md ${
          result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className={`font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
            {result.success ? '✅ Upload Successful' : '❌ Upload Failed'}
          </div>
          
          {result.message && (
            <div className={`text-sm mt-1 ${result.success ? 'text-green-700' : 'text-red-700'}`}>
              {result.message}
            </div>
          )}

          {result.success && result.ocr_text && (
            <div className="mt-3">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Extracted Text (Confidence: {result.confidence?.toFixed(1)}%)
              </div>
              <div className="bg-white p-3 rounded border text-sm text-gray-800 max-h-32 overflow-y-auto">
                {result.ocr_text}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Document Type: {result.doc_type} • Status: {result.processing_status}
              </div>
            </div>
          )}

          {result.error && (
            <div className="text-sm text-red-700 mt-2">
              Error: {result.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}