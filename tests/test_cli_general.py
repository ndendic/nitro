"""
Tests for general CLI commands (nitro --help, nitro --version)
"""
import subprocess
import re
import pytest


class TestCLIHelp:
    """Test nitro --help command"""

    def test_help_shows_available_commands(self):
        """Verify --help shows all command groups"""
        result = subprocess.run(
            ["uv", "run", "nitro", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        output = result.stdout

        # Verify main usage line
        assert "Usage:" in output
        assert "nitro" in output

        # Verify command groups are shown
        assert "tw" in output.lower() or "tailwind" in output.lower()
        assert "db" in output.lower() or "database" in output.lower()

        # Verify options are shown
        assert "--help" in output
        assert "--version" in output

    def test_help_output_formatted_with_rich(self):
        """Verify help output is formatted nicely"""
        result = subprocess.run(
            ["uv", "run", "nitro", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        output = result.stdout

        # Rich formatting uses box drawing characters
        # Check for common patterns in Rich/Typer output
        assert "─" in output or "Options" in output or "Commands" in output

    def test_subcommand_help_works(self):
        """Verify subcommand --help works"""
        result = subprocess.run(
            ["uv", "run", "nitro", "tw", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        output = result.stdout

        assert "Tailwind" in output
        assert "init" in output
        assert "dev" in output
        assert "build" in output


class TestCLIVersion:
    """Test nitro --version command"""

    def test_version_shows_framework_version(self):
        """Verify --version displays version number"""
        result = subprocess.run(
            ["uv", "run", "nitro", "--version"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        output = result.stdout.strip()

        # Should show "nitro X.Y.Z" format
        assert "nitro" in output.lower()

        # Should have version number (X.Y.Z format)
        version_pattern = r'\d+\.\d+\.\d+'
        assert re.search(version_pattern, output), f"Version not found in: {output}"

    def test_version_format_is_semver(self):
        """Verify version follows semantic versioning"""
        result = subprocess.run(
            ["uv", "run", "nitro", "--version"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0
        output = result.stdout.strip()

        # Extract version number
        version_pattern = r'(\d+)\.(\d+)\.(\d+)'
        match = re.search(version_pattern, output)

        assert match, f"Version not in semver format: {output}"
        major, minor, patch = match.groups()

        # Verify they're valid integers
        assert int(major) >= 0
        assert int(minor) >= 0
        assert int(patch) >= 0


class TestCLIErrorHandling:
    """Test CLI error handling and messages"""

    def test_invalid_command_shows_helpful_error(self):
        """Verify invalid commands show helpful messages"""
        result = subprocess.run(
            ["uv", "run", "nitro", "invalid-command"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        # Should exit with non-zero code
        assert result.returncode != 0

        # Error output should be helpful
        error_output = result.stderr
        assert "invalid-command" in error_output.lower() or "no such command" in error_output.lower()

    def test_no_command_shows_help(self):
        """Verify running 'nitro' alone shows help or error"""
        result = subprocess.run(
            ["uv", "run", "nitro"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        # Either shows help (exit 0) or error (exit non-zero)
        # Both are acceptable behaviors
        output = result.stdout + result.stderr

        # Should mention how to get help or show usage
        assert "usage" in output.lower() or "help" in output.lower() or "commands" in output.lower()


class TestCLIIntegration:
    """Integration tests for CLI functionality"""

    def test_cli_accessible_from_path(self):
        """Verify CLI can be run via uv run"""
        result = subprocess.run(
            ["uv", "run", "nitro", "--version"],
            capture_output=True,
            text=True,
            cwd="/home/ndendic/Projects/auto-nitro/nitro"
        )

        assert result.returncode == 0

    def test_all_command_groups_accessible(self):
        """Verify all command groups can be accessed"""
        command_groups = ["tw", "db"]

        for group in command_groups:
            result = subprocess.run(
                ["uv", "run", "nitro", group, "--help"],
                capture_output=True,
                text=True,
                cwd="/home/ndendic/Projects/auto-nitro/nitro"
            )

            assert result.returncode == 0, f"Command group '{group}' failed"
            assert len(result.stdout) > 0, f"No output from '{group} --help'"
