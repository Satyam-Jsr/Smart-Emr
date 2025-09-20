import React, { useMemo, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { usePatients } from '../context/PatientContext';
import Timeline from '../components/Timeline';
import SummaryPanel from '../components/SummaryPanel';
import TrendChart from '../components/TrendChart';
import QAOverlay from '../components/QAOverlay';
import SummaryModal from '../components/SummaryModal';
import NoteModal from '../components/NoteModal';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';

export default function PatientPage() {
  const { selectedPatientId, patients, selectPatient, addNote, summarizePatient } = usePatients();
  const { id } = useParams<{ id: string }>(); // grab /patients/:id from URL
  const [qaOpen, setQaOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{ one_line: string; bullets: string[] } | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'documents'>('timeline');

  const [noteOpen, setNoteOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [documentRefresh, setDocumentRefresh] = useState(0);

  async function handleAddNote(text?: string) {
    if (!patient) return;
    setLoading(true);
    try {
      if (text) {
        await addNote(patient.id, text);
        // bump reloadKey so child Timeline re-fetches notes
        setReloadKey((k) => k + 1);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const handleDocumentUpload = (result: any) => {
    if (result.success) {
      // Refresh document list and notes timeline (since OCR text is added as a note)
      setDocumentRefresh(prev => prev + 1);
      setReloadKey(prev => prev + 1);
    }
  };

  async function handleSummarize() {
    if (!patient) return;
    setLoading(true);
    try {
      const result = await summarizePatient(patient.id);
      setSummary(result);
      setSummaryOpen(true);
    } catch (err) {
      alert('Failed to summarize');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Ensure that if we land directly on /patients/:id, we sync into context
  useEffect(() => {
    if (id && !selectedPatientId) {
      selectPatient(Number(id));
    }
  }, [id, selectedPatientId, selectPatient]);

  const patient = useMemo(
    () => patients.find((p) => p.id === (selectedPatientId ?? Number(id))),
    [patients, selectedPatientId, id]
  );

  if (!patient) {
    return <div className="text-sm text-gray-500">Select a patient from the list to view details.</div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header Section - Fixed */}
      <div className="flex-shrink-0 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="emr-heading-1">{patient.name}</h2>
            <div className="emr-text-muted">
              Patient ID: {patient.id} · {patient.age} years old
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setNoteOpen(true)} disabled={loading} className="emr-btn-secondary">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Note
            </button>
            <button
              className="emr-btn-secondary"
              onClick={() => setQaOpen(true)}
              title="Ask a question about this patient"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Ask Question
            </button>
            <button onClick={handleSummarize} disabled={loading} className="emr-btn-primary">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Generate Summary
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('timeline')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'timeline'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📝 Timeline & Notes
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documents'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📄 Medical Documents
            </button>
          </nav>
        </div>
      </div>

      {/* Content Section - Scrollable */}
      <div className="flex-1 min-h-0">
        <div className="grid grid-cols-12 gap-4 h-full">
          {/* Left side - Timeline/Documents */}
          <div className="col-span-8">
            <div className="emr-card h-full flex flex-col overflow-hidden">
              <div className="flex-grow overflow-y-auto p-4">
                {activeTab === 'timeline' ? (
                  <Timeline patientId={patient.id} reloadKey={reloadKey} />
                ) : (
                  <div className="space-y-6">
                    <DocumentUpload 
                      patientId={patient.id} 
                      onUploadComplete={handleDocumentUpload}
                    />
                    <DocumentList 
                      patientId={patient.id} 
                      refreshTrigger={documentRefresh}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right side - Trends */}
          <div className="col-span-4">
            <div className="emr-card h-full flex flex-col overflow-hidden">
              <div className="emr-panel-header">
                <h4 className="emr-heading-3">Patient Trends</h4>
                <p className="emr-text-muted">Clinical data visualization</p>
              </div>
              <div className="emr-panel-body flex-grow overflow-y-auto">
                <TrendChart patientId={patient.id} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <SummaryModal isOpen={summaryOpen} onClose={() => setSummaryOpen(false)} summary={summary} />
      <NoteModal isOpen={noteOpen} onClose={() => setNoteOpen(false)} onSave={async (text) => { await handleAddNote(text); }} />
      <QAOverlay isOpen={qaOpen} onClose={() => setQaOpen(false)} patientId={patient.id} />
    </div>
  );
}
