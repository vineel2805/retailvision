import React, { useState, useEffect } from 'react';
import { Camera, Check, RefreshCw } from 'lucide-react';

export default function LineSetupView({ telemetry }) {
  const [pointA, setPointA] = useState(telemetry?.line_p1 || [40, 240]);
  const [pointB, setPointB] = useState(telemetry?.line_p2 || [250, 240]);
  const [direction, setDirection] = useState('negative_to_positive');
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    try {
      const res = await fetch('/api/camera/line', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          point_a: [parseInt(pointA[0]), parseInt(pointA[1])],
          point_b: [parseInt(pointB[0]), parseInt(pointB[1])],
          entry_direction: direction,
        }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (err) {
      console.error('Failed to update line:', err);
    }
  };

  return (
    <div style={{ margin: '0 24px', display: 'grid', gridTemplateColumns: '1fr 360px', gap: '20px' }}>
      <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Virtual Counting Line Live Preview</h2>
        <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: '12px', overflow: 'hidden' }}>
          <img src="/api/video_feed" alt="Camera Feed" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        </div>
      </div>

      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Configure Line Coordinates</h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Start Point (X1, Y1)</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="number"
              value={pointA[0]}
              onChange={(e) => setPointA([e.target.value, pointA[1]])}
              style={{ width: '50%', padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
            <input
              type="number"
              value={pointA[1]}
              onChange={(e) => setPointA([pointA[0], e.target.value])}
              style={{ width: '50%', padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
          </div>

          <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>End Point (X2, Y2)</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="number"
              value={pointB[0]}
              onChange={(e) => setPointB([e.target.value, pointB[1]])}
              style={{ width: '50%', padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
            <input
              type="number"
              value={pointB[1]}
              onChange={(e) => setPointB([pointB[0], e.target.value])}
              style={{ width: '50%', padding: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
          </div>

          <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Entry Direction</label>
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            style={{ padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
          >
            <option value="negative_to_positive" style={{ background: '#0F172A' }}>Right to Left (Negative to Positive)</option>
            <option value="positive_to_negative" style={{ background: '#0F172A' }}>Left to Right (Positive to Negative)</option>
          </select>
        </div>

        <button className="glow-btn" onClick={handleSave} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          {saved ? <Check size={18} /> : <RefreshCw size={18} />}
          {saved ? 'Line Updated!' : 'Apply Line Coordinates'}
        </button>
      </div>
    </div>
  );
}
