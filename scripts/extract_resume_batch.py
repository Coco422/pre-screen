#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages/backend-common/src"))

from services.resume.app.tasks.batch_extract import run_resume_batch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract resume PDFs into Markdown, metadata, and avatars.")
    parser.add_argument("pdfs", nargs="+", type=Path, help="PDF resume paths to process.")
    parser.add_argument("--batch-id", default=None, help="Optional stable batch id.")
    parser.add_argument("--output-root", type=Path, default=Path("tmp/resume-batches"))
    parser.add_argument("--use-ai", action="store_true", help="Call the configured multimodal model.")
    args = parser.parse_args()

    missing = [str(path) for path in args.pdfs if not path.exists()]
    if missing:
        raise SystemExit(f"Missing PDF(s): {', '.join(missing)}")

    result = run_resume_batch(
        pdf_paths=args.pdfs,
        output_root=args.output_root,
        batch_id=args.batch_id,
        use_ai=args.use_ai,
        save_to_repository=False,
    )
    print(result.output_dir)


if __name__ == "__main__":
    main()
