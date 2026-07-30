#!/usr/bin/env python3
"""Shared helpers for the portable Superpowers governance bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


BUNDLE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_BEGIN_MARKER = "# >>> codex-superpowers-governance >>>"
CONFIG_END_MARKER = "# <<< codex-superpowers-governance <<<"
AGENTS_BEGIN_MARKER = "<!-- >>> codex-superpowers-governance >>> -->"
AGENTS_END_MARKER = "<!-- <<< codex-superpowers-governance <<< -->"

SKILL_IDS = (
    "brainstorming",
    "dispatching-parallel-agents",
    "executing-plans",
    "finishing-a-development-branch",
    "receiving-code-review",
    "requesting-code-review",
    "subagent-driven-development",
    "systematic-debugging",
    "test-driven-development",
    "using-git-worktrees",
    "using-superpowers",
    "verification-before-completion",
    "writing-plans",
    "writing-skills",
)

EXPECTED_IMPLICIT = {
    skill_id: skill_id == "verification-before-completion"
    for skill_id in SKILL_IDS
}

TABLE_HEADER_RE = re.compile(r"^\s*(\[\[.*\]\]|\[.*\])\s*(?:#.*)?$")
PLUGIN_HEADER_RE = re.compile(
    r'^\[plugins\."(?P<plugin_id>superpowers@[^"]+)"\]$'
)


def add_path_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
        help="Codex configuration directory (default: $CODEX_HOME or ~/.codex)",
    )
    parser.add_argument(
        "--agents-skills-dir",
        type=Path,
        default=Path(
            os.environ.get(
                "AGENTS_SKILLS_DIR",
                Path.home() / ".agents" / "skills",
            )
        ),
        help="User skill directory (default: ~/.agents/skills)",
    )


def resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".governance-tmp")
    temp.write_text(content, encoding="utf-8")
    os.replace(str(temp), str(path))


def remove_managed_block(text: str, begin_marker: str, end_marker: str) -> str:
    lines = text.splitlines(keepends=True)
    output: List[str] = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == begin_marker:
            inside = True
            continue
        if inside and stripped == end_marker:
            inside = False
            continue
        if not inside:
            output.append(line)
    if inside:
        raise ValueError("managed block starts but has no end marker")
    return "".join(output).rstrip()


def render_agents_fragment(codex_home: Path) -> str:
    template = read_text(BUNDLE_ROOT / "templates" / "AGENTS.fragment.md")
    return template.replace("{{CODEX_HOME}}", codex_home.as_posix()).strip()


def merge_agents(existing: str, codex_home: Path) -> str:
    unmanaged = remove_managed_block(
        existing,
        AGENTS_BEGIN_MARKER,
        AGENTS_END_MARKER,
    )
    fragment = render_agents_fragment(codex_home)
    if unmanaged:
        return unmanaged + "\n\n" + fragment + "\n"
    return fragment + "\n"


def split_toml_blocks(text: str) -> List[Tuple[str, str]]:
    """Split TOML into a preamble plus table blocks without parsing values."""
    blocks: List[Tuple[str, str]] = []
    current_header = ""
    current_lines: List[str] = []
    for line in text.splitlines(keepends=True):
        match = TABLE_HEADER_RE.match(line)
        if match:
            if current_lines:
                blocks.append((current_header, "".join(current_lines)))
            current_header = match.group(1)
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        blocks.append((current_header, "".join(current_lines)))
    return blocks


def discover_superpowers_source_paths(codex_home: Path) -> List[Path]:
    cache = codex_home / "plugins" / "cache"
    if not cache.exists():
        return []
    results: List[Path] = []
    for path in cache.rglob("SKILL.md"):
        parts = path.parts
        try:
            superpowers_index = parts.index("superpowers")
            skills_index = parts.index("skills", superpowers_index + 1)
        except ValueError:
            continue
        if skills_index + 3 == len(parts):
            results.append(path.resolve())
    return sorted(set(results), key=lambda item: item.as_posix())


def _is_source_skill_config(header: str, block: str) -> bool:
    if header != "[[skills.config]]":
        return False
    normalized = block.replace("\\\\", "/")
    return (
        "path" in normalized
        and "/plugins/cache/" in normalized
        and "/superpowers/" in normalized
        and "/skills/" in normalized
        and "SKILL.md" in normalized
    )


def merge_config(
    existing: str,
    source_paths: Sequence[Path],
    fallback_plugin_id: str,
) -> Tuple[str, List[str]]:
    unmanaged = remove_managed_block(
        existing,
        CONFIG_BEGIN_MARKER,
        CONFIG_END_MARKER,
    )
    kept: List[str] = []
    plugin_ids: List[str] = []

    for header, block in split_toml_blocks(unmanaged):
        plugin_match = PLUGIN_HEADER_RE.match(header)
        if plugin_match:
            plugin_ids.append(plugin_match.group("plugin_id"))
            continue
        if _is_source_skill_config(header, block):
            continue
        kept.append(block)

    if fallback_plugin_id not in plugin_ids:
        plugin_ids.append(fallback_plugin_id)
    plugin_ids = sorted(set(plugin_ids))

    managed: List[str] = [CONFIG_BEGIN_MARKER]
    for plugin_id in plugin_ids:
        managed.extend(
            [
                '[plugins.{}]'.format(json.dumps(plugin_id)),
                "enabled = false",
                "",
            ]
        )
    for path in source_paths:
        managed.extend(
            [
                "[[skills.config]]",
                "path = {}".format(json.dumps(path.as_posix())),
                "enabled = false",
                "",
            ]
        )
    managed.append(CONFIG_END_MARKER)

    base = "".join(kept).rstrip()
    rendered = "\n".join(managed).rstrip() + "\n"
    if base:
        return base + "\n\n" + rendered, plugin_ids
    return rendered, plugin_ids


def metadata_implicit_value(path: Path) -> bool:
    text = read_text(path)
    match = re.search(
        r"^\s*allow_implicit_invocation:\s*(true|false)\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError("missing allow_implicit_invocation in {}".format(path))
    return match.group(1) == "true"


def run_codex_version() -> Tuple[int, str]:
    executable = shutil.which("codex")
    if not executable:
        return 127, "codex executable not found on PATH"
    result = subprocess.run(
        [executable, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def print_json(payload: Dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def fail(message: str, code: int = 1) -> "None":
    print("ERROR: " + message, file=sys.stderr)
    raise SystemExit(code)
