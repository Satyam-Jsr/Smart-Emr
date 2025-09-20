import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import './index.css';
import { PatientProvider } from './context/PatientContext';
import { NoteProvider } from './context/NoteContext';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PatientProvider>
      <NoteProvider>
        <BrowserRouter>
          <Routes>
            {/* Render the full App for the root and for patient-detail URLs so nested components
                (like PatientPage) can read the URL param via useParams */}
            <Route path="/" element={<App />} />
            <Route path="/patients/:id" element={<App />} />
            {/* Fallback to App for any other paths */}
            <Route path="/*" element={<App />} />
          </Routes>
        </BrowserRouter>
      </NoteProvider>
    </PatientProvider>
  </React.StrictMode>
);
