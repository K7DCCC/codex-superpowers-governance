#!/usr/bin/env python3
"""End-to-end tests for install, verify, idempotency, and rollback."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
SKILL_IDS = (
    MANIFEST["skills"]["explicit_or_confirm_only"]
    + MANIFEST["skills"]["conditional_auto"]
)


def run(script: str, codex_home: Path, skills_dir: Path, *extra: str) -> str:
    command = [
        sys.executable,
        str(SCRIPTS / script),
        "--codex-home",
        str(codex_home),
        "--agents-skills-dir",
        str(skills_dir),
        *extra,
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError("{} failed:\n{}".format(script, result.stdout))
    return result.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="governance-portable-test-") as temp:
        root = Path(temp)
        codex_home = root / ".codex"
        skills_dir = root / ".agents" / "skills"
        codex_home.mkdir(parents=True)
        skills_dir.mkdir(parents=True)

        original_config = (
            'model = "preserve-me"\n\n'
            '[plugins."superpowers@openai-curated"]\n'
            "enabled = true\n\n"
            "[[skills.config]]\n"
            'path = "/old/plugins/cache/superpowers/1.0/skills/old/SKILL.md"\n'
            "enabled = true\n"
        )
        original_agents = "# Existing rules\n\nKeep this line.\n"
        (codex_home / "config.toml").write_text(
            original_config,
            encoding="utf-8",
        )
        (codex_home / "AGENTS.md").write_text(
            original_agents,
            encoding="utf-8",
        )

        source_root = (
            codex_home
            / "plugins"
            / "cache"
            / "market"
            / "superpowers"
            / "6.2.0"
            / "skills"
        )
        for skill_id in SKILL_IDS:
            source = source_root / skill_id
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(
                "# source {}\n".format(skill_id),
                encoding="utf-8",
            )

        old_skill = skills_dir / "systematic-debugging"
        old_skill.mkdir()
        (old_skill / "old.txt").write_text("restore me\n", encoding="utf-8")

        preflight = json.loads(run("preflight.py", codex_home, skills_dir))
        assert preflight["superpowers_source_skill_count"] == 14

        dry_run = json.loads(
            run("install.py", codex_home, skills_dir, "--dry-run")
        )
        assert dry_run["status"] == "dry-run"
        assert (codex_home / "config.toml").read_text() == original_config

        installed = json.loads(run("install.py", codex_home, skills_dir))
        assert installed["status"] == "installed"
        config_after = (codex_home / "config.toml").read_text(encoding="utf-8")
        agents_after = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
        assert 'model = "preserve-me"' in config_after
        assert config_after.count('[plugins."superpowers@openai-curated"]') == 1
        assert "Keep this line." in agents_after

        verified = json.loads(run("verify.py", codex_home, skills_dir))
        assert verified["status"] == "pass"

        installed_again = json.loads(run("install.py", codex_home, skills_dir))
        assert installed_again["status"] == "installed"
        config_again = (codex_home / "config.toml").read_text(encoding="utf-8")
        agents_again = (codex_home / "AGENTS.md").read_text(encoding="utf-8")
        assert config_again.count('[plugins."superpowers@openai-curated"]') == 1
        assert agents_again.count("<!-- >>> codex-superpowers-governance >>>") == 1

        rolled_back_once = json.loads(
            run("rollback.py", codex_home, skills_dir)
        )
        assert rolled_back_once["status"] == "rolled-back"
        verified_after_first_rollback = json.loads(
            run("verify.py", codex_home, skills_dir)
        )
        assert verified_after_first_rollback["status"] == "pass"

        rolled_back_twice = json.loads(
            run("rollback.py", codex_home, skills_dir)
        )
        assert rolled_back_twice["status"] == "rolled-back"
        assert (codex_home / "config.toml").read_text() == original_config
        assert (codex_home / "AGENTS.md").read_text() == original_agents
        assert (skills_dir / "systematic-debugging" / "old.txt").read_text() == "restore me\n"

    print("PASS: install, verify, idempotency, and two-level rollback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
