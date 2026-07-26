# RetailVision User Guide: Store Owner & Manager Manual

Welcome to **RetailVision**, your automated AI footfall and store occupancy system. This guide is written in plain language to help store owners and managers set up cameras, outline store monitoring zones, view live customer footfall, and generate reports — no technical background required.

---

## 1. How to Switch or Add a Camera

To configure your video source (such as your store's CCTV camera or a USB webcam plugged into the computer):

1. Open the **RetailVision Dashboard** in your web browser.
2. Click the **Settings** tab in the top navigation bar.
3. Look at the **Multi-Camera Setup** section:
   - **Camera Name**: Type a helpful label for your camera (e.g., *Main Store Entrance* or *Front Counter*).
   - **Source Type**: Select the type of camera you are connecting:
     - **USB Webcam**: A camera plugged directly into a USB port on the computer.
     - **RTSP Stream (CCTV)**: A standard IP security camera or NVR/DVR streaming over your store's local Wi-Fi or network cable.
     - **ONVIF IP Camera**: An ONVIF-compatible smart security camera.
   - **Device Index or Stream URL**:
     - For **USB Webcams**: Type `0` for the built-in or default camera, or `1` if you have a second camera plugged in.
     - For **RTSP / ONVIF Cameras**: Type the full network stream address provided by your camera installer (e.g., `rtsp://admin:password123@192.168.1.100:554/stream1`).
4. Click **Save Camera Config**.
5. The system will connect to the new camera stream automatically. The status badge at the top right will change to **Camera Online** in green.

---

## 2. How to Outline and Resize the Store Counting Zone

RetailVision measures occupancy by checking when customers' feet are inside your designated store area. You can outline your store floor directly on the video screen without typing any coordinates.

### Setting Up Your Zone Step by Step:

1. Click the **Zone Setup** tab in the top navigation bar.
2. You will see your camera's live video stream with a semi-transparent highlighted area overlaid on top.
3. **Reshaping the Zone**:
   - Look for the **cyan circular handles** (labeled P1, P2, P3, P4) on the video corners.
   - **Click and drag** any corner handle with your mouse to move it directly to where your store doorway or shop floor starts.
4. **Adding New Corner Handles**:
   - To make a custom shape (like an L-shaped entrance or angled doorway), click anywhere directly on the video picture to add a new point, or click the **Add Corner Point** button.
   - Drag the new handle to outline your store boundaries.
5. **Resetting**:
   - If you want to start over, click **Reset Box** to restore the default rectangle.
6. **Saving**:
   - Once the highlighted shape accurately covers your customer entrance or store interior, click **Save Zone Configuration**. The new shape will take effect immediately.

### Understanding the Hysteresis / Confirmation Slider:
- Below the zone controls, you will see the **Hysteresis Window** slider (default: `5` frames).
- **What it does**: This ensures a customer must be inside or outside the zone for a few split seconds before the system records a count. It prevents false counts if someone briefly pauses right on the boundary edge.
- **Should you change it?**: The default setting (`5`) works best for almost all retail stores. You only need to increase it if your doorway gets heavy foot traffic where people linger near the doorway line.

---

## 3. How to Read the Live Monitor Dashboard

Click the **Live Monitor** tab to view your store's real-time performance.

### Understanding the Stat Cards:
- **Today's Entries**: The total number of customer entries detected since midnight.
- **Today's Exits**: The total number of customer exits detected since midnight.
- **Current Occupancy**: The exact number of customers currently inside your store right now. This number is updated live every frame.
- **Inference FPS**: Processing speed (frames per second). Numbers between 15 and 30 indicate smooth, real-time performance.
- **CPU Usage & RAM Usage**: Shows how much computer power the system is using. Normal CPU usage is usually under 50%.

### Understanding Status Badges (Top Right):
- **Camera Online** (Green): Your camera is connected and sending clear video frames.
- **Camera Offline** (Red): The computer cannot reach the camera. Check that the USB cable is plugged in or that the CCTV network cable is powered on.
- **AI Engine Healthy** (Green): The artificial intelligence model is actively detecting and tracking people.
- **AI Engine Degraded** (Red/Orange): The system encountered a temporary error. It will automatically restart the AI processing within a few seconds.

---

## 4. How to Generate & Export Reports

To view customer flow trends over time or download sales/footfall analytics:

1. Click the **Analytics & Reports** tab.
2. Select your desired date range using the **Start Date** and **End Date** selectors at the top.
3. The dashboard will automatically calculate:
   - **Range Total Entries**: Total shoppers who entered during the selected period.
   - **Range Total Exits**: Total shoppers who left during the selected period.
   - **Peak Traffic Hour**: The specific hour of the day that received the highest customer volume (e.g., `14:00` / 2:00 PM).
   - **Hourly Traffic Breakdown Chart**: A bar chart displaying entries and exits for every hour of the day.
4. **Downloading Reports**:
   - Click **CSV** to download raw data for spreadsheet analysis.
   - Click **Excel** to download a formatted `.xlsx` workbook with tables and totals.
   - Click **PDF** to generate a printable store summary report.

---

## 5. Troubleshooting Guide

| Problem | Cause | Plain-Language Fix |
|---|---|---|
| **Camera shows Offline** | Cable unplugged or wrong RTSP stream address. | Check that the USB camera cable is secure. If using a CCTV camera, verify your Wi-Fi/router connection and double-check the stream URL in **Settings**. |
| **AI Engine shows Degraded** | Temporary graphics or memory hitch on the computer. | RetailVision automatically recovers within 5–10 seconds. If it stays degraded, restart the app by opening `run_v2.py`. |
| **Zone Configuration Won't Save** | Polygon shape has fewer than 3 points. | Make sure your zone shape has at least 3 corner handles before clicking **Save Zone Configuration**. |
| **Occupancy Count Seems Incorrect** | Zone boundary is placed where customers queue or stand outside. | Open **Zone Setup** and drag the boundary handles inward so the zone strictly covers the interior shop floor, away from outside sidewalk foot traffic. |

---

*For further assistance or advanced multi-store setup, consult your RetailVision administrator.*
