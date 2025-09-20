import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { PatientProvider, usePatients } from './context/PatientContext';
import PatientList from './components/PatientList';
import PatientPage from './pages/PatientPage';
import PatientListPage from './pages/PatientListPage';
import SummaryPanel from './components/SummaryPanel';
import QAOverlay from './components/QAOverlay';

function AppContent() {
  const { selectedPatientId } = usePatients();
  const [qaOpen, setQaOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen w-full bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Modern Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="emr-heading-1">Smart EMR</h1>
                  <p className="emr-text-caption -mt-1">AI-Powered Medical Records</p>
                </div>
              </div>
              <div className="emr-badge emr-badge-primary">
                Prototype v1.0
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="relative">
                <input 
                  className="emr-input pl-10 w-80" 
                  placeholder="Search patients, notes, or conditions..." 
                />
                <svg className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="emr-status-dot emr-status-online"></div>
                <span className="emr-text-muted">System Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 overflow-hidden min-h-0">
        <div className="grid grid-cols-12 gap-6 h-full">
          {/* Left Sidebar - Patient List */}
          <aside className="col-span-3 min-h-0">
            <div className="emr-panel h-full flex flex-col overflow-hidden">
              <div className="emr-panel-header flex-shrink-0">
                <h2 className="emr-heading-3">Patients</h2>
                <p className="emr-text-muted">Manage patient records</p>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto p-6">
                <PatientList />
              </div>
            </div>
          </aside>

          {/* Center - Timeline / Notes */}
          <section className="col-span-6 min-h-0">
            <div className="emr-panel h-full flex flex-col overflow-hidden">
              <div className="emr-panel-header flex-shrink-0">
                <h2 className="emr-heading-3">Patient Timeline</h2>
                <p className="emr-text-muted">Medical history and notes</p>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto p-6">
                <PatientPage />
              </div>
            </div>
          </section>

          {/* Right Sidebar - AI Smart Panel */}
          <aside className="col-span-3 min-h-0">
            <div className="emr-panel h-full flex flex-col overflow-hidden">
              <div className="emr-panel-header flex-shrink-0">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <h2 className="emr-heading-3">AI Assistant</h2>
                </div>
                <p className="emr-text-muted">Smart insights and analysis</p>
              </div>
              <div className="flex-1 min-h-0 overflow-y-auto p-6">
                <SummaryPanel onAskQuestion={() => setQaOpen(true)} />
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* Q&A Overlay */}
      <QAOverlay 
        isOpen={qaOpen} 
        onClose={() => setQaOpen(false)} 
        patientId={selectedPatientId || undefined} 
      />
    </div>
  );
}

export default function App() {
  return (
    <PatientProvider>
      <AppContent />
    </PatientProvider>
  );
}
