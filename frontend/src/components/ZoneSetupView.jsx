import React, { useState, useEffect, useRef } from 'react';
import { Square, Check, RefreshCw, Plus, Trash2 } from 'lucide-react';

export default function ZoneSetupView({ telemetry }) {
  // Dynamic frame dimensions loaded from backend camera API
  const [frameDims, setFrameDims] = useState({ w: 1280, h: 720 });

  // Single source of truth for polygon coordinates (in real camera frame space)
  const [polygon, setPolygon] = useState([
    [64, 36],
    [1216, 36],
    [1216, 684],
    [64, 684],
  ]);
  const [confirmationFrames, setConfirmationFrames] = useState(5);
  const [draggingIdx, setDraggingIdx] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [saved, setSaved] = useState(false);

  const containerRef = useRef(null);

  // Fetch current active zone configuration and frame dimensions directly from backend API on mount
  useEffect(() => {
    fetch('/api/camera/zone')
      .then((res) => res.json())
      .then((data) => {
        const w = data?.frame_width || 1280;
        const h = data?.frame_height || 720;
        setFrameDims({ w, h });

        if (data?.polygon && data.polygon.length >= 3) {
          setPolygon(data.polygon);
        } else {
          // Default polygon with 5% margins based on dynamic frame dimensions
          setPolygon([
            [Math.round(w * 0.05), Math.round(h * 0.05)],
            [Math.round(w * 0.95), Math.round(h * 0.05)],
            [Math.round(w * 0.95), Math.round(h * 0.95)],
            [Math.round(w * 0.05), Math.round(h * 0.95)],
          ]);
        }

        if (data?.confirmation_frames) {
          setConfirmationFrames(data.confirmation_frames);
        }
      })
      .catch((err) => console.error('Failed to load active zone config:', err));
  }, []);

  const getContainerCoords = (e) => {
    if (!containerRef.current) return null;
    const rect = containerRef.current.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);

    const relX = clientX - rect.left;
    const relY = clientY - rect.top;

    const frameX = Math.round((relX / rect.width) * frameDims.w);
    const frameY = Math.round((relY / rect.height) * frameDims.h);

    return [
      Math.max(0, Math.min(frameDims.w, frameX)),
      Math.max(0, Math.min(frameDims.h, frameY)),
    ];
  };

  const handleContainerMouseDown = (e) => {
    const coords = getContainerCoords(e);
    if (!coords) return;

    const rect = containerRef.current.getBoundingClientRect();
    const handleThreshold = 25; // 25px click detection radius

    const clickedIdx = polygon.findIndex((pt) => {
      const handleScreenX = (pt[0] / frameDims.w) * rect.width;
      const handleScreenY = (pt[1] / frameDims.h) * rect.height;
      const clickScreenX = (coords[0] / frameDims.w) * rect.width;
      const clickScreenY = (coords[1] / frameDims.h) * rect.height;
      const dist = Math.hypot(handleScreenX - clickScreenX, handleScreenY - clickScreenY);
      return dist <= handleThreshold;
    });

    if (clickedIdx !== -1) {
      setDraggingIdx(clickedIdx);
      setSelectedIdx(clickedIdx);
    } else {
      // Clicked empty space — add a new vertex handle at clicked location
      const newPoly = [...polygon, coords];
      setPolygon(newPoly);
      setSelectedIdx(newPoly.length - 1);
    }
  };

  const handleMouseMove = (e) => {
    if (draggingIdx === null) return;
    const coords = getContainerCoords(e);
    if (!coords) return;

    const next = [...polygon];
    next[draggingIdx] = coords;
    setPolygon(next);
  };

  const handleMouseUp = () => {
    setDraggingIdx(null);
  };

  const handleSave = async () => {
    try {
      const res = await fetch('/api/camera/zone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          polygon: polygon.map((pt) => [parseFloat(pt[0]), parseFloat(pt[1])]),
          confirmation_frames: parseInt(confirmationFrames),
        }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (err) {
      console.error('Failed to update zone:', err);
    }
  };

  const addPoint = () => {
    const newPoly = [...polygon, [Math.round(frameDims.w / 2), Math.round(frameDims.h / 2)]];
    setPolygon(newPoly);
    setSelectedIdx(newPoly.length - 1);
  };

  const removeSelectedPoint = () => {
    if (polygon.length <= 3) return;
    const idxToRemove = selectedIdx !== null ? selectedIdx : polygon.length - 1;
    setPolygon(polygon.filter((_, i) => i !== idxToRemove));
    setSelectedIdx(null);
  };

  const resetDefault = () => {
    setPolygon([
      [Math.round(frameDims.w * 0.05), Math.round(frameDims.h * 0.05)],
      [Math.round(frameDims.w * 0.95), Math.round(frameDims.h * 0.05)],
      [Math.round(frameDims.w * 0.95), Math.round(frameDims.h * 0.95)],
      [Math.round(frameDims.w * 0.05), Math.round(frameDims.h * 0.95)],
    ]);
    setSelectedIdx(null);
  };

  // Single Source of Truth for handles & polygon (Numeric SVG coordinates using dynamic viewBox)
  const handles = polygon;
  const pointsStr = polygon.map(([x, y]) => `${x},${y}`).join(' ');

  return (
    <div style={{ margin: '0 24px', display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
      <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Square size={20} color="#60A5FA" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Visual Zone Polygon Editor</h2>
          </div>
          <span style={{ fontSize: '0.8rem', color: '#06B6D4', display: 'flex', alignItems: 'center', gap: '4px' }}>
            Frame Resolution: {frameDims.w} x {frameDims.h}
          </span>
        </div>

        <div
          ref={containerRef}
          onMouseDown={handleContainerMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{
            position: 'relative',
            width: '100%',
            aspectRatio: '16/9',
            background: '#000',
            borderRadius: '12px',
            overflow: 'hidden',
            cursor: draggingIdx !== null ? 'grabbing' : 'crosshair',
            userSelect: 'none',
          }}
        >
          {/* Clean Live Video Feed Background */}
          <img
            src="/api/video_feed?hide_zone=true"
            alt="Live Feed"
            style={{ width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }}
          />

          {/* Single SVG Overlay using dynamic viewBox matching actual camera frame dimensions */}
          <svg
            viewBox={`0 0 ${frameDims.w} ${frameDims.h}`}
            preserveAspectRatio="none"
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
          >
            {/* Filled Polygon & Outline using numeric coordinates */}
            <polygon
              points={pointsStr}
              fill="rgba(6, 182, 212, 0.25)"
              stroke="#06B6D4"
              strokeWidth="3"
              strokeDasharray="6 3"
            />

            {/* Draggable Handles using same numeric coordinates */}
            {handles.map(([x, y], idx) => {
              const isSelected = selectedIdx === idx;

              return (
                <g key={idx}>
                  <circle
                    cx={x}
                    cy={y}
                    r={isSelected ? 14 : 10}
                    fill={isSelected ? '#38BDF8' : '#06B6D4'}
                    stroke="#FFFFFF"
                    strokeWidth="2.5"
                    style={{ filter: 'drop-shadow(0px 2px 6px rgba(0,0,0,0.6))' }}
                  />
                  <text
                    x={x}
                    y={y}
                    dy="4"
                    textAnchor="middle"
                    fill="#000"
                    fontSize="11"
                    fontWeight="bold"
                    pointerEvents="none"
                  >
                    P{idx + 1}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Zone Configuration</h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ padding: '14px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px', fontSize: '0.85rem', color: '#94A3B8' }}>
            <p style={{ fontWeight: 600, color: '#F8FAFC', marginBottom: '4px' }}>Visual Editor Guide:</p>
            <ul style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <li>Click anywhere on video to place a point</li>
              <li>Drag any corner handle to resize</li>
              <li>{polygon.length} points active in polygon</li>
            </ul>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={addPoint}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '8px',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#60A5FA',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                fontSize: '0.85rem',
              }}
            >
              <Plus size={16} /> Add Corner Point
            </button>
            {polygon.length > 3 && (
              <button
                onClick={removeSelectedPoint}
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  color: '#EF4444',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8', display: 'flex', alignItems: 'center', gap: '6px' }}>
              Hysteresis Window (Consecutive Frames): {confirmationFrames}
            </label>
            <input
              type="range"
              min="1"
              max="15"
              value={confirmationFrames}
              onChange={(e) => setConfirmationFrames(e.target.value)}
              style={{ width: '100%', marginTop: '8px' }}
            />
            <span style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '4px', display: 'block' }}>
              Default: 5 frames. Eliminates boundary jitter when people pause near edge.
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
            <button
              onClick={resetDefault}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.05)',
                color: '#94A3B8',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '0.85rem',
              }}
            >
              Reset Box
            </button>
            <button
              className="glow-btn"
              onClick={handleSave}
              style={{
                flex: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                fontSize: '0.85rem',
              }}
            >
              {saved ? <Check size={18} /> : <RefreshCw size={18} />}
              {saved ? 'Zone Saved!' : 'Save Zone Configuration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
