import React, { createContext, useContext, useState } from 'react';
import API from '../api/api';

export interface Note {
  id: number;
  patient_id: number;
  note_date: string;
  text: string;
}

interface NoteContextValue {
  notes: Note[];
  fetchNotes: (patientId: number) => Promise<void>;
  createNote: (patientId: number, text: string) => Promise<void>;
  deleteNote: (noteId: number) => Promise<void>;
}

const NoteContext = createContext<NoteContextValue | undefined>(undefined);

export const NoteProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notes, setNotes] = useState<Note[]>([]);

  const fetchNotes = async (patientId: number) => {
    try {
  const res = await API.get<Note[]>(`/notes/${patientId}`);
  setNotes(res.data);
    } catch (err) {
      console.error('Failed to fetch notes:', err);
    }
  };

  const createNote = async (patientId: number, text: string) => {
    try {
      await API.post('/notes/', { patient_id: patientId, text });
      await fetchNotes(patientId);
    } catch (err) {
      console.error('Failed to create note:', err);
    }
  };

  const deleteNote = async (noteId: number) => {
    try {
      await API.delete(`/notes/${noteId}`);
      setNotes((prev) => prev.filter((n) => n.id !== noteId));
    } catch (err) {
      console.error('Failed to delete note:', err);
    }
  };

  return (
    <NoteContext.Provider value={{ notes, fetchNotes, createNote, deleteNote }}>
      {children}
    </NoteContext.Provider>
  );
};

export function useNotes() {
  const ctx = useContext(NoteContext);
  if (!ctx) throw new Error('useNotes must be used inside NoteProvider');
  return ctx;
}
