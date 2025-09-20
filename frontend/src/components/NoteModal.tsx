import React, { useState, useEffect, useRef } from 'react';

interface NoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (text: string) => Promise<void>;
}

export default function NoteModal({ isOpen, onClose, onSave }: NoteModalProps) {
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) {
      document.addEventListener('keydown', onKey);
      // autofocus
      setTimeout(() => textareaRef.current?.focus(), 0);
    }
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  async function handleSave() {
    if (!text.trim()) return;
    setSaving(true);
    try {
      await onSave(text.trim());
      setText('');
      onClose();
    } catch (err) {
      console.error('Failed to save note', err);
      // keep modal open so user can retry
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-[480px] max-h-[70vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-2">Add Note</h3>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          className="w-full border rounded p-2 mb-3"
          placeholder="Write a clinical note..."
          aria-label="Note text"
        />

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1 border rounded">Cancel</button>
          <button onClick={handleSave} disabled={saving} className="px-3 py-1 bg-indigo-600 text-white rounded flex items-center gap-2">
            {saving ? (
              <>
                <svg className="animate-spin w-4 h-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                </svg>
                Saving...
              </>
            ) : (
              'Save'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
