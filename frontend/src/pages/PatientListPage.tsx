import React, { useState } from 'react';
import { usePatients, Patient } from '../context/PatientContext';
import API from '../api/api';

export default function PatientListPage() {
  const { patients, refresh, selectPatient, selectedPatientId } = usePatients();
  const [showForm, setShowForm] = useState(false);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [name, setName] = useState('');
  const [age, setAge] = useState('');

  const openNewPatientForm = () => {
    setEditingPatient(null);
    setName('');
    setAge('');
    setShowForm(true);
  };

  const openEditForm = (p: Patient) => {
    setEditingPatient(p);
    setName(p.name);
    setAge(p.age.toString());
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingPatient) {
        // Update patient
        await API.put(`/patients/${editingPatient.id}`, { name, age: parseInt(age) });
      } else {
        // Create new patient
        await API.post('/patients', { name, age: parseInt(age) });
      }
      setShowForm(false);
      refresh();
    } catch (err) {
      console.error('Failed to save patient', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this patient?')) return;
    try {
      await API.delete(`/patients/${id}`);
      refresh();
    } catch (err) {
      console.error('Failed to delete patient', err);
    }
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Patients</h2>
        <button
          className="bg-indigo-600 text-white px-3 py-1 rounded"
          onClick={openNewPatientForm}
        >
          New Patient
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mb-4 p-4 border rounded">
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="border p-2 mr-2"
            required
          />
          <input
            type="number"
            placeholder="Age"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            className="border p-2 mr-2"
            required
          />
          <button
            type="submit"
            className="bg-green-600 text-white px-3 py-1 rounded mr-2"
          >
            {editingPatient ? 'Update' : 'Add'}
          </button>
          <button
            type="button"
            onClick={() => setShowForm(false)}
            className="bg-gray-300 px-3 py-1 rounded"
          >
            Cancel
          </button>
        </form>
      )}

      {patients.length === 0 ? (
        <div>No patients found</div>
      ) : (
        <ul className="space-y-2">
          {patients.map((p) => (
            <li
              key={p.id}
              className={`p-3 border rounded flex justify-between items-center cursor-pointer ${
                selectedPatientId === p.id ? 'bg-gray-100' : ''
              }`}
            >
              <div onClick={() => selectPatient(p.id)}>
                <div className="font-semibold">{p.name}</div>
                <div className="text-sm text-gray-500">Age {p.age}</div>
              </div>
              <div className="flex space-x-2">
                <button
                  className="text-blue-600 text-sm"
                  onClick={() => openEditForm(p)}
                >
                  Edit
                </button>
                <button
                  className="text-red-600 text-sm"
                  onClick={() => handleDelete(p.id)}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
