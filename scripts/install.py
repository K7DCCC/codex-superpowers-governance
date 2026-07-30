#!/usr/bin/env python3
"""Install the portable Superpowers governance bundle safely."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from _common import (
    BUNDLE_ROOT,
    SKILL_IDS,
    add_path_arguments,
    atomic_write_text,
    discover_superpowers_source_paths,
    merge_agents,
    merge_config,
    print_json,
    read_text,
    resolved,
    tree_hash,
    utc_stamp,
)


GOVERNANCE_FILES = (
    "level1-router.md",
    "superpowers-governance.md",
    "governed-skill-ids.txt",
    "manifests/baseline-direct.md",
    "manifests/browser-control-in-app-browser.md",
    "manifests/github-github.md",
    "manifests/grist-table-reader.md",
    "manifests/product-design-index.md",
    "manifests/superpowers-using-superpowers.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_path_arguments(parser)
    parser.add_argument(
        "--plugin-id",
        default="superpowers@openai-curated",
        help="Superpowers plugin identifier to disable",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show resolved changes without writing",
    )
    args = parser.parse_args()

    codex_home = resolved(args.codex_home)
    skills_dir = resolved(args.agents_skills_dir)
    config_path = codex_home / "config.toml"
    agents_path = codex_home / "AGENTS.md"
    governance_dir = codex_home / "governance"
    state_path = governance_dir / "install-state.json"
    source_paths = discover_superpowers_source_paths(codex_home)
    merged_config, plugin_ids = merge_config(
        read_text(config_path),
        source_paths,
        args.plugin_id,
    )
    merged_agents = merge_agents(read_text(agents_path), codex_home)

    preview = {
        "status": "dry-run" if args.dry_run else "installing",
        "codex_home": str(codex_home),
        "agents_skills_dir": str(skills_dir),
        "source_skill_count_disabled": len(source_paths),
        "plugin_ids_disabled": plugin_ids,
        "user_skill_count_installed": len(SKILL_IDS),
    }
    if args.dry_run:
        print_json(preview)
        return 0

    stamp = utc_stamp()
    backup_dir = governance_dir / "backups" / (
        "portable-superpowers-governance-" + stamp
    )
    backup_dir.mkdir(parents=True, exist_ok=False)

    preexisting_files = {}
    for path in (config_path, agents_path):
        preexisting_files[path.name] = path.exists()
        if path.exists():
            shutil.copy2(str(path), str(backup_dir / path.name))

    preexisting_state = state_path.exists()
    if preexisting_state:
        shutil.copy2(str(state_path), str(backup_dir / "install-state.json"))

    governance_backup = backup_dir / "governance"
    preexisting_governance = {}
    for name in GOVERNANCE_FILES:
        source = governance_dir / name
        preexisting_governance[name] = source.exists()
        if source.exists():
            destination = governance_backup / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))

    preexisting_skills = []
    skills_backup = backup_dir / "skills"
    for skill_id in SKILL_IDS:
        destination = skills_dir / skill_id
        if destination.exists():
            preexisting_skills.append(skill_id)
            skills_backup.mkdir(parents=True, exist_ok=True)
            os.replace(str(destination), str(skills_backup / skill_id))

    try:
        governance_dir.mkdir(parents=True, exist_ok=True)
        skills_dir.mkdir(parents=True, exist_ok=True)

        for name in GOVERNANCE_FILES:
            destination = governance_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                str(BUNDLE_ROOT / "governance" / name),
                str(destination),
            )

        for skill_id in SKILL_IDS:
            shutil.copytree(
                str(BUNDLE_ROOT / "skills" / skill_id),
                str(skills_dir / skill_id),
            )

        atomic_write_text(agents_path, merged_agents)
        atomic_write_text(config_path, merged_config)

        state = {
            "installed_at": stamp,
            "bundle_version": "1.0.0",
            "backup_dir": str(backup_dir),
            "codex_home": str(codex_home),
            "agents_skills_dir": str(skills_dir),
            "preexisting_files": preexisting_files,
            "preexisting_state": preexisting_state,
            "preexisting_governance": preexisting_governance,
            "preexisting_skills": preexisting_skills,
            "plugin_ids_disabled": plugin_ids,
            "source_paths_disabled": [str(path) for path in source_paths],
            "installed_skill_hashes": {
                skill_id: tree_hash(skills_dir / skill_id)
                for skill_id in SKILL_IDS
            },
        }
        atomic_write_text(
            state_path,
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    except Exception:
        print(
            "Installation stopped. Backup is available at {}".format(backup_dir)
        )
        raise

    preview.update(
        {
            "status": "installed",
            "backup_dir": str(backup_dir),
            "restart_required": True,
            "next": "Restart Codex, create a new task, then run scripts/verify.py",
        }
    )
    print_json(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
