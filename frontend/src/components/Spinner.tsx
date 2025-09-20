import React from 'react';

export default function Spinner({ size = 4 }: { size?: number }) {
  // size corresponds to tailwind w-/h- classes (e.g., 4 -> w-4 h-4)
  const s = `w-${size} h-${size}`;
  // fallback inline SVG with animate-spin
  return (
    <svg
      className={`animate-spin text-white ${s}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      ></path>
    </svg>
  );
}
