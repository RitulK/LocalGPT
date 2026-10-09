import psutil
from typing import Dict

class HardwareService:
    """Detects system hardware capabilities for model fit scoring."""

    def get_available_resources(self) -> Dict[str, float]:
        """
        Returns available system memory in GB.
        VRAM detection is OS-specific and often requires external tools;
        falling back to total RAM for basic fit estimation.
        """
        mem = psutil.virtual_memory()
        return {
            "ram_gb": round(mem.available / (1024**3), 2),
            "total_ram_gb": round(mem.total / (1024**3), 2),
        }

hardware_service = HardwareService()
