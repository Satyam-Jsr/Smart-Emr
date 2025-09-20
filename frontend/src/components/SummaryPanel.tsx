import React from 'react';
import { usePatients } from '../context/PatientContext';
import Spinner from './Spinner';

interface SummaryPanelProps {
  onAskQuestion?: () => void;
}

export default function SummaryPanel({ onAskQuestion }: SummaryPanelProps) {
  const { latestSummary, summarizeLoading, summarizePatient, selectedPatientId } = usePatients();

  async function handleRefresh() {
    if (!selectedPatientId) return;
    try {
      await summarizePatient(selectedPatientId);
    } catch (err) {
      console.error('Failed to refresh summary', err);
    }
  }

  if (!selectedPatientId) {
    return (
      <div className="text-center p-8">
        <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <h3 className="emr-heading-3 mb-2">AI Analysis Ready</h3>
        <p className="emr-text-muted">Select a patient to generate intelligent medical insights</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="emr-heading-2">AI Summary</h3>
          <p className="emr-text-muted">Intelligent medical analysis</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={summarizeLoading}
          className={`emr-btn-${summarizeLoading ? 'secondary' : 'primary'} text-sm`}
        >
          {summarizeLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
              Analyzing...
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </>
          )}
        </button>
      </div>

      {/* Summary Content */}
      <div className="space-y-4">
        {/* One-line Summary */}
        <div className="emr-card-compact">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <h4 className="emr-heading-3">Executive Summary</h4>
          </div>
          {latestSummary?.one_line ? (
            <p className="emr-text-body leading-relaxed">{latestSummary.one_line}</p>
          ) : (
            <div className="flex items-center gap-3 text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span className="emr-text-muted">Click refresh to generate AI summary</span>
            </div>
          )}
        </div>

        {/* Key Points */}
        <div className="emr-card-compact">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            <h4 className="emr-heading-3">Key Medical Points</h4>
          </div>
          {latestSummary?.bullets?.length ? (
            <div className="space-y-2">
              {latestSummary.bullets.map((bullet, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="emr-text-body">{bullet}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3 text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="emr-text-muted">Key insights will appear here</span>
            </div>
          )}
        </div>

        {/* Clinical Alerts */}
        <div className="emr-card-compact">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
            <h4 className="emr-heading-3">Clinical Alerts</h4>
          </div>
          <div className="flex items-center gap-3 text-gray-400">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="emr-text-muted">No active alerts</span>
          </div>
        </div>
      </div>

      {/* AI Action Buttons */}
      <div className="space-y-3 pt-4 border-t border-gray-200">
        <button 
          className="emr-btn-primary w-full"
          onClick={onAskQuestion}
          disabled={!selectedPatientId}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Ask AI Question
        </button>
        
        <div className="grid grid-cols-2 gap-2">
          <button className="emr-btn-secondary text-sm">
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Trends
          </button>
          <button className="emr-btn-secondary text-sm">
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            Export
          </button>
        </div>
      </div>
    </div>
  );
}