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
  onNoteUpdated?: () => void;
}

export default function NoteViewModal({ note, isOpen, onClose, onNoteUpdated }: NoteViewModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Add ESC key support
  useEffect(() => {
    const handleEscKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        if (isEditing) {
          // If editing, first cancel edit mode
          setIsEditing(false);
          setEditText('');
        } else {
          // If not editing, close modal
          onClose();
        }
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
    }
    
    return () => document.removeEventListener('keydown', handleEscKey);
  }, [isOpen, isEditing, onClose]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setEditText('');
      setSaving(false);
      setDeleting(false);
    }
  }, [isOpen]);

  // Early returns
  if (!isOpen) {
    return null;
  }

  if (!note) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-6 max-w-md w-full">
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

  const startEditing = () => {
    setEditText(note.text || '');
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditText('');
  };

  const saveNote = async () => {
    if (!editText.trim()) return;
    
    setSaving(true);
    try {
      await API.put(`/patients/notes/${note.id}`, {
        text: editText,
        note_date: note.note_date || note.date
      });
      
      if (onNoteUpdated) onNoteUpdated();
      setIsEditing(false);
      setEditText('');
    } catch (error) {
      console.error('Failed to save note:', error);
      alert('Failed to save note. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const deleteNote = async () => {
    if (!confirm('Are you sure you want to delete this note?')) {
      return;
    }

    setDeleting(true);
    try {
      await API.delete(`/notes/${note.id}`);
      if (onNoteUpdated) onNoteUpdated();
      onClose();
    } catch (error) {
      console.error('Failed to delete note:', error);
      alert('Failed to delete note. Please try again.');
    } finally {
      setDeleting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            {isEditing ? 'Edit Note' : 'Note Details'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: '60vh' }}>
          {isEditing ? (
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full h-32 p-3 border border-gray-300 rounded resize-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter note text..."
              autoFocus
            />
          ) : (
            <div className="whitespace-pre-wrap text-gray-800">
              {note.text || 'No content available'}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-gray-200">
          {isEditing ? (
            <>
              <button
                onClick={cancelEditing}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={saveNote}
                disabled={saving || !editText.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Close
              </button>
              <button
                onClick={deleteNote}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
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
}