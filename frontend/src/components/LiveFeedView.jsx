import React from 'react';
import { Video, ShieldCheck } from 'lucide-react';

export default function LiveFeedView({ telemetry }) {
  const isOnline = telemetry?.camera_status === 'online';

  return (
    <div style={{ margin: '0 24px', display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px' }}>
      <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Video size={20} color="#60A5FA" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Live Camera Stream (Local Edge Inference)</h2>
          </div>
          <span style={{ fontSize: '0.8rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ShieldCheck size={14} />
            100% On-Premises Privacy Enforced
          </span>
        </div>

        <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: '12px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <img
            src="/api/video_feed"
            alt="Live Stream"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          {!isOnline && (
            <div style={{ position: 'absolute', color: '#94A3B8', textAlign: 'center' }}>
              <Video size={48} style={{ opacity: 0.5, marginBottom: '12px' }} />
              <p style={{ fontWeight: 600 }}>Camera Stream Offline</p>
              <p style={{ fontSize: '0.85rem' }}>Check USB / RTSP connection in Camera Setup</p>
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '12px', color: '#F8FAFC' }}>Hardware Active Tier</h3>
          <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ color: '#94A3B8' }}>Tier Mode:</span>
              <span style={{ color: '#60A5FA', fontWeight: 600, textTransform: 'uppercase' }}>{telemetry?.tier || 'Standard'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ color: '#94A3B8' }}>FPS Target:</span>
              <span style={{ color: '#F8FAFC', fontWeight: 500 }}>{telemetry?.fps || 0} FPS</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
              <span style={{ color: '#94A3B8' }}>Counting Line:</span>
              <span style={{ color: '#F8FAFC', fontWeight: 500 }}>Active</span>
            </div>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px', flex: 1 }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '12px', color: '#F8FAFC' }}>Security & Privacy Guarantee</h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.85rem', color: '#94A3B8' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#10B981' }}>✓</span> All AI processing occurs locally on device CPU/GPU
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#10B981' }}>✓</span> No video or frame images ever transmitted off-site
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#10B981' }}>✓</span> No face recognition or biometric storage
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ color: '#10B981' }}>✓</span> Full offline functionality for core counting
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
