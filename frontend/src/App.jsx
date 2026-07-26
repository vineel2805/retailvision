import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import StatsGrid from './components/StatsGrid';
import LiveFeedView from './components/LiveFeedView';
import AnalyticsView from './components/AnalyticsView';
import LineSetupView from './components/LineSetupView';
import SettingsView from './components/SettingsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    // Fetch stats via REST or WebSocket
    const fetchTelemetry = async () => {
      try {
        const res = await fetch('/api/stats');
        if (res.ok) {
          const data = await res.json();
          setTelemetry(data);
        }
      } catch (err) {
        console.error('Stats fetch error:', err);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '40px' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} telemetry={telemetry} />
      <StatsGrid telemetry={telemetry} />

      {activeTab === 'live' && <LiveFeedView telemetry={telemetry} />}
      {activeTab === 'analytics' && <AnalyticsView />}
      {activeTab === 'camera' && <LineSetupView telemetry={telemetry} />}
      {activeTab === 'settings' && <SettingsView />}
    </div>
  );
}
