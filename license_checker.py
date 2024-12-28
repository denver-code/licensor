import requests
import uuid
import platform
import psutil
import time
from typing import Optional, Callable
from datetime import datetime


class LicenseError(Exception):
    pass


class LicenseChecker:
    def __init__(self, license_key: str, api_url: str):
        self.license_key = license_key
        self.api_url = api_url
        self.cached_token: Optional[str] = None
        self.last_check: Optional[float] = None

    @staticmethod
    def get_hardware_id() -> str:
        """Generate a unique hardware identifier."""
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory().total

        # Create a unique identifier based on hardware information
        hardware_info = f"{system}:{machine}:{processor}:{cpu_count}:{memory}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, hardware_info))

    def validate_license(self) -> bool:
        """Validate the license with the server."""
        if self.last_check and self.cached_token:
            if time.time() - self.last_check < 3600:
                return True

        try:
            response = requests.post(
                f"{self.api_url}/api/validate",
                json={
                    "license_key": self.license_key,
                    "hardware_id": self.get_hardware_id(),
                },
            )

            if response.status_code != 200:
                raise LicenseError(f"License validation failed: {response.text}")

            data = response.json()
            if data["valid"]:
                self.cached_token = data["token"]
                self.last_check = time.time()
                return True

            return False

        except requests.RequestException as e:
            raise LicenseError(f"Failed to contact license server: {str(e)}")

    def check_and_run(self, func: Callable) -> None:
        """Run a function only if the license is valid."""
        if self.validate_license():
            return func()
        else:
            raise LicenseError("Invalid license")
