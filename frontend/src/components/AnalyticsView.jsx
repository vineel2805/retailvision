import React, { useState, useEffect } from 'react';
import { Download, Calendar, Flame, BarChart } from 'lucide-react';
import { BarChart as ReBarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function AnalyticsView() {
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/reports/summary?start_date=${startDate}&end_date=${endDate}`);
      if (res.ok) {
        const data = await res.json();
        setSummaryData(data);
      }
    } catch (err) {
      console.error('Failed to fetch summary data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [startDate, endDate]);

  const handleExport = (fmt) => {
    window.open(`/api/reports/export/${fmt}?start_date=${startDate}&end_date=${endDate}`, '_blank');
  };

  const chartData = summaryData?.hourly_breakdown?.map(item => ({
    time: `${item.hour}:00`,
    entries: item.entries,
    exits: item.exits,
  })) || [];

  return (
    <div style={{ margin: '0 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="glass-card" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Calendar size={20} color="#60A5FA" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Analytics & Custom Reports</h2>
          <div style={{ display: 'flex', gap: '8px', marginLeft: '16px' }}>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 12px', borderRadius: '8px' }}
            />
            <span style={{ alignSelf: 'center', color: '#94A3B8' }}>to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 12px', borderRadius: '8px' }}
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="glow-btn" onClick={() => handleExport('csv')} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
            <Download size={14} /> CSV
          </button>
          <button className="glow-btn" onClick={() => handleExport('xlsx')} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #10B981, #059669)' }}>
            <Download size={14} /> Excel
          </button>
          <button className="glow-btn" onClick={() => handleExport('pdf')} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', background: 'linear-gradient(135deg, #EF4444, #DC2626)' }}>
            <Download size={14} /> PDF
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Range Total Entries</span>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#10B981', marginTop: '8px' }}>
            {summaryData?.total_entries ?? 0}
          </p>
        </div>
        <div className="glass-card" style={{ padding: '20px' }}>
          <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Range Total Exits</span>
          <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#F59E0B', marginTop: '8px' }}>
            {summaryData?.total_exits ?? 0}
          </p>
        </div>
        <div className="glass-card" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Peak Traffic Hour</span>
            <p style={{ fontSize: '1.8rem', fontWeight: 700, color: '#EC4899', marginTop: '8px' }}>
              {summaryData?.peak_hour ?? 'N/A'}
            </p>
          </div>
          <Flame size={32} color="#EC4899" />
        </div>
      </div>

      <div className="glass-card" style={{ padding: '24px', height: '400px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '20px', color: '#F8FAFC' }}>Hourly Traffic Breakdown</h3>
        <ResponsiveContainer width="100%" height="85%">
          <ReBarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="time" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip contentStyle={{ background: '#0F172A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
            <Bar dataKey="entries" fill="#10B981" name="Entries" radius={[4, 4, 0, 0]} />
            <Bar dataKey="exits" fill="#F59E0B" name="Exits" radius={[4, 4, 0, 0]} />
          </ReBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
