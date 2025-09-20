import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import API from '../api/api';

interface Vital {
  id: number;
  patient_id: number;
  date: string;
  systolic: number;
  diastolic: number;
}

export default function TrendChart({ patientId }: { patientId?: number }) {
  const [data, setData] = useState<Vital[]>([]);

  useEffect(() => {
    if (!patientId) return;
    API.get<Vital[]>(`/vitals?patient_id=${patientId}&_sort=date&_order=asc`).then((r) =>
      setData(r.data)
    );
  }, [patientId]);

  if (!patientId) return null;

  return (
    <div style={{ width: '100%', height: 220 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="systolic" stroke="#8884d8" dot />
          <Line type="monotone" dataKey="diastolic" stroke="#82ca9d" dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
