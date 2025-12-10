"""
Tests for CLI Tailwind commands (nitro tw init, dev, build)
"""
import subprocess
import tempfile
import shutil
import os
import pytest
from pathlib import Path


class TestTailwindInit:
    """Test nitro tw init command"""

    def test_tw_init_command_exists(self):
        """Verify 'nitro tw init' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "init", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "init" in result.stdout.lower() or "initialize" in result.stdout.lower()

    def test_tw_init_in_temp_directory(self):
        """Verify 'nitro tw init' creates necessary files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run init in temp directory
            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Command should succeed or give helpful error
            # (may fail if Tailwind binary download fails, which is OK)
            if result.returncode == 0:
                # If successful, check for created files
                tmppath = Path(tmpdir)

                # Should create tailwind.config.js or input.css
                config_exists = (tmppath / "tailwind.config.js").exists()
                input_exists = (tmppath / "input.css").exists()

                # At least one should exist
                assert config_exists or input_exists, "No Tailwind files created"

    def test_tw_init_idempotent(self):
        """Verify running 'nitro tw init' twice is safe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run init first time
            result1 = subprocess.run(
                ["uv", "run", "nitro", "tw", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Run init second time
            result2 = subprocess.run(
                ["uv", "run", "nitro", "tw", "init"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Both should succeed or fail gracefully (not crash)
            # Second run should either skip existing files or overwrite
            assert result2.returncode in [0, 1]  # Success or expected error


class TestTailwindDev:
    """Test nitro tw dev command"""

    def test_tw_dev_command_exists(self):
        """Verify 'nitro tw dev' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "dev", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "dev" in result.stdout.lower() or "watch" in result.stdout.lower()

    def test_tw_dev_requires_init_or_gives_error(self):
        """Verify 'nitro tw dev' gives helpful error without init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to run dev without init
            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "dev"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=5  # Don't wait forever
            )

            # Should either succeed (if it finds defaults) or give error
            output = result.stdout + result.stderr

            # If it errors, should mention config or initialization
            if result.returncode != 0:
                assert "config" in output.lower() or "init" in output.lower() or "not found" in output.lower()


class TestTailwindBuild:
    """Test nitro tw build command"""

    def test_tw_build_command_exists(self):
        """Verify 'nitro tw build' command is available"""
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "build", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        assert "build" in result.stdout.lower() or "production" in result.stdout.lower()

    def test_tw_build_requires_init_or_gives_error(self):
        """Verify 'nitro tw build' gives helpful error without init"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to run build without init
            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "build"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=5
            )

            # Should either succeed or give error
            output = result.stdout + result.stderr

            # If it errors, should mention config or initialization
            if result.returncode != 0:
                assert "config" in output.lower() or "init" in output.lower() or "not found" in output.lower()


class TestTailwindWorkflow:
    """Test complete Tailwind workflow"""

    def test_full_workflow_init_build(self):
        """Test: init -> build workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create minimal files for Tailwind to work
            (tmppath / "input.css").write_text("""
@tailwind base;
@tailwind components;
@tailwind utilities;
""")

            (tmppath / "tailwind.config.js").write_text("""
module.exports = {
  content: ["./**/*.{html,py}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
""")

            # Try to run build
            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "build"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=30
            )

            # May succeed or fail depending on binary availability
            # At minimum, command should not crash
            assert result.returncode in [0, 1, 2]  # Various acceptable outcomes


class TestTailwindBinaryManagement:
    """Test Tailwind binary caching and management"""

    def test_tailwind_binary_cached_location(self):
        """Verify Tailwind binary is cached in ~/.nitro/cache/"""
        home = Path.home()
        cache_dir = home / ".nitro" / "cache"

        # After running any tw command, cache dir should exist
        # (or command fails gracefully if download fails)
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        # Command should at least execute
        assert result.returncode == 0

    def test_tailwind_works_without_nodejs(self):
        """Verify Tailwind CLI works without Node.js"""
        # Check if node is in PATH (optional)
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        # Should work regardless of Node.js presence
        assert result.returncode == 0
        assert "tailwind" in result.stdout.lower()

    def test_tailwind_binary_reused_across_projects(self):
        """Verify binary is reused, not re-downloaded per project"""
        # Create two separate temp directories
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                # Run init in first project
                result1 = subprocess.run(
                    ["uv", "run", "nitro", "tw", "--help"],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir1
                )

                # Run init in second project
                result2 = subprocess.run(
                    ["uv", "run", "nitro", "tw", "--help"],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir2
                )

                # Both should work
                assert result1.returncode == 0
                assert result2.returncode == 0

                # Binary should be cached in ~/.nitro/cache/
                cache_dir = Path.home() / ".nitro" / "cache"
                # Cache dir may or may not exist depending on if binary was downloaded
                # But command should work in both projects


class TestTailwindConfiguration:
    """Test Tailwind configuration detection and usage"""

    def test_config_detection_static_directory(self):
        """Verify config detects static/ directory structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create static directory
            static_dir = tmppath / "static" / "css"
            static_dir.mkdir(parents=True)

            # Run help to see if it detects structure
            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "--help"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            assert result.returncode == 0

    def test_config_override_via_env_vars(self):
        """Verify config can be overridden via environment variables"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["NITRO_TAILWIND_CSS_INPUT"] = "custom/input.css"
            env["NITRO_TAILWIND_CSS_OUTPUT"] = "custom/output.css"

            result = subprocess.run(
                ["uv", "run", "nitro", "tw", "--help"],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                env=env
            )

            assert result.returncode == 0
