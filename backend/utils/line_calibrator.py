"""Interactive mouse-based line calibration for Phase 1 setup."""

from __future__ import annotations

import cv2


def select_line_interactive(capture, window_name: str = "Set Counting Line"):
    """
    Show a live preview and let the user click two points to define
    the counting line. Left-click sets point 1, second left-click sets
    point 2. Press 'r' to reset, ENTER/SPACE to confirm, 'q' to cancel
    and keep the existing config default.

    Returns (point_1, point_2) as (x, y) tuples, or None if cancelled.
    """
    points: list[tuple[int, int]] = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
            points.append((x, y))

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)

    print("\n--- Line calibration ---")
    print("Click TWO points on the window to draw the counting line.")
    print("Press 'r' to reset, ENTER to confirm, 'q' to skip.\n")

    while True:
        ok, frame = capture.read()
        if not ok:
            continue

        display = frame.copy()

        # Draw points/line as the user places them
        for p in points:
            cv2.circle(display, p, 6, (0, 200, 255), -1)
        if len(points) == 2:
            cv2.line(display, points[0], points[1], (0, 255, 255), 2)

        # Show live pixel coords under the cursor via text hint
        hint = f"Points: {points}   (window size: {frame.shape[1]}x{frame.shape[0]})"
        cv2.putText(display, hint, (10, 25), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(window_name, display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            points.clear()
        elif key in (13, 32) and len(points) == 2:  # ENTER or SPACE
            cv2.destroyWindow(window_name)
            print(f"Line set: {points[0]} -> {points[1]}\n")
            return points[0], points[1]
        elif key == ord('q'):
            cv2.destroyWindow(window_name)
            print("Calibration skipped — using config default.\n")
            return None