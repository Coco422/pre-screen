from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_COMMON_SRC = ROOT / "packages" / "backend-common" / "src"

for path in (ROOT, BACKEND_COMMON_SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
