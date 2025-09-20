import React, { useEffect, useState } from 'react';
import API from '../api/api';
import NoteViewModal from './NoteViewModalFixed';

interface Note {
  id: number;
  note_date: string;
  text: string;
}

// Utility function to truncate text
const truncateText = (text: string, maxLength: number = 150): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export default function PatientNotes({ patientId }: { patientId: number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchNotes = () => {
    API.get<Note[]>(`/patients/${patientId}/notes`)
      .then((res) => setNotes(res.data))
      .catch((err) => console.error('Failed to load notes', err));
  };

  useEffect(() => {
    fetchNotes();
  }, [patientId]);

  const handleNoteClick = (note: Note) => {
    setSelectedNote(note);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedNote(null);
  };

  const handleNoteUpdated = () => {
    fetchNotes(); // Refresh notes after edit/delete
  };

  return (
    <div>
      <h4 className="text-md font-medium mt-4 mb-3">Notes</h4>
      <ul className="space-y-3">
        {notes.map((note) => (
          <li 
            key={note.id} 
            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all duration-200 border border-gray-200 hover:border-gray-300 hover:shadow-md group"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-gray-500 font-medium">
                {new Date(note.note_date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                })}
              </div>
              <div className="flex items-center gap-2">
                <div className="text-xs text-gray-400">
                  Note #{note.id}
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleNoteClick(note)}
                    className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                    title="View/Edit note"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Delete this note? This action cannot be undone.`)) {
                        API.delete(`/notes/${note.id}`)
                          .then(() => fetchNotes())
                          .catch((err) => console.error('Failed to delete note:', err));
                      }
                    }}
                    className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                    title="Delete note"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            <div 
              onClick={() => handleNoteClick(note)}
              className="text-gray-800 leading-relaxed cursor-pointer"
            >
              {truncateText(note.text)}
              {note.text.length > 150 && (
                <span className="ml-2 text-blue-600 hover:text-blue-800 text-sm font-medium inline-flex items-center">
                  Read more
                  <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              )}
            </div>
            {note.text.length > 150 && (
              <div className="mt-2 text-xs text-gray-400">
                {note.text.length} characters • Click to view full note
              </div>
            )}
          </li>
        ))}
      </ul>

      {/* Note View Modal */}
      <NoteViewModal
        note={selectedNote}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onNoteUpdated={handleNoteUpdated}
      />
    </div>
  );
}
