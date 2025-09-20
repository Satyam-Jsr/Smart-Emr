import React, { useState, useRef, useEffect } from 'react';
import { usePatients } from '../context/PatientContext';
import API from '../api/api';

export default function NewPatientForm({ onSuccess, onCancel }: { onSuccess?: () => void; onCancel?: () => void }) {
  const { refresh } = usePatients();
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nameRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    nameRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !age.trim()) {
      setError('Please fill in all fields');
      return;
    }

    const ageNum = parseInt(age);
    if (isNaN(ageNum) || ageNum < 0 || ageNum > 150) {
      setError('Please enter a valid age (0-150)');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      await API.post('/patients', { name: name.trim(), age: ageNum });
      setName('');
      setAge('');
      refresh();
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error('Failed to create patient', err);
      setError('Failed to create patient. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h4 className="emr-heading-3 mb-2">Add New Patient</h4>
        <p className="emr-text-muted">Enter patient information to create a new record</p>
      </div>
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block emr-text-body font-medium mb-2">
              Patient Name
            </label>
            <input
              type="text"
              placeholder="Enter full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="emr-input w-full"
              ref={nameRef}
              disabled={loading}
            />
          </div>
          <div>
            <label className="block emr-text-body font-medium mb-2">
              Age
            </label>
            <input
              type="number"
              placeholder="Age"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className="emr-input w-full"
              min="0"
              max="150"
              disabled={loading}
            />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            className="emr-btn-primary flex-1"
            disabled={loading || !name.trim() || !age.trim()}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Patient
              </>
            )}
          </button>
          
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="emr-btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}