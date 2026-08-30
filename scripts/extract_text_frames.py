#!/usr/bin/env python3
"""Extract review-required source text-frame candidates from a paginated PDF.

The implementation is kept in ``extract_text_frames_impl`` so regression fixes
can remain narrowly testable while this public import/CLI path stays stable.
"""

from __future__ import annotations

import sys

import extract_text_frames_impl as _impl

# Preserve the historical module API, including private helpers used by the
# regression suite. Do not duplicate extraction logic in this compatibility
# entry point.
globals().update(
    {
        name: getattr(_impl, name)
        for name in dir(_impl)
        if not name.startswith("__")
    }
)


if __name__ == "__main__":
    sys.exit(_impl.main())
