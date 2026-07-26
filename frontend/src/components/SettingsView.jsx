import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Camera, Cpu, Save } from 'lucide-react';

export default function SettingsView() {
  const [sourceType, setSourceType] = useState('usb');
  const [sourceUrl, setSourceUrl] = useState('0');
  const [cameraName, setCameraName] = useState('Main Entrance Camera');
  const [frameSkip, setFrameSkip] = useState(1);
  const [inferenceSize, setInferenceSize] = useState(640);
  const [roiEnabled, setRoiEnabled] = useState(true);
  const [useOnnx, setUseOnnx] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const handleSaveCamera = async () => {
    try {
      const res = await fetch('/api/camera/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: cameraName,
          source_type: sourceType,
          source_url: sourceUrl,
          width: 1280,
          height: 720,
          fps: 30,
        }),
      });
      if (res.ok) {
        setStatusMsg('Camera source updated successfully!');
        setTimeout(() => setStatusMsg(''), 3000);
      }
    } catch (err) {
      console.error('Failed to update camera:', err);
    }
  };

  const handleSaveAdaptive = async () => {
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_name: 'yolov8n.pt',
          frame_skip: parseInt(frameSkip),
          inference_size: parseInt(inferenceSize),
          roi_enabled: roiEnabled,
          use_onnx: useOnnx,
        }),
      });
      if (res.ok) {
        setStatusMsg('Adaptive performance settings saved!');
        setTimeout(() => setStatusMsg(''), 3000);
      }
    } catch (err) {
      console.error('Failed to update settings:', err);
    }
  };

  return (
    <div style={{ margin: '0 24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Camera size={20} color="#60A5FA" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Multi-Camera Setup (USB / RTSP / ONVIF)</h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Camera Name</label>
            <input
              type="text"
              value={cameraName}
              onChange={(e) => setCameraName(e.target.value)}
              style={{ width: '100%', marginTop: '6px', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Source Type</label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              style={{ width: '100%', marginTop: '6px', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            >
              <option value="usb" style={{ background: '#0F172A' }}>USB Webcam</option>
              <option value="rtsp" style={{ background: '#0F172A' }}>RTSP Stream (CCTV)</option>
              <option value="onvif" style={{ background: '#0F172A' }}>ONVIF IP Camera</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Device Index or RTSP/ONVIF Stream URL</label>
            <input
              type="text"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="e.g. 0 or rtsp://admin:pass@192.168.1.100:554/stream"
              style={{ width: '100%', marginTop: '6px', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            />
          </div>

          <button className="glow-btn" onClick={handleSaveCamera} style={{ marginTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <Save size={16} /> Save Camera Config
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={20} color="#8B5CF6" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Adaptive Performance Settings (FR-014)</h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>Frame Processing Sampling Rate</label>
            <select
              value={frameSkip}
              onChange={(e) => setFrameSkip(e.target.value)}
              style={{ width: '100%', marginTop: '6px', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            >
              <option value="1" style={{ background: '#0F172A' }}>Process Every Frame (1:1 - Standard/High)</option>
              <option value="2" style={{ background: '#0F172A' }}>Process Every 2nd Frame (Skip 1 - Low Power)</option>
              <option value="3" style={{ background: '#0F172A' }}>Process Every 3rd Frame (Skip 2 - Low Power Edge)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', color: '#94A3B8' }}>AI Inference Resolution</label>
            <select
              value={inferenceSize}
              onChange={(e) => setInferenceSize(e.target.value)}
              style={{ width: '100%', marginTop: '6px', padding: '10px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
            >
              <option value="320" style={{ background: '#0F172A' }}>320x320 (Ultra Fast Low Power)</option>
              <option value="480" style={{ background: '#0F172A' }}>480x480 (Balanced Edge)</option>
              <option value="640" style={{ background: '#0F172A' }}>640x640 (Standard High Accuracy)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#94A3B8', cursor: 'pointer' }}>
              <input type="checkbox" checked={roiEnabled} onChange={(e) => setRoiEnabled(e.target.checked)} />
              Enable ROI Cropping around Counting Line
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#94A3B8', cursor: 'pointer' }}>
              <input type="checkbox" checked={useOnnx} onChange={(e) => setUseOnnx(e.target.checked)} />
              Use ONNX Runtime INT8 Quantized Engine
            </label>
          </div>

          <button className="glow-btn" onClick={handleSaveAdaptive} style={{ marginTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: 'linear-gradient(135deg, #8B5CF6, #6366F1)' }}>
            <Save size={16} /> Save Performance Config
          </button>
        </div>

        {statusMsg && (
          <div style={{ padding: '10px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#10B981', borderRadius: '8px', fontSize: '0.85rem', textAlign: 'center' }}>
            {statusMsg}
          </div>
        )}
      </div>
    </div>
  );
}
