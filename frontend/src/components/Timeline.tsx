import React, { useEffect, useState } from 'react';
import API from '../api/api';
import NoteViewModal from './NoteViewModalFixed';

interface Note {
  id: number;
  patient_id: number;
  // backend uses `note_date`; some code used `date`. Accept both.
  date?: string;
  note_date?: string;
  text: string;
  doctor_name?: string; // Added for editable doctor name
}

// Utility function to truncate text
const truncateText = (text: string, maxLength: number = 200): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export default function Timeline({ patientId, reloadKey }: { patientId?: number; reloadKey?: number }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDoctorId, setEditingDoctorId] = useState<number | null>(null);
  const [doctorNameInput, setDoctorNameInput] = useState('');

  // Handle editing doctor name
  const handleEditDoctor = (note: Note) => {
    setEditingDoctorId(note.id);
    setDoctorNameInput(note.doctor_name || 'Smith');
  };

  const handleSaveDoctorName = async (noteId: number) => {
    try {
      // Update the note with new doctor name (this would typically be an API call)
      setNotes(prevNotes => 
        prevNotes.map(note => 
          note.id === noteId 
            ? { ...note, doctor_name: doctorNameInput }
            : note
        )
      );
      setEditingDoctorId(null);
    } catch (error) {
      console.error('Error updating doctor name:', error);
      alert('Could not update doctor name. Please try again.');
    }
  };

  const handleCancelEditDoctor = () => {
    setEditingDoctorId(null);
    setDoctorNameInput('');
  };

  // Handle sharing notes
  const handleShareNote = async (note: Note) => {
    try {
      // Create shareable text
      const shareText = `Clinical Note - Patient ID: ${note.patient_id}\n\nDate: ${note.date || note.note_date}\nDoctor: Dr. ${note.doctor_name || 'Smith'}\n\nNote:\n${note.text}`;
      
      if (navigator.share) {
        // Use native sharing if available
        await navigator.share({
          title: 'Clinical Note',
          text: shareText
        });
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(shareText);
        alert('Note copied to clipboard!');
      }
    } catch (error) {
      console.error('Error sharing note:', error);
      alert('Could not share note. Please try again.');
    }
  };

  const fetchNotes = () => {
    if (!patientId) return;
    
    setLoading(true);
    setError(null);
    
    // Use the explicit patient-scoped endpoint which the backend exposes
    API.get<Note[]>(`/patients/${patientId}/notes`)
      .then((r) => {
        setNotes(r.data || []);
      })
      .catch((err) => {
        console.error('Failed to load timeline notes', err);
        setError('Failed to load patient notes');
        setNotes([]);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchNotes();
  }, [patientId, reloadKey]);

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

  if (!patientId) {
    return (
      <div className="text-center p-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="emr-heading-3 mb-2">Select a Patient</h3>
        <p className="emr-text-muted">Choose a patient from the list to view their medical timeline</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="emr-text-muted">Loading timeline...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-12">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="emr-heading-3 mb-2 text-red-600">Error Loading Timeline</h3>
        <p className="emr-text-muted">{error}</p>
      </div>
    );
  }

  if (notes.length === 0) {
    return (
      <div className="text-center p-12">
        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
        <h3 className="emr-heading-3 mb-2">No Notes Yet</h3>
        <p className="emr-text-muted">This patient doesn't have any medical notes. Add the first note to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Timeline Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="emr-heading-2">Medical Timeline</h3>
          <p className="emr-text-muted">{notes.length} note{notes.length !== 1 ? 's' : ''} in chronological order</p>
        </div>
        <div className="emr-badge emr-badge-primary">
          Recent Activity
        </div>
      </div>

      {/* Timeline Notes */}
      <div className="space-y-4">
        {notes.map((note, index) => (
          <div key={note.id} className="relative">
            {/* Timeline connector line */}
            {index < notes.length - 1 && (
              <div className="absolute left-6 top-12 w-0.5 h-full bg-gray-200"></div>
            )}
            
            <div className="emr-card-compact hover:shadow-lg transition-all duration-200">
              <div className="flex gap-4">
                {/* Timeline dot */}
                <div className="flex-shrink-0">
                  <div className="w-3 h-3 bg-blue-600 rounded-full mt-2"></div>
                </div>
                
                {/* Note content */}
                <div className="flex-grow">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="emr-badge emr-badge-primary">
                        {note.note_date ?? note.date ?? 'No date'}
                      </span>
                      <span className="emr-text-caption">Note #{note.id}</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleNoteClick(note)}
                        className="emr-btn-secondary text-sm px-3 py-2"
                        title="Edit note"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Edit
                      </button>
                      <button 
                        onClick={() => {
                          if (confirm(`Delete this note? This action cannot be undone.`)) {
                            API.delete(`/notes/${note.id}`)
                              .then(() => fetchNotes())
                              .catch((err) => console.error('Failed to delete note:', err));
                          }
                        }}
                        className="emr-btn-secondary text-sm px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                        title="Delete note"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>
                  
                  <div 
                    onClick={() => handleNoteClick(note)}
                    className="emr-text-body leading-relaxed cursor-pointer hover:text-gray-900 transition-colors"
                  >
                    {truncateText(note.text)}
                    {note.text.length > 200 && (
                      <button className="ml-2 text-blue-600 hover:text-blue-800 text-sm font-medium">
                        Read more
                      </button>
                    )}
                  </div>
                  
                  {/* Note metadata */}
                  <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                    <div className="flex items-center gap-4 emr-text-caption">
                      <span>📋 Clinical Note</span>
                      <div className="flex items-center gap-1">
                        <span>👤 Dr.</span>
                        {editingDoctorId === note.id ? (
                          <div className="flex items-center gap-1">
                            <input
                              type="text"
                              value={doctorNameInput}
                              onChange={(e) => setDoctorNameInput(e.target.value)}
                              className="px-1 py-0 text-xs border rounded w-20"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveDoctorName(note.id);
                                if (e.key === 'Escape') handleCancelEditDoctor();
                              }}
                              autoFocus
                            />
                            <button 
                              onClick={() => handleSaveDoctorName(note.id)}
                              className="text-green-600 hover:text-green-800"
                              title="Save"
                            >
                              ✓
                            </button>
                            <button 
                              onClick={handleCancelEditDoctor}
                              className="text-red-600 hover:text-red-800"
                              title="Cancel"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => handleEditDoctor(note)}
                            className="hover:bg-gray-100 px-1 rounded"
                            title="Click to edit doctor name"
                          >
                            {note.doctor_name || 'Smith'}
                          </button>
                        )}
                      </div>
                      <span>🏥 General Medicine</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleShareNote(note)}
                        className="emr-btn-ghost text-xs"
                        title="Share note"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                        </svg>
                        Share
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

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
