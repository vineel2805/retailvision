# Product Requirements Document (PRD)

# RetailVision
### AI-Powered People Counting, Footfall Analytics & Remote Monitoring Platform

**Version:** 2.0 (MVP+)
**Document Owner:** Product Team
**Status:** Draft — Approved for Development
**Target Release:** MVP v1.0
**Last Updated:** July 2026

---

## Document Revision History

| Version | Date | Changes | Author |
|---|---|---|---|
| 1.0 | — | Initial PRD (local-only MVP) | Product Team |
| 2.0 | July 2026 | Added low-power hardware tier, remote dashboard access, revised AI pipeline for CPU efficiency, expanded NFRs | Product Team |

---

## 1. Executive Summary

RetailVision is an AI-powered application that enables retail businesses to automatically count customer entries and exits using existing CCTV cameras or USB webcams. The system processes video **locally** using computer vision, ensuring privacy and offline reliability, while optionally syncing **anonymized aggregate statistics** to the cloud so store owners can view footfall analytics remotely from any device.

The platform is designed to run on both **high-spec** and **low-power/low-cost hardware**, making it accessible to small and medium retail stores without requiring expensive infrastructure.

**Key differentiators of v2.0:**
- Runs on low-power edge devices (Raspberry Pi 5, Intel N100 mini PCs) in addition to standard PCs
- Owner can view live occupancy and reports from home/anywhere via a secure remote dashboard
- No video ever leaves the store — only anonymous numeric counts are synced

---

## 2. Problem Statement

Small and medium retail stores lack reliable, affordable tools to measure customer footfall. Current pain points:

- Manual counting is inaccurate and unscalable
- No historical analytics or peak-hour visibility
- No real-time occupancy awareness
- Enterprise-grade people-counting systems are cost-prohibitive
- Existing solutions often require constant on-site presence to check numbers — owners can't monitor their store when away

---

## 3. Vision

Provide an affordable, privacy-respecting AI people-counting solution that:
- Installs in under 10 minutes using existing cameras
- Runs reliably on low-cost hardware
- Lets owners check their store's performance from anywhere, without exposing any video or personal data

---

## 4. Goals

### 4.1 Business Goals
- Minimize hardware cost to widen addressable market (support sub-$150 edge devices)
- Reuse existing CCTV infrastructure — no camera replacement required
- Provide actionable, real-time and historical business insights
- Enable remote visibility to increase daily engagement with the product

### 4.2 Product Goals
- ≥98% counting accuracy under normal conditions
- Support USB webcams, RTSP CCTV, ONVIF/IP cameras
- Run fully offline for core counting (no internet dependency for accuracy)
- Optional lightweight cloud sync for remote dashboard access
- Adaptive performance — same software works on a Raspberry Pi or a gaming PC
- Simple, guided installation and setup

---

## 5. Non-Goals (MVP)

Explicitly excluded from MVP scope:

- Face Recognition / Biometric Identification
- Unique Visitor Detection (de-duplication across days)
- Gender, Age, or Emotion Detection
- Heat Maps
- Queue / Dwell-Time Analytics
- Multi-store aggregated management (single store only in MVP)
- Mobile native app (remote access via responsive web is in-scope; native app is post-MVP)
- Employee Attendance
- POS Integration
- Cloud-based video processing or storage (all AI inference stays local)

---

## 6. Target Users

### 6.1 Primary
Small retail stores: Grocery, Pharmacy, Electronics, Clothing, Mobile Shops, Gift Shops, Book Stores

### 6.2 Secondary
Salons, Clinics, Cafes, Restaurants, Offices

---

## 7. User Personas

### 7.1 Store Owner
**Needs:** Daily/monthly visitor counts, peak hours, occupancy, exportable reports, **ability to check all of this from home or while traveling**
**Pain Points:** No visibility into customer flow; can't measure marketing effectiveness; currently must be physically present or call staff to get any sense of store activity

### 7.2 Store Manager
**Needs:** Live occupancy, camera health status, daily reports, on-site alerts

---

## 8. Success Metrics

| Metric | Target |
|---|---|
| Counting Accuracy | ≥98% |
| System Uptime (local) | 99% |
| Processing FPS (standard hardware) | 20+ FPS |
| Processing FPS (low-power hardware) | 8–12 FPS (frame-skipping enabled) |
| Local Dashboard Latency | <1 second |
| Remote Dashboard Refresh Latency | <3 seconds |
| False Count Rate | <2% |
| Time to First Successful Camera Setup | <5 minutes |

---

## 9. Functional Requirements

### FR-001 Camera Management
System shall support USB Webcam, RTSP CCTV, ONVIF/IP Camera.
User can: add camera, remove camera, test connection, preview feed.

### FR-002 Live Video Display
System shall display live camera feed, current FPS, and camera connection status.

### FR-003 Person Detection
System shall detect **only** persons. Must ignore animals, vehicles, posters, TV/screen reflections, and static objects.

### FR-004 Person Tracking
Each detected person receives a temporary tracking ID, valid only while continuously visible in frame. Re-entry after leaving frame may assign a new ID (expected behavior — no persistent identity is stored, by design, for privacy).

### FR-005 Line Crossing Configuration
Administrator places one virtual counting line via the setup UI (drag two points on the live preview). Direction of crossing determines entry vs. exit.

### FR-006 Counting Logic
Every valid line crossing increments the respective counter. Visits are counted, not unique individuals (a person leaving and re-entering counts as a new entry).

### FR-007 Occupancy Calculation
`Current Occupancy = Entry Count − Exit Count`
Value cannot go below zero; system auto-corrects drift via periodic recalibration logic (see FR-016).

### FR-008 Local Dashboard
Displays: Today's Entries, Today's Exits, Current Occupancy, Current Time, Camera Status, AI Status, FPS, CPU Usage.

### FR-009 Reports
Daily, Weekly, Monthly, and Custom Date Range reports with hourly breakdowns and peak-hour identification.

### FR-010 Data Export
Export reports as CSV, Excel (.xlsx), and PDF.

### FR-011 Automatic Daily Reset
Entry/Exit/Occupancy counters reset at midnight (configurable). Historical event data is retained indefinitely in the local database (subject to storage limits/archival policy).

### FR-012 Remote Dashboard Access *(New in v2.0)*
Store owner can view a read-only summary dashboard (today's entries/exits/occupancy, recent trend charts) from any internet-connected device (phone browser, laptop) without being on the store's local network.
- Only aggregated numeric data is transmitted — never video or frames.
- Dashboard updates on a polling/push interval (target: every 30–60 seconds).

### FR-013 Offline Queueing & Sync *(New in v2.0)*
If the store's internet connection drops, the local app continues counting normally and queues unsynced summary data locally. On reconnection, queued data syncs automatically without data loss or duplication.

### FR-014 Adaptive Performance Mode *(New in v2.0)*
On first run, the system benchmarks the host device (CPU cores, available RAM, presence of GPU/accelerator) and automatically selects:
- Model variant (nano vs. small)
- Frame processing rate (full vs. skip-frame)
- Input resolution for inference
This is configurable/overridable by an advanced user in Settings.

### FR-015 Remote Authentication *(New in v2.0)*
Remote dashboard access requires a separate login (token/password) from the local admin console. Supports basic session expiry and logout.

### FR-016 Occupancy Drift Correction *(New in v2.0)*
Periodic (e.g., end-of-day, or on idle detection with zero motion) reconciliation logic to correct occupancy drift caused by missed detections, ensuring long-run accuracy doesn't degrade over multi-day continuous operation.

---

## 10. Non-Functional Requirements

### 10.1 Performance

| Requirement | Low-Power Tier | Standard Tier | Recommended Tier |
|---|---|---|---|
| Startup Time | <15 sec | <10 sec | <10 sec |
| Local Processing Latency | <800 ms | <500 ms | <300 ms |
| RAM Usage | <1 GB | <2 GB | <2 GB |
| CPU Usage (sustained) | <60% | <50% | <30% |
| Target FPS | 8–12 | 15–20 | 25–30 |
| GPU | Not required | Optional | Recommended (RTX 3050+) |

### 10.2 Reliability
- Must run continuously for 12+ hours without crash or memory leak (24-hour soak test required pre-release)
- Automatic camera reconnection on disconnect
- Graceful degradation: if AI inference fails, system logs the error, alerts the user, and attempts automatic restart of the inference engine without requiring app restart

### 10.3 Scalability (within MVP scope)
- Single store, single camera in MVP
- Architecture should not preclude future multi-camera/multi-store expansion (post-MVP roadmap)

---

## 11. Supported Hardware

### 11.1 Low-Power Tier *(New in v2.0)*
- Intel N100 Mini PC or Raspberry Pi 5 (8GB)
- No dedicated GPU
- USB Webcam or RTSP camera over LAN
- Optional: Google Coral USB Accelerator / Hailo-8 for improved FPS

### 11.2 Standard (Minimum) Tier
- Intel i5, 8GB RAM, Integrated Graphics, Windows 10+, USB Camera

### 11.3 Recommended Tier
- Intel i7, 16GB RAM, RTX 3050+

---

## 12. Supported Cameras

- USB Webcam
- RTSP streams
- ONVIF-compatible IP Cameras
- Resolution: 720p or 1080p
- Recommended FPS: 20–30 (source), processed at adaptive rate per FR-014

---

## 13. AI Pipeline (Revised)

```
Video Source
    ↓
Frame Capture
    ↓
Adaptive Frame Sampling (skip frames on low-power devices)
    ↓
ROI Cropping (process only region near counting line)
    ↓
Person Detection (YOLOv8-nano, ONNX Runtime, INT8 quantized)
    ↓
Tracking (ByteTrack)
    ↓
Virtual Line Crossing Check
    ↓
Direction Detection
    ↓
Entry/Exit Event
    ↓
SQLite Database (local)
    ↓
Local Dashboard  +  Sync Queue → Cloud API → Remote Dashboard
```

**Key model/runtime decisions:**
- Default model: **YOLOv8n**, exported to **ONNX** with **INT8 quantization** for CPU efficiency
- **ROI cropping**: inference limited to the region surrounding the counting line rather than the full frame, reducing compute load significantly
- **Frame-skipping**: on low-power tier, process every 2nd–3rd frame; full-frame processing not required for accurate line-crossing detection
- Optional hardware acceleration: Intel OpenVINO (iGPU/NPU), Coral USB, Hailo-8

---

## 14. Database Design

### 14.1 Local Database (SQLite)

**Cameras**
| Field | Type |
|---|---|
| id | INTEGER |
| name | TEXT |
| source_type | TEXT |
| source_url | TEXT |
| status | TEXT |

**Visitor Events**
| Field | Type |
|---|---|
| id | INTEGER |
| timestamp | DATETIME |
| direction | TEXT |
| confidence | REAL |
| tracking_id | INTEGER |
| camera_id | INTEGER |

**Daily Summary**
| Field | Type |
|---|---|
| date | DATE |
| entries | INTEGER |
| exits | INTEGER |
| occupancy | INTEGER |

**Sync Queue** *(New in v2.0)*
| Field | Type |
|---|---|
| id | INTEGER |
| payload | TEXT (JSON) |
| synced | BOOLEAN |
| created_at | DATETIME |

### 14.2 Cloud Database *(New in v2.0)*
Stores only aggregated, anonymized data synced from stores — no video, no raw tracking data, no PII.

**Store Summary (cloud)**
| Field | Type |
|---|---|
| store_id | UUID |
| date | DATE |
| hour | INTEGER |
| entries | INTEGER |
| exits | INTEGER |
| occupancy | INTEGER |
| synced_at | DATETIME |

---

## 15. Dashboard Specification

### 15.1 Local Dashboard (Main Screen)
Live Camera Feed · Today's Entries · Today's Exits · Current Occupancy · Current Time · Camera Health · AI Health · FPS · CPU Usage

### 15.2 Local Dashboard (Analytics)
Hourly Visitors · Daily Visitors · Weekly Trend · Monthly Trend · Peak Hour Identification

### 15.3 Remote Dashboard *(New in v2.0)*
Read-only view accessible via browser from any device:
- Today's Entries/Exits/Occupancy (near-real-time, 30–60s refresh)
- Historical trend charts (daily/weekly/monthly)
- Camera online/offline status indicator
- No live video stream (aggregate stats only, by design — keeps bandwidth and privacy footprint minimal)

---

## 16. Error Handling

| Scenario | Response |
|---|---|
| Camera disconnected | Auto-reconnect attempt → notify user if persists |
| Database unavailable | Retry with backoff → log error |
| AI model/inference failure | Auto-restart inference engine → show warning banner |
| Internet unavailable (for sync) | Continue local operation normally → queue data → sync on reconnect |
| Remote auth failure | Standard invalid-credential response, rate-limited to prevent brute force |

---

## 17. Logging

- System Logs
- AI/Inference Logs
- Camera Logs
- Application Logs
- Sync Logs *(New)*
- Crash Reports

---

## 18. Security

- Local authentication for admin console (local-only access)
- Separate, distinct authentication for remote dashboard access *(New)*
- Encrypted local configuration storage
- All cloud sync traffic encrypted in transit (TLS 1.2+)
- Role-based access: Admin (full control), Viewer (remote, read-only)
- Core counting functionality requires no internet connection

---

## 19. Privacy

- No face recognition
- No biometric storage
- No video ever uploaded or transmitted off-premises
- No cloud-based video processing
- No personally identifiable information stored, locally or in the cloud
- Cloud sync limited strictly to anonymized aggregate counts (entries/exits/occupancy per hour)
- Video remains on the local machine at all times

---

## 20. Tech Stack

### Frontend (Local Desktop App)
React · Electron · Tailwind CSS · Recharts/Chart.js

### Frontend (Remote Web Dashboard) *(New)*
React (shared components with desktop where feasible) · responsive/mobile-friendly layout

### Backend (Local)
Python · FastAPI · APScheduler (for reset/sync jobs)

### Backend (Cloud) *(New)*
FastAPI or Node.js/Express · PostgreSQL (managed, e.g., Supabase/RDS) · JWT-based auth

### AI/Computer Vision
YOLOv8-nano (Ultralytics) · ByteTrack · OpenCV · NumPy · ONNX Runtime (INT8 quantized) · Optional: Intel OpenVINO, Coral/Hailo SDKs

### Database
SQLite (local) · PostgreSQL (cloud aggregate store)

### Packaging & Deployment
PyInstaller · Electron Builder · Docker (cloud backend) · GitHub Actions (CI/CD)

### Hosting (Cloud Layer)
Lightweight VM or serverless platform (Render/Railway/AWS/GCP) — low resource requirement since payloads are small JSON, not video

---

## 21. Folder Structure

```
RetailVision/
├── backend/
│   ├── api/
│   ├── ai/
│   ├── tracking/
│   ├── counting/
│   ├── camera/
│   ├── database/
│   ├── sync/                # new: handles cloud sync + offline queue
│   ├── services/
│   └── utils/
│
├── frontend/
│   ├── src/
│   ├── pages/
│   ├── components/
│   ├── charts/
│   └── assets/
│
├── cloud/                    # new: cloud API + remote dashboard
│   ├── api/
│   ├── auth/
│   └── web-dashboard/
│
├── models/
├── config/
├── logs/
├── exports/
└── installer/
```

---

## 22. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Poor camera angle | Installation guide + live camera preview during setup |
| Low lighting | Recommend minimum lighting; adjustable confidence thresholds |
| Crowded entrances / occlusion | Robust tracking (ByteTrack); configurable line placement; ROI tuning |
| Camera disconnect | Automatic reconnection + alerts |
| Low-spec device can't sustain FPS | Nano model + INT8 quantization + frame-skipping + adjustable resolution |
| Internet outage breaks remote view | Local counting unaffected; offline queueing ensures no data loss on reconnect |
| Occupancy drift over long runtime | Periodic drift-correction reconciliation (FR-016) |
| Privacy concerns from customers/staff | No video/biometric data leaves premises; clearly documented privacy policy |

---

## 23. Acceptance Criteria

MVP is considered successful when:

- A camera can be connected and configured in under 5 minutes
- Live video displays reliably on both low-power and standard hardware
- Entries and exits are counted with ≥98% accuracy under normal conditions
- Current occupancy updates in real time on the local dashboard
- Remote dashboard reflects store data within 60 seconds of an event, when internet is available
- Daily, weekly, and monthly reports generate correctly
- Event data persists after application restart and after internet outages
- The application runs continuously for at least 12 hours without crashing
- Reports export correctly to CSV, Excel, and PDF
- Core counting functionality works fully offline
- System runs within defined RAM/CPU limits on the low-power hardware tier

---

## 24. Future Roadmap (Post-MVP)

- Multi-camera support (single store)
- Multi-store management with aggregated cross-store dashboard
- Native mobile app (iOS/Android) for remote monitoring
- Real-time push alerts (e.g., occupancy threshold exceeded)
- REST API for third-party integrations
- Heat maps and dwell-time analytics
- Queue analytics
- Employee/customer differentiation
- POS integration
- Business intelligence / advanced reporting dashboards
- OTA software and AI model auto-updates
- On-device hardware acceleration expansion (broader NPU/accelerator support)

---

## 25. Product Definition (Final)

**RetailVision** is a privacy-first, AI-powered people-counting platform for single-store retailers. It runs on both standard PCs and low-cost edge devices, using existing CCTV or USB cameras to count customer entries/exits and calculate real-time occupancy — entirely offline. Store owners additionally get secure, remote access to aggregated analytics from any device, anywhere, without any video or personal data ever leaving the store premises.

---

*End of Document*