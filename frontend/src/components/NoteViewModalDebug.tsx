import React, { useState, useEffect } from 'react';

interface Note {
  id: number;
  note_date?: string;
  date?: string;
  text: string;
}

interface NoteViewModalProps {
  note: Note | null;
  isOpen: boolean;
  onClose: () => void;
  onNoteUpdated?: () => void;
}

export default function NoteViewModalDebug({ note, isOpen, onClose, onNoteUpdated }: NoteViewModalProps) {
  console.log('=== NoteViewModalDebug Props ===');
  console.log('isOpen:', isOpen);
  console.log('note:', note);
  console.log('note exists:', !!note);
  console.log('note.text:', note?.text);
  console.log('note.id:', note?.id);
  
  if (!isOpen) {
    console.log('Modal not open, returning null');
    return null;
  }

  if (!note) {
    console.log('No note provided, showing error');
    return (
      <div className="fixed inset-0 bg-red-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded">
          <h1>ERROR: No note data</h1>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  console.log('Rendering modal with note:', note);

  return (
    <div className="fixed inset-0 bg-green-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded max-w-lg w-full">
        <h1 className="text-xl font-bold mb-4">DEBUG MODAL</h1>
        <div className="mb-4">
          <strong>Note ID:</strong> {note.id}
        </div>
        <div className="mb-4">
          <strong>Note Text:</strong>
          <div className="bg-gray-100 p-2 rounded mt-2">
            {note.text || 'NO TEXT FOUND'}
          </div>
        </div>
        <button 
          onClick={onClose}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Close Debug Modal
        </button>
      </div>
    </div>
  );
}