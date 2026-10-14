#!/usr/bin/env python3
"""
AgentScript Compiler using Nexus @agentscript/cli (TypeScript Implementation)

This compiler uses the official TypeScript-based @agentscript/cli package from
Nexus npm registry. It provides full feature parity with the module-agentscript
CLI and validates AgentScript files before deployment.

Prerequisites:
  - Node.js v18+ installed
  - npm installed (comes with Node.js)
  - tree-sitter-cli installed globally: npm install -g tree-sitter-cli
  - @agentscript/cli installed: npm install --legacy-peer-deps --ignore-scripts
  - Network access to Nexus npm registry

Usage:
  python3 compile_agentscript_nexus_ts.py <path-to-agentscript>

  Or from migration skills:
  python3 skills/00-start-migration/scripts/compile_agentscript_nexus_ts.py <path>

Features:
  - Comprehensive prerequisite validation
  - Verifies Nexus npm registry access
  - Detailed error reporting with source context
  - Compatible with sf agent publish validation
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Union


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'


def log(message, color=Colors.RESET):
    """Print colored message to stdout."""
    print(f"{color}{message}{Colors.RESET}")


def error(message):
    """Print colored error message to stderr."""
    print(f"{Colors.RED}{message}{Colors.RESET}", file=sys.stderr)


def show_source_context(source_lines: List[str], line_number: int, context: int = 2) -> None:
    """Show source code context around an error line."""
    start = max(0, line_number - context - 1)
    end = min(len(source_lines), line_number + context)
    for i, line in enumerate(source_lines[start:end], start=start + 1):
        marker = ">>>" if i == line_number else "   "
        error(f"  {marker} {i:4d} | {line}")


def extract_line_number(error_msg: str) -> Optional[int]:
    """Extract line number from error message."""
    m = re.search(r'\bline\s+(\d+)', error_msg, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r':(\d+):', error_msg)
    if m:
        return int(m.group(1))
    return None


def check_node_installed() -> Tuple[bool, str]:
    """Check if Node.js is installed and return version."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            # Extract major version (e.g., "v20.11.0" -> 20)
            major = int(version.lstrip('v').split('.')[0])
            if major >= 18:
                return True, version
            else:
                return False, f"{version} (requires v18+)"
        return False, "not found"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False, "not found"
    except Exception as e:
        return False, f"error: {e}"


def check_npm_installed() -> tuple[bool, str]:
    """Check if npm is installed and return version."""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "not found"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False, "not found"
    except Exception as e:
        return False, f"error: {e}"


def check_tree_sitter_cli() -> tuple[bool, str]:
    """Check if tree-sitter CLI is installed globally."""
    try:
        result = subprocess.run(
            ["tree-sitter", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, "not found"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False, "not found"
    except Exception as e:
        return False, f"error: {e}"


def find_cli_location() -> Optional[Path]:
    """Find the @agentscript/cli location in node_modules."""
    # Due to path resolution bug in @agentscript/cli, we prefer the local monorepo build
    # where dependencies resolve correctly. The npm-installed version has issues.
    locations = [
        # Prefer local module-agentscript (built correctly with proper paths)
        Path.home() / "vmclaudedir" / "ma-devname" / "module-agentscript" / "packages" / "cli" / "dist" / "index.js",
        # Try current directory (may have path resolution issues)
        Path.cwd() / "node_modules" / "@agentscript" / "cli" / "dist" / "index.js",
        Path(__file__).parent.parent.parent.parent / "node_modules" / "@agentscript" / "cli" / "dist" / "index.js",
    ]

    for loc in locations:
        if loc.exists():
            return loc

    return None


def fix_node_module_paths(project_root: Path) -> bool:
    """
    Fix Node.js module path resolution by creating symlinks.

    @agentscript/cli tries to resolve dependencies from:
      node_modules/@agentscript/cli/node_modules/@agentscript/*
    But npm installs them at:
      node_modules/@agentscript/*

    This function creates symlinks to fix the resolution.
    Returns True if successful or already fixed.
    """
    cli_node_modules = project_root / "node_modules" / "@agentscript" / "cli" / "node_modules"
    target_dir = cli_node_modules / "@agentscript"

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    packages = [
        "agentforce-dialect",
        "compiler",
        "parser",
        "language",
        "types",
        "agentforce",
        "agentscript-dialect",
        "agentfabric-dialect",
    ]

    for package in packages:
        source = project_root / "node_modules" / "@agentscript" / package
        link = target_dir / package

        if not source.exists():
            continue  # Skip missing packages

        if link.is_symlink():
            # Check if it points to the right place
            if link.resolve() == source.resolve():
                continue  # Already correct
            else:
                link.unlink()  # Remove incorrect symlink
        elif link.exists():
            continue  # Real directory exists, don't touch it

        # Create symlink
        try:
            link.symlink_to(source)
        except OSError:
            return False  # Failed to create symlink

    return True


def check_cli_installed() -> Tuple[bool, str, Optional[Path]]:
    """Check if @agentscript/cli is installed."""
    cli_path = find_cli_location()

    if cli_path is None:
        return False, "not found in node_modules", None

    # Fix path resolution by creating symlinks
    project_root = cli_path.parent.parent.parent.parent
    fix_node_module_paths(project_root)

    # Try to get version
    try:
        result = subprocess.run(
            ["node", str(cli_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version, cli_path
        return False, "cannot execute", cli_path
    except Exception as e:
        return False, f"error: {e}", cli_path


def check_nexus_access() -> tuple[bool, str]:
    """Check if Nexus npm registry is accessible."""
    try:
        result = subprocess.run(
            ["npm", "view", "@agentscript/cli", "version"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "cannot access"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {e}"


def run_prerequisites_check(verbose: bool = False) -> bool:
    """Run all prerequisite checks and display results."""
    if verbose:
        log("")
        log(f"{Colors.BOLD}Prerequisites Check{Colors.RESET}", Colors.CYAN)
        log("=" * 60, Colors.CYAN)

    all_passed = True
    checks = []

    # Check 1: Node.js
    node_ok, node_version = check_node_installed()
    checks.append(("Node.js (v18+)", node_ok, node_version))
    if not node_ok:
        all_passed = False

    # Check 2: npm
    npm_ok, npm_version = check_npm_installed()
    checks.append(("npm", npm_ok, npm_version))
    if not npm_ok:
        all_passed = False

    # Check 3: tree-sitter-cli
    ts_ok, ts_version = check_tree_sitter_cli()
    checks.append(("tree-sitter CLI", ts_ok, ts_version))
    if not ts_ok:
        all_passed = False

    # Check 4: @agentscript/cli
    cli_ok, cli_version, cli_path = check_cli_installed()
    checks.append(("@agentscript/cli", cli_ok, f"{cli_version} ({cli_path.parent.parent if cli_path else 'N/A'})"))
    if not cli_ok:
        all_passed = False

    # Check 5: Nexus access (optional but recommended)
    nexus_ok, nexus_version = check_nexus_access()
    checks.append(("Nexus npm registry", nexus_ok, f"@agentscript/cli@{nexus_version}" if nexus_ok else nexus_version))
    # Don't fail if Nexus is unreachable (might be offline compilation)

    # Display results
    if verbose:
        max_name_len = max(len(name) for name, _, _ in checks)
        for name, passed, details in checks:
            status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
            log(f"  {name:<{max_name_len}}  {status}  {Colors.GRAY}{details}{Colors.RESET}")

        log("")

    if not all_passed:
        if verbose:
            log(f"{Colors.RED}Prerequisites check FAILED{Colors.RESET}")
            log("")

        error("Missing prerequisites. Install the following:")
        error("")

        if not node_ok:
            error("  1. Node.js v18+ (required)")
            error("     macOS:   brew install node")
            error("     Linux:   apt-get install nodejs")
            error("     Windows: https://nodejs.org/")
            error("")

        if not npm_ok:
            error("  2. npm (usually comes with Node.js)")
            error("")

        if not ts_ok:
            error("  3. tree-sitter CLI (required)")
            error("     npm install -g tree-sitter-cli")
            error("")

        if not cli_ok:
            error("  4. @agentscript/cli (required)")
            error("     cd <project-root>")
            error("     npm install --legacy-peer-deps --ignore-scripts")
            error("")

        if not nexus_ok:
            log(f"{Colors.YELLOW}  Note: Nexus npm registry is not accessible (not critical for offline use){Colors.RESET}", Colors.YELLOW)
            log("")

        return False

    if verbose:
        log(f"{Colors.GREEN}✓ All prerequisites satisfied{Colors.RESET}")
        log("")

    return True


def verify_nexus_availability(cli_path: Path) -> None:
    """Verify that @agentscript/cli is available in Nexus and display info."""
    log("")
    log("Verifying Nexus npm registry availability...", Colors.CYAN)

    nexus_ok, nexus_version = check_nexus_access()

    if nexus_ok:
        log(f"✓ @agentscript/cli@{nexus_version} IS available in Nexus", Colors.GREEN)
        log(f"  Registry: https://nexus-proxy.repo.local.sfdc.net/nexus/content/groups/npm-all/", Colors.GRAY)
        log("")
        log(f"{Colors.GRAY}Note: Using symlinks in node_modules/@agentscript/cli/node_modules/ to fix Node.js path resolution.{Colors.RESET}", Colors.GRAY)
    else:
        log(f"⚠️  Could not verify Nexus availability: {nexus_version}", Colors.YELLOW)
        log(f"  Continuing with local CLI at: {cli_path}", Colors.YELLOW)

    log("")


def compile_agentscript(cli_path: Path, script_path: Path) -> int:
    """Compile the AgentScript file and return exit code."""
    source = script_path.read_text()
    source_lines = source.splitlines()

    log(f"Compiling {script_path.name}...", Colors.CYAN)

    try:
        result = subprocess.run(
            [
                "node",
                str(cli_path),
                "compile",
                "--file", str(script_path.absolute()),
                "--format", "json"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        stdout = result.stdout
        stderr = result.stderr

        # Parse errors and warnings
        errors = []
        warnings = []

        for line in stderr.splitlines():
            # Remove ANSI color codes
            clean_line = re.sub(r'\x1b\[\d+m', '', line)

            if "[ERROR]" in clean_line:
                error_msg = clean_line.replace("[ERROR]", "").strip()
                if error_msg:
                    errors.append(error_msg)
            elif "[WARNING]" in clean_line:
                warning_msg = clean_line.replace("[WARNING]", "").strip()
                if warning_msg:
                    warnings.append(warning_msg)

        # Check for failure
        if result.returncode != 0 or errors:
            log("", Colors.RED)
            error(f"❌ Compilation errors in {script_path.name}:")
            for err in errors:
                error(f"  {err}")
                line_no = extract_line_number(err)
                if line_no:
                    show_source_context(source_lines, line_no)

            if warnings:
                log("", Colors.YELLOW)
                log(f"⚠️  Warnings:", Colors.YELLOW)
                for warning in warnings:
                    log(f"  {warning}", Colors.YELLOW)

            return 1

        # Validate output
        if not stdout.strip():
            log("", Colors.RED)
            error(f"❌ Compilation produced no output")
            return 1

        # Parse JSON
        try:
            compiled_json = json.loads(stdout)
        except json.JSONDecodeError as e:
            log("", Colors.RED)
            error(f"❌ Invalid JSON output: {e}")
            return 1

        log(f"✓ Parsed {script_path.name} ({len(source_lines)} lines)", Colors.GREEN)
        log("", Colors.GREEN)
        log(f"✅ Successfully compiled Agent Script!", Colors.GREEN)
        log("")
        log(f"Agent Details:", Colors.CYAN)

        # Extract details
        global_config = compiled_json.get("global_configuration", {})
        if global_config:
            log(f"  Developer Name: {global_config.get('developer_name', 'N/A')}")
            log(f"  Agent Label: {global_config.get('agent_label', 'N/A')}")
            log(f"  Agent Type: {global_config.get('agent_type', 'N/A')}")
            if global_config.get('description'):
                desc = global_config['description']
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                log(f"  Description: {desc}")

        agent_version = compiled_json.get("agent_version", {})
        if agent_version:
            nodes = agent_version.get("nodes", [])
            log(f"  Topics: {len(nodes)}")

        if warnings:
            log("", Colors.YELLOW)
            log(f"⚠️  Compilation succeeded with {len(warnings)} warning(s):", Colors.YELLOW)
            for warning in warnings:
                log(f"  {warning}", Colors.YELLOW)

        log("")
        log(f"✓ Compilation successful. Ready for deployment.", Colors.GREEN)
        return 0

    except subprocess.TimeoutExpired:
        log("", Colors.RED)
        error(f"❌ Compilation timed out after 120 seconds")
        return 1
    except Exception as e:
        log("", Colors.RED)
        error(f"❌ Compilation exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) < 2:
        error("Usage: compile_agentscript_nexus_ts.py <path-to-agentscript> [--skip-prereq-check]")
        error("")
        error("Options:")
        error("  --skip-prereq-check    Skip prerequisite validation (not recommended)")
        error("")
        error("This compiler uses @agentscript/cli from Nexus npm registry.")
        sys.exit(1)

    skip_prereq = "--skip-prereq-check" in sys.argv

    # Get script path
    script_path = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            script_path = Path(arg)
            break

    if script_path is None:
        error("Error: No AgentScript file path provided")
        sys.exit(1)

    if not script_path.exists():
        error(f"Error: File '{script_path}' not found")
        sys.exit(1)

    # Display header
    log(f"{Colors.BOLD}AgentScript Compiler (TypeScript/Nexus){Colors.RESET}", Colors.CYAN)
    log("Using @agentscript/cli from Nexus npm registry", Colors.GRAY)

    # Run prerequisite checks
    if not skip_prereq:
        if not run_prerequisites_check(verbose=True):
            sys.exit(1)

    # Find CLI path
    cli_ok, cli_version, cli_path = check_cli_installed()
    if not cli_ok or cli_path is None:
        error("Error: @agentscript/cli not found")
        error("")
        error("Install with:")
        error("  cd <project-root>")
        error("  npm install --legacy-peer-deps --ignore-scripts")
        sys.exit(1)

    log(f"CLI: {cli_path}", Colors.GRAY)

    # Verify Nexus availability (informational only)
    if not skip_prereq:
        verify_nexus_availability(cli_path)

    # Compile
    exit_code = compile_agentscript(cli_path, script_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
