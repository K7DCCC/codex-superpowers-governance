#!/usr/bin/env python3
"""Read-only preflight for the portable governance bundle."""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

from _common import (
    BUNDLE_ROOT,
    SKILL_IDS,
    add_path_arguments,
    discover_superpowers_source_paths,
    metadata_implicit_value,
    print_json,
    resolved,
    run_codex_version,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_path_arguments(parser)
    args = parser.parse_args()
    codex_home = resolved(args.codex_home)
    skills_dir = resolved(args.agents_skills_dir)

    bundle_errors = []
    for skill_id in SKILL_IDS:
        skill_root = BUNDLE_ROOT / "skills" / skill_id
        if not (skill_root / "SKILL.md").is_file():
            bundle_errors.append("missing skills/{}/SKILL.md".format(skill_id))
        try:
            metadata_implicit_value(skill_root / "agents" / "openai.yaml")
        except ValueError as exc:
            bundle_errors.append(str(exc))

    source_paths = discover_superpowers_source_paths(codex_home)
    codex_rc, codex_output = run_codex_version()
    warnings = []
    if not source_paths:
        warnings.append(
            "No cached Superpowers source skills found. Install or refresh the "
            "plugin before installation, or install now and rerun after it is cached."
        )

    payload = {
        "status": "pass" if not bundle_errors else "fail",
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "bundle_root": str(BUNDLE_ROOT),
        "codex_home": str(codex_home),
        "agents_skills_dir": str(skills_dir),
        "codex_command_rc": codex_rc,
        "codex_version_output": codex_output,
        "superpowers_source_skill_count": len(source_paths),
        "superpowers_source_paths": [str(path) for path in source_paths],
        "existing_config": (codex_home / "config.toml").exists(),
        "existing_agents": (codex_home / "AGENTS.md").exists(),
        "bundle_errors": bundle_errors,
        "warnings": warnings,
    }
    print_json(payload)
    return 0 if not bundle_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

