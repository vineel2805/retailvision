"""Adaptive Performance Mode manager (FR-014).

Benchmarks hardware (CPU, RAM, GPU) on initial boot and auto-selects:
- Model variant (nano vs. small)
- Frame processing rate (full vs. skip-frame)
- Input resolution for inference
- ROI cropping enablement

Can be manually overridden via settings.
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict

import psutil
import torch

logger = logging.getLogger("retailvision.ai.adaptive")


@dataclass
class AdaptiveConfig:
    tier: str  # "low_power", "standard", "recommended"
    model_name: str  # "yolov8n.pt", "yolov8s.pt", etc.
    frame_skip: int  # 1 = process every frame, 2 = process every 2nd frame, etc.
    inference_size: int  # 320, 480, 640
    roi_enabled: bool  # True / False
    use_onnx: bool  # True / False
    cpu_cores: int
    ram_gb: float
    gpu_available: bool
    gpu_name: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptivePerformanceManager:
    """Detects system hardware resources and determines optimal pipeline settings."""

    @staticmethod
    def benchmark_system() -> AdaptiveConfig:
        cpu_cores = os.cpu_count() or 2
        ram_bytes = psutil.virtual_memory().total
        ram_gb = round(ram_bytes / (1024**3), 2)

        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None"

        logger.info(
            f"Hardware Benchmark: CPU={cpu_cores} cores, RAM={ram_gb} GB, GPU={gpu_name}"
        )

        if gpu_available or (cpu_cores >= 8 and ram_gb >= 15.0):
            tier = "recommended"
            model_name = "yolov8n.pt"
            frame_skip = 1
            inference_size = 640
            roi_enabled = False
            use_onnx = False
        elif cpu_cores >= 4 and ram_gb >= 6.0:
            tier = "standard"
            model_name = "yolov8n.pt"
            frame_skip = 1
            inference_size = 640
            roi_enabled = True
            use_onnx = True
        else:
            tier = "low_power"
            model_name = "yolov8n.pt"
            frame_skip = 2
            inference_size = 480
            roi_enabled = True
            use_onnx = True

        config = AdaptiveConfig(
            tier=tier,
            model_name=model_name,
            frame_skip=frame_skip,
            inference_size=inference_size,
            roi_enabled=roi_enabled,
            use_onnx=use_onnx,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            gpu_available=gpu_available,
            gpu_name=gpu_name,
        )

        logger.info(f"Auto-selected performance tier: {tier.upper()} ({config})")
        return config
