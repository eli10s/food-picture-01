#!/usr/bin/env python3
"""food-picture-01 entry: copy the repo-held image to the output directory.

Standard library only. Deterministic: no network, no randomness, no
timestamps. The grader runs this in a container where /output exists;
outside that container MAKEFUN_OUTPUT_DIR stands in for /output.
"""

import os
import shutil
from pathlib import Path

SOURCE_NAME = "entry.png"
DEFAULT_OUTPUT_DIR = "/output"


def main() -> None:
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / SOURCE_NAME
    shutil.copyfile(source, destination)


if __name__ == "__main__":
    main()
