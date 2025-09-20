import React, { useEffect, useRef } from "react";

interface SummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: { one_line: string; bullets: string[] } | null;
}

export default function SummaryModal({ isOpen, onClose, summary }: SummaryModalProps) {
  const closeBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) {
      document.addEventListener('keydown', onKey);
      setTimeout(() => closeBtnRef.current?.focus(), 0);
    }
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen || !summary) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-[500px] max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-2">Patient Summary</h2>
        <p className="text-gray-700 mb-4">{summary.one_line}</p>

        <ul className="list-disc pl-5 space-y-1">
          {summary.bullets.map((point, idx) => (
            <li key={idx} className="text-gray-600">{point}</li>
          ))}
        </ul>

        <div className="mt-5 flex justify-end">
          <button
            ref={closeBtnRef}
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
