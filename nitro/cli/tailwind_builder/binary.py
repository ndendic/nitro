"""Tailwind CSS binary management."""

import hashlib
import platform
import shutil
from pathlib import Path

import requests


class BinaryError(Exception):
    """Binary management error."""

    pass


class NetworkError(BinaryError):
    """Network error during download."""

    pass


class VerificationError(BinaryError):
    """Binary verification failed."""

    pass


def get_platform_info() -> tuple[str, str]:
    system = platform.system()
    machine = platform.machine()

    platform_map = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}
    arch_map = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "AMD64": "x64"}

    if system not in platform_map:
        raise BinaryError(f"Unsupported platform: {system}")
    if machine not in arch_map:
        raise BinaryError(f"Unsupported architecture: {machine}")

    return platform_map[system], arch_map[machine]


def get_binary_name(platform_name: str, arch: str) -> str:
    base = f"tailwindcss-{platform_name}-{arch}"
    return f"{base}.exe" if platform_name == "windows" else base


def get_cache_dir(version: str) -> Path:
    cache_dir = Path.home() / ".nitro" / "cache" / version
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class TailwindBinaryManager:
    """Manages Tailwind CSS binaries."""

    DEFAULT_VERSION = "latest"
    GITHUB_RELEASES_URL = (
        "https://github.com/tailwindlabs/tailwindcss/releases/download"
    )
    GITHUB_API_URL = (
        "https://api.github.com/repos/tailwindlabs/tailwindcss/releases/latest"
    )

    def __init__(self, version: str | None = None):
        self.version = version or self.DEFAULT_VERSION

    def _get_latest_version(self) -> str:
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            return response.json().get("tag_name", "v4.0.0-beta.2")
        except requests.RequestException:
            return "v4.0.0-beta.2"  # Fallback

    def _get_download_url(self) -> str:
        platform_name, arch = get_platform_info()
        binary_name = get_binary_name(platform_name, arch)

        if self.version == "latest":
            version = self._get_latest_version()
            return f"{self.GITHUB_RELEASES_URL}/{version}/{binary_name}"
        return f"{self.GITHUB_RELEASES_URL}/v{self.version}/{binary_name}"

    def _get_binary_path(self, cache_dir: Path | None = None) -> Path:
        if cache_dir is None:
            cache_dir = get_cache_dir(self.version)

        platform_name, arch = get_platform_info()
        return cache_dir / get_binary_name(platform_name, arch)

    def _download_binary(
        self, url: str, binary_path: Path, checksum: str | None = None
    ) -> None:
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            binary_path.parent.mkdir(parents=True, exist_ok=True)
            binary_path.write_bytes(response.content)
            binary_path.chmod(binary_path.stat().st_mode | 0o755)

            if checksum:
                actual = hashlib.sha256(binary_path.read_bytes()).hexdigest()
                if actual != checksum:
                    raise VerificationError(
                        f"Checksum mismatch: {actual} != {checksum}"
                    )

        except requests.RequestException as e:
            raise NetworkError(f"Failed to download: {e}") from e

    def _is_valid_tailwind_binary(self, binary_path: Path) -> bool:
        """Check if the binary is the actual Tailwind CSS standalone CLI."""
        try:
            import subprocess
            result = subprocess.run(
                [str(binary_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # The real Tailwind CLI should mention "tailwindcss" and have standard options
            # Python wrapper has Python-specific commands like "download"
            help_text = result.stdout.lower()
            return (
                "tailwindcss" in help_text and
                ("--input" in help_text or "--output" in help_text) and
                "download" not in help_text  # Python wrapper has download command
            )
        except Exception:
            return False

    def get_binary(
        self, cache_dir: Path | None = None, checksum: str | None = None
    ) -> Path:
        # Check cache first (prefer our downloaded binary)
        binary_path = self._get_binary_path(cache_dir)
        if binary_path.exists() and self._is_valid_tailwind_binary(binary_path):
            return binary_path

        # Check system PATH, but validate it's the real Tailwind CLI
        if system_binary := shutil.which("tailwindcss"):
            system_path = Path(system_binary)
            if self._is_valid_tailwind_binary(system_path):
                return system_path

        # Download the real Tailwind CLI
        self._download_binary(self._get_download_url(), binary_path, checksum)
        return binary_path

    def clear_cache(self) -> None:
        cache_dir = get_cache_dir(self.version)
        if cache_dir.exists():
            shutil.rmtree(cache_dir)

    @classmethod
    def list_cached_versions(cls) -> list[str]:
        cache_base = Path.home() / ".nitro" / "cache"
        if not cache_base.exists():
            return []
        return sorted(d.name for d in cache_base.iterdir() if d.is_dir())
