# CI/CD enhancement script
# Run after tests to validate deployment readiness

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n[CHECK] {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"    ✓ {description}")
            return True
        else:
            print(f"    ✗ {description}: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ✗ {description}: timeout")
        return False
    except Exception as e:
        print(f"    ✗ {description}: {e}")
        return False


def main():
    """Run deployment readiness checks."""
    print("="*60)
    print("DEPLOYMENT READINESS CHECK")
    print("="*60)

    checks = [
        ("python -m pytest tests/ -v --tb=short", "Running test suite"),
        ("python -m flake8 src/ --max-line-length=127 --ignore=E501,W503", "Linting code"),
        ("python -m black --check src/ pipeline/ 2>/dev/null || echo 'black not installed'"),
        ("docker --version", "Docker available"),
        ("docker-compose --version", "Docker Compose available"),
    ]

    results = []
    for cmd, desc in checks:
        if cmd.startswith("python -m black"):
            # Skip black if not installed
            try:
                subprocess.run(["python", "-m", "black", "--version"],
                             capture_output=True, timeout=10)
                results.append(run_command("python -m black --check src/ pipeline/", "Formatting check"))
            except:
                print(f"\n[SKIP] Formatting check (black not installed)")
                results.append(True)  # Don't fail if black not available
        else:
            results.append(run_command(cmd, desc))

    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    print(f"Checks passed: {passed}/{total}")

    if all(results):
        print("✓ Deployment ready!")
        return 0
    else:
        print("⚠ Some checks failed. Review above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
