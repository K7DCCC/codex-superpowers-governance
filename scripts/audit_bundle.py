#!/usr/bin/env python3
"""Fail if the repository contains machine-specific or secret-like material."""

from __future__ import annotations

import re
from pathlib import Path

from _common import BUNDLE_ROOT, print_json


FORBIDDEN_NAMES = {
    "auth.json",
    "state.db",
    "state.sqlite",
    ".env",
    ".env.local",
}

TEXT_PATTERNS = {
    "source-machine-user-path": re.compile(r"/Users/mac001(?:/|$)"),
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-token": re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    "aws-access-key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "serialized-access-token": re.compile(
        r'["\']access_token["\']\s*:\s*["\'][^"\']+["\']',
        flags=re.IGNORECASE,
    ),
}


def main() -> int:
    findings = []
    for path in sorted(BUNDLE_ROOT.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_symlink():
            target = path.resolve()
            try:
                target.relative_to(BUNDLE_ROOT)
            except ValueError:
                findings.append(
                    {
                        "type": "escaping-symlink",
                        "path": str(path.relative_to(BUNDLE_ROOT)),
                        "target": str(target),
                    }
                )
            continue
        if not path.is_file():
            continue
        if path.name in FORBIDDEN_NAMES:
            findings.append(
                {
                    "type": "forbidden-filename",
                    "path": str(path.relative_to(BUNDLE_ROOT)),
                }
            )
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in TEXT_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "type": label,
                        "path": str(path.relative_to(BUNDLE_ROOT)),
                        "line": line,
                    }
                )

    payload = {
        "status": "pass" if not findings else "fail",
        "files_scanned": sum(
            1
            for path in BUNDLE_ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts
        ),
        "findings": findings,
    }
    print_json(payload)
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

