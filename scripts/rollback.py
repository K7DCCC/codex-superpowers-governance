#!/usr/bin/env python3
"""Rollback the most recent portable governance installation without deletion."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from _common import (
    SKILL_IDS,
    add_path_arguments,
    print_json,
    resolved,
    utc_stamp,
)


def move_if_exists(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(source), str(destination))
    return True


def restore_file(
    target: Path,
    backup: Path,
    existed_before: bool,
    quarantine: Path,
) -> None:
    if target.exists():
        move_if_exists(target, quarantine / "current-files" / target.name)
    if existed_before:
        if not backup.is_file():
            raise FileNotFoundError("missing backup file: {}".format(backup))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(backup), str(target))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_path_arguments(parser)
    args = parser.parse_args()
    codex_home = resolved(args.codex_home)
    skills_dir = resolved(args.agents_skills_dir)
    state_path = codex_home / "governance" / "install-state.json"
    if not state_path.is_file():
        raise SystemExit("ERROR: install-state.json not found; cannot select backup")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    recorded_codex_home = Path(state["codex_home"]).resolve()
    recorded_skills_dir = Path(state["agents_skills_dir"]).resolve()
    if recorded_codex_home != codex_home or recorded_skills_dir != skills_dir:
        raise SystemExit(
            "ERROR: supplied paths do not match the installation state"
        )

    backup_dir = Path(state["backup_dir"]).resolve()
    if not backup_dir.is_dir():
        raise SystemExit("ERROR: backup directory is missing: " + str(backup_dir))
    quarantine = codex_home / "governance" / "quarantine" / (
        "rollback-" + utc_stamp()
    )
    quarantine.mkdir(parents=True, exist_ok=False)

    preexisting_skills = set(state.get("preexisting_skills", []))
    for skill_id in SKILL_IDS:
        current = skills_dir / skill_id
        move_if_exists(current, quarantine / "installed-skills" / skill_id)
        if skill_id in preexisting_skills:
            backed_up = backup_dir / "skills" / skill_id
            if not backed_up.is_dir():
                raise FileNotFoundError(
                    "missing backed-up skill: {}".format(backed_up)
                )
            skills_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(backed_up), str(current))

    preexisting_files = state.get("preexisting_files", {})
    restore_file(
        codex_home / "config.toml",
        backup_dir / "config.toml",
        bool(preexisting_files.get("config.toml")),
        quarantine,
    )
    restore_file(
        codex_home / "AGENTS.md",
        backup_dir / "AGENTS.md",
        bool(preexisting_files.get("AGENTS.md")),
        quarantine,
    )

    preexisting_governance = state.get("preexisting_governance", {})
    for name, existed_before in preexisting_governance.items():
        restore_file(
            codex_home / "governance" / name,
            backup_dir / "governance" / name,
            bool(existed_before),
            quarantine / "governance",
        )

    move_if_exists(
        state_path,
        quarantine / "install-state.json",
    )
    if state.get("preexisting_state"):
        previous_state = backup_dir / "install-state.json"
        if not previous_state.is_file():
            raise FileNotFoundError(
                "missing previous install state: {}".format(previous_state)
            )
        shutil.copy2(str(previous_state), str(state_path))
    report = {
        "status": "rolled-back",
        "restored_from": str(backup_dir),
        "quarantine": str(quarantine),
        "restart_required": True,
    }
    (quarantine / "rollback-result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print_json(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
