"""CLI entrypoint for LLVManim."""
from pathlib import Path


def main() -> int:
    """Main function for the CLI."""
    root = Path(__file__).resolve().parents[3]
    print(f"LLVManim workspace: {root}")
    print(f"Current working directory: {Path.cwd()}")
    return 0
