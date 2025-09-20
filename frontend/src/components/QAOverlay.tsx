import React, { useState, useEffect } from 'react';
import API from '../api/api';

export default function QAOverlay({ isOpen, onClose, patientId }: { isOpen: boolean; onClose: () => void; patientId?: number }) {
  const [q, setQ] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Add ESC key support
  useEffect(() => {
    const handleEscKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
    }
    
    return () => document.removeEventListener('keydown', handleEscKey);
  }, [isOpen, onClose]);

  // Auto-reset when dialog closes
  useEffect(() => {
    if (!isOpen) {
      setQ('');
      setAnswer(null);
    }
  }, [isOpen]);

  async function submit() {
    if (!patientId || !q.trim()) return;
    setLoading(true);
    try {
      const res = await API.post(`/patients/${patientId}/qa`, { question: q });
      console.log('Q&A Response:', res);
      console.log('Response data:', res.data);
      console.log('Answer field:', res.data.answer);
      setAnswer(res.data.answer || 'No answer received.');
    } catch (err: any) {
      console.error('Q&A error:', err);
      console.error('Error response:', err.response);
      console.error('Error status:', err.response?.status);
      console.error('Error data:', err.response?.data);
      console.error('Error message:', err.message);
      console.error('Error code:', err.code);
      
      if (err.response?.status === 404) {
        setAnswer('Patient not found. Please select a valid patient.');
      } else if (err.response?.status === 400) {
        setAnswer('Please enter a valid question.');
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setAnswer('Request timed out. The question might be too complex. Please try a simpler question.');
      } else if (err.code === 'ECONNREFUSED') {
        setAnswer('Cannot connect to server. Please check if the backend is running.');
      } else if (!err.response) {
        setAnswer('Network error: Cannot reach the server. Please check your connection and try again.');
      } else {
        setAnswer('Sorry, I couldn\'t process your question at the moment. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40 p-4 z-50">
      <div className="bg-white p-4 rounded shadow max-w-xl w-full">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold">Ask about this patient</h3>
          <button onClick={onClose} className="text-gray-500">Close</button>
        </div>
        <textarea className="w-full border rounded p-2 mb-3" rows={3} value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="flex gap-2">
          <button className="px-3 py-2 bg-indigo-600 text-white rounded" onClick={submit} disabled={loading}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
          <button className="px-3 py-2 border rounded" onClick={() => { setQ(''); setAnswer(null); }}>
            Reset
          </button>
        </div>

        {answer && (
          <div className="mt-4 p-3 border rounded bg-gray-50">
            <div className="font-medium">Answer</div>
            <div className="text-sm text-gray-700 mt-2">{answer}</div>
          </div>
        )}
      </div>
    </div>
  );
}
