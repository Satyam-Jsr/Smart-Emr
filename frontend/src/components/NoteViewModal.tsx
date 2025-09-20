import React, { useState, useEffect } from 'react';
import API from '../api/api';

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
  onNoteUpdated?: () => void; // Callback to refresh notes after edit/delete
}

export default function NoteViewModal({ note, isOpen, onClose, onNoteUpdated }: NoteViewModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Debug logging
  useEffect(() => {
    console.log('NoteViewModal props received:', { 
      note: note ? { id: note.id, hasText: !!note.text, textLength: note.text?.length } : null, 
      isOpen, 
      isEditing 
    });
    if (note && isOpen) {
      console.log('Full note data:', note);
    }
  }, [note, isOpen, isEditing]);

  // Early return if modal is not open
  if (!isOpen) {
    return null;
  }

  // Early return if note is not available
  if (!note) {
    console.error('NoteViewModal: No note provided but modal is open');
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 className="text-lg font-semibold mb-4">Error</h3>
          <p className="text-gray-600 mb-4">No note data available.</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  // Reset editing state when modal closes or note changes
  useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setEditText('');
      setSaving(false);
      setDeleting(false);
    }
  }, [isOpen]);

  const noteDate = note.note_date || note.date || 'No date';

  // Initialize edit text when starting to edit
  const startEditing = () => {
    try {
      setEditText(note.text || '');
      setIsEditing(true);
      console.log('Starting edit mode with text:', note.text);
    } catch (error) {
      console.error('Error starting edit:', error);
    }
  };

  const cancelEditing = () => {
    try {
      setIsEditing(false);
      setEditText('');
      console.log('Cancelled editing');
    } catch (error) {
      console.error('Error cancelling edit:', error);
    }
  };

  const saveNote = async () => {
    if (!editText.trim()) return;
    
    setSaving(true);
    try {
      // Use the correct endpoint with patients prefix
      await API.put(`/patients/notes/${note.id}`, { text: editText.trim() });
      
      // Update the note object locally
      note.text = editText.trim();
      
      setIsEditing(false);
      if (onNoteUpdated) onNoteUpdated();
    } catch (error) {
      console.error('Failed to save note:', error);
      alert('Failed to save note. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const deleteNote = async () => {
    if (!confirm(`Are you sure you want to delete this note? This action cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    try {
      await API.delete(`/notes/${note.id}`);
      if (onNoteUpdated) onNoteUpdated();
      onClose(); // Close modal after successful deletion
    } catch (error) {
      console.error('Failed to delete note:', error);
      alert('Failed to delete note. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  // Handle ESC key press to close modal
  React.useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Handle backdrop click to close modal
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  console.log('Rendering modal with note:', note);

  try {
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={handleBackdropClick}
      >
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
          {/* Simple Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="text-lg font-semibold">
              {isEditing ? 'Edit Note' : 'Note Details'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>
          </div>

          {/* Simple Content */}
          <div className="p-4 overflow-y-auto" style={{ maxHeight: '60vh' }}>
            {isEditing ? (
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full h-32 p-3 border rounded resize-none"
                placeholder="Enter note text..."
              />
            ) : (
              <div className="whitespace-pre-wrap">
                {note?.text || 'No content available'}
              </div>
            )}
          </div>

          {/* Simple Footer */}
          <div className="flex justify-end gap-2 p-4 border-t">
            {isEditing ? (
              <>
                <button
                  onClick={cancelEditing}
                  className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={saveNote}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={deleteNote}
                  disabled={deleting}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  {deleting ? 'Deleting...' : 'Delete'}
                </button>
                <button
                  onClick={startEditing}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Edit
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error rendering NoteViewModal:', error);
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 className="text-lg font-semibold mb-4">Rendering Error</h3>
          <p className="text-gray-600 mb-4">There was an error displaying the note modal.</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }
}