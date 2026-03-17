"""CLI smoke tests."""

from llvmanim.cli.main import main


def test_main_returns_zero() -> None:
    """CLI main returns success exit code."""
    assert main() == 0
