# RetailVision v2.0 — AI People-Counting & Zone Occupancy Platform

**RetailVision** is an AI-powered people-counting and footfall analytics system designed for retail stores. It processes video 100% locally using computer vision to provide real-time occupancy counting and privacy-first store analytics.

## Documentation & User Manuals

- **Store Owner & Manager Manual**: For step-by-step instructions written for non-technical users on setting up cameras, drawing zones with mouse click & drag, reading dashboards, and generating reports, see [docs/USAGE_GUIDE.md](file:///d:/projects/retailvision/docs/USAGE_GUIDE.md).
- **Product Requirements Document**: See [PRD.md](file:///d:/projects/retailvision/PRD.md) for technical scope, specifications, and architecture decisions.

---

## Features

- **Zone-Based Live Occupancy**: Live self-correcting occupancy counting using foot-point polygon detection and N-frame hysteresis to eliminate boundary jitter.
- **100% On-Premises Privacy**: All AI inference stays local on the device. No video frames ever leave the store.
- **Multi-Camera Support**: Supports USB webcams, RTSP CCTV streams, and ONVIF IP security cameras.
- **Interactive Visual Zone Setup**: Click and drag polygon handles directly on the live camera stream to outline store boundaries — zero coordinate typing required.
- **Adaptive Performance Mode**: Hardware benchmarking auto-configures frame sampling, inference resolution, and model variants for edge devices (Intel N100, Raspberry Pi 5) or high-spec PCs.
- **Offline Cloud Sync & Remote Dashboard**: Queues aggregate hourly footfall statistics locally during internet dropouts and syncs automatically when online.
- **Multi-Format Exports**: Export daily, weekly, and monthly reports as CSV, formatted Excel (`.xlsx`), or PDF.

---

## Quick Start

### 1. Install Dependencies
```powershell
.\retailvision-env\Scripts\pip.exe install -r requirements.txt
```

### 2. Run Local Engine & Dashboard
```powershell
.\retailvision-env\Scripts\python.exe run_v2.py
```
Open your browser at **http://localhost:8000**.

### 3. Run Remote Cloud Service & Viewer (Optional)
```powershell
.\retailvision-env\Scripts\python.exe run_cloud.py
```
Open your browser at **http://localhost:8001**.

---

## Automated Test Suite

Run pytest to execute the full unit and integration test suite:
```powershell
.\retailvision-env\Scripts\python.exe -m pytest tests/ -v
```
