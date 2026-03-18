#!/usr/bin/env bash
set -e
echo "=========================================="
echo "LLVManim Quality Check"
echo "=========================================="
echo ""

echo "[1/4] Running Ruff..."
uv run ruff check src tests
echo "OK Ruff passed"
echo ""

echo "[2/4] Running Pyright..."
uv run pyright
echo "OK Pyright passed"
echo ""

echo "[3/4] Running Import Linter..."
uv run lint-imports
echo "OK Import Linter passed"
echo ""

echo "[4/4] Running pytest..."
uv run pytest -q --cov=llvmanim --cov-report=term-missing
echo "OK Tests passed"
echo ""

echo "=========================================="
echo "OK All quality checks passed"
echo "=========================================="
