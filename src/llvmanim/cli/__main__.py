"""Package entrypoint: python -m llvmanim.cli forwards to cli.main."""
from llvmanim.cli.main import main

if __name__ == "__main__":
    raise SystemExit(main())
