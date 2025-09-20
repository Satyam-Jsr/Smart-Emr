// src/context/PatientContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import API from '../api/api';

export interface Patient {
  id: number;
  name: string;
  age: number;
  last_visit?: string; // optional
}

export interface Note {
  id: number;
  text: string;
  note_date: string;
}

interface PatientContextValue {
  patients: Patient[];
  selectedPatientId?: number;
  selectPatient: (id: number) => void;
  refresh: () => Promise<void>;
  addNote: (patientId: number, text: string) => Promise<void>;
  summarizePatient: (patientId: number) => Promise<any>;
  latestSummary: { one_line: string; bullets: string[] } | null;
  clearSummary: () => void;
  summarizeLoading: boolean;
  loading: boolean;
  error?: string;
}

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);
  const [latestSummary, setLatestSummary] = useState<{ one_line: string; bullets: string[] } | null>(null);
  const [summarizeLoading, setSummarizeLoading] = useState(false);

  async function fetchPatients() {
    try {
      setLoading(true);
      setError(undefined);
      const res = await API.get<Patient[]>('/patients/');
      
      if (!res.data) {
        throw new Error('No data received from server');
      }
      
      if (!Array.isArray(res.data)) {
        console.error('Invalid response format:', res.data);
        throw new Error('Invalid response format from server');
      }
      
      setPatients(res.data);
    } catch (err: any) {
      console.error('Failed to fetch patients from backend:', err);
      setError(err.message || 'Failed to fetch patients');
      // Initialize empty array on error to prevent undefined state
      setPatients([]);
    } finally {
      setLoading(false);
    }
  }

  async function addNote(patientId: number, text: string) {
    try {
      await API.post(`/patients/${patientId}/notes`, { text });
      await fetchPatients();
    } catch (err) {
      console.error('Failed to add note', err);
      throw err;
    }
  }

  async function summarizePatient(patientId: number) {
    setSummarizeLoading(true);
    try {
      const res = await API.post(`/patients/${patientId}/summarize`);
      // store in context so UI panels can read it
      setLatestSummary(res.data ?? null);
      return res.data;
    } catch (err) {
      console.error('Failed to summarize patient', err);
      throw err;
    } finally {
      setSummarizeLoading(false);
    }
  }

  function clearSummary() {
    setLatestSummary(null);
  }

  useEffect(() => {
    fetchPatients();
  }, []);

  return (
    <PatientContext.Provider
      value={{
        patients,
        selectedPatientId,
        selectPatient: (id: number) => {
          // clear summary when switching patients to avoid stale content
          setLatestSummary(null);
          setSelectedPatientId(id);
        },
        refresh: fetchPatients,
        addNote,
        summarizePatient,
        latestSummary,
        clearSummary,
        loading,
        summarizeLoading,
        error,
      }}
    >
      {children}
    </PatientContext.Provider>
  );
};

export function usePatients() {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error('usePatients must be used inside PatientProvider');
  return ctx;
}
