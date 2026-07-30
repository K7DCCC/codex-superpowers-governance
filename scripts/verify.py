#!/usr/bin/env python3
"""Verify a portable Superpowers governance installation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import (
    AGENTS_BEGIN_MARKER,
    AGENTS_END_MARKER,
    BUNDLE_ROOT,
    CONFIG_BEGIN_MARKER,
    CONFIG_END_MARKER,
    EXPECTED_IMPLICIT,
    SKILL_IDS,
    add_path_arguments,
    discover_superpowers_source_paths,
    metadata_implicit_value,
    print_json,
    read_text,
    resolved,
    run_codex_version,
    split_toml_blocks,
    tree_hash,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_path_arguments(parser)
    args = parser.parse_args()
    codex_home = resolved(args.codex_home)
    skills_dir = resolved(args.agents_skills_dir)

    errors = []
    checks = {}
    governance_dir = codex_home / "governance"
    agents_text = read_text(codex_home / "AGENTS.md")
    config_text = read_text(codex_home / "config.toml")

    checks["agents_managed_block"] = (
        AGENTS_BEGIN_MARKER in agents_text
        and AGENTS_END_MARKER in agents_text
    )
    if not checks["agents_managed_block"]:
        errors.append("AGENTS.md managed block is missing")
    if str(codex_home) not in agents_text:
        errors.append("AGENTS.md does not point to the resolved CODEX_HOME")

    checks["config_managed_block"] = (
        CONFIG_BEGIN_MARKER in config_text
        and CONFIG_END_MARKER in config_text
    )
    if not checks["config_managed_block"]:
        errors.append("config.toml managed block is missing")

    plugin_disabled = False
    disabled_source_paths = set()
    for header, block in split_toml_blocks(config_text):
        if header.startswith('[plugins."superpowers@') and "enabled = false" in block:
            plugin_disabled = True
        if header == "[[skills.config]]" and "enabled = false" in block:
            for line in block.splitlines():
                if line.strip().startswith("path = "):
                    try:
                        disabled_source_paths.add(json.loads(line.split("=", 1)[1].strip()))
                    except json.JSONDecodeError:
                        pass
    checks["plugin_disabled"] = plugin_disabled
    if not plugin_disabled:
        errors.append("no disabled Superpowers plugin table found")

    discovered = discover_superpowers_source_paths(codex_home)
    missing_disabled = [
        str(path)
        for path in discovered
        if path.as_posix() not in disabled_source_paths
    ]
    checks["source_skill_paths"] = {
        "discovered": len(discovered),
        "disabled": len(discovered) - len(missing_disabled),
    }
    if missing_disabled:
        errors.append(
            "cached source paths are not disabled: {}".format(
                ", ".join(missing_disabled)
            )
        )

    skill_results = {}
    for skill_id in SKILL_IDS:
        installed = skills_dir / skill_id
        bundled = BUNDLE_ROOT / "skills" / skill_id
        result = {"present": installed.is_dir()}
        if not installed.is_dir():
            errors.append("missing installed skill: " + skill_id)
            skill_results[skill_id] = result
            continue
        try:
            implicit = metadata_implicit_value(
                installed / "agents" / "openai.yaml"
            )
            result["allow_implicit_invocation"] = implicit
            if implicit != EXPECTED_IMPLICIT[skill_id]:
                errors.append("wrong implicit policy: " + skill_id)
        except ValueError as exc:
            errors.append(str(exc))
        result["matches_bundle"] = tree_hash(installed) == tree_hash(bundled)
        if not result["matches_bundle"]:
            errors.append("installed skill differs from bundle: " + skill_id)
        skill_results[skill_id] = result
    checks["skills"] = skill_results

    for name in (
        "level1-router.md",
        "superpowers-governance.md",
        "governed-skill-ids.txt",
        "manifests/baseline-direct.md",
        "manifests/superpowers-using-superpowers.md",
        "install-state.json",
    ):
        if not (governance_dir / name).is_file():
            errors.append("missing governance file: " + name)

    codex_rc, codex_output = run_codex_version()
    checks["codex_config_load"] = {
        "return_code": codex_rc,
        "output": codex_output,
    }
    if codex_rc != 0:
        errors.append("Codex could not load its configuration")

    payload = {
        "status": "pass" if not errors else "fail",
        "codex_home": str(codex_home),
        "agents_skills_dir": str(skills_dir),
        "checks": checks,
        "errors": errors,
        "restart_and_new_task_required_for_behavior_check": True,
    }
    print_json(payload)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
