import React from 'react';
import { Activity, Camera, Cpu, LayoutDashboard, BarChart3, Settings, ShieldCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, telemetry }) {
  const isCameraOnline = telemetry?.camera_status === 'online';
  const isAiHealthy = telemetry?.ai_health === 'healthy';

  return (
    <nav className="glass-card" style={{ margin: '16px 24px', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #06B6D4, #3B82F6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Activity size={22} color="#fff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, #94A3B8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            RetailVision
          </h1>
          <p style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 500 }}>AI People-Counting Engine v2.0</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        {[
          { id: 'live', label: 'Live Monitor', icon: LayoutDashboard },
          { id: 'analytics', label: 'Analytics & Reports', icon: BarChart3 },
          { id: 'camera', label: 'Line Setup', icon: Camera },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                color: isActive ? '#60A5FA' : '#94A3B8',
                fontWeight: isActive ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <Icon size={18} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className={isCameraOnline ? 'badge badge-online' : 'badge badge-offline'}>
          <Camera size={14} />
          {isCameraOnline ? 'Camera Online' : 'Camera Offline'}
        </span>
        <span className={isAiHealthy ? 'badge badge-online' : 'badge badge-offline'}>
          <Cpu size={14} />
          {isAiHealthy ? 'AI Engine Healthy' : 'AI Degraded'}
        </span>
      </div>
    </nav>
  );
}
