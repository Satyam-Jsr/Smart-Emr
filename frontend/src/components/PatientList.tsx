import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePatients } from '../context/PatientContext';
import API from '../api/api';
import PatientModal from './PatientModal';

export default function PatientList() {
  const { patients, selectPatient, loading, error, refresh } = usePatients();
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [editingPatient, setEditingPatient] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter patients based on search term
  const filteredPatients = patients.filter(patient =>
    patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    patient.id.toString().includes(searchTerm)
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header with Add Patient */}
      <div className="mb-6 flex items-center justify-between flex-shrink-0">
        <div>
          <h3 className="emr-heading-3">Active Patients</h3>
          <p className="emr-text-muted">{filteredPatients.length} of {patients.length} patient{patients.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          className={`emr-btn-primary text-sm`}
          onClick={() => setShowModal(true)}
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Patient
        </button>
      </div>

      {/* Search Input */}
      <div className="mb-4 flex-shrink-0">
        <div className="relative">
          <input
            type="text"
            placeholder="Search patients by name or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Patient List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="emr-text-muted">Loading patients...</span>
            </div>
          </div>
        ) : error ? (
          <div className="text-center p-8">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-red-600 font-medium">Error Loading Patients</p>
            <p className="emr-text-muted mt-1">{error}</p>
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="text-center p-8">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <p className="emr-text-body">{searchTerm ? 'No patients match your search' : 'No patients found'}</p>
            <p className="emr-text-muted mt-1">{searchTerm ? 'Try adjusting your search terms' : 'Add your first patient to get started'}</p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {filteredPatients.map((p) => (
              <div key={p.id}>
                <div
                  className="emr-card-compact cursor-pointer hover:shadow-md hover:scale-[1.02] transition-all duration-200 group"
                  onClick={() => {
                    selectPatient(p.id);
                    navigate(`/patients/${p.id}`);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-medium">
                        {p.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </div>
                      <div>
                        <div className="emr-heading-3">{p.name}</div>
                        <div className="flex items-center gap-2 emr-text-muted">
                          <span className="flex-shrink-0">Age {p.age}</span>
                          {p.last_visit && (
                            <>
                              <span className="flex-shrink-0">•</span>
                              <span className="truncate">Last visit: {p.last_visit}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <button
                        className="emr-btn-ghost text-xs p-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingPatient(p);
                          setShowModal(true);
                        }}
                        title="Edit patient"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        className="emr-btn-ghost text-xs p-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete patient ${p.name}? This action cannot be undone.`)) {
                            API.delete(`/patients/${p.id}`).then(() => refresh());
                          }
                        }}
                        title="Delete patient"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patient Modal */}
      <PatientModal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setEditingPatient(null);
        }}
        onSuccess={() => {
          refresh();
          setShowModal(false);
          setEditingPatient(null);
        }}
        patient={editingPatient}
      />
    </div>
  );
}