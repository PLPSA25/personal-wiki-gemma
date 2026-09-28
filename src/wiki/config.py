"""Where things live. Everything is relative to one project folder so the tool runs from any directory."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def default_root() -> Path:
    """The project folder: $WIKI_ROOT if set, otherwise the folder that contains src/."""
    override = os.environ.get("WIKI_ROOT")
    return Path(override) if override else Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def vault_dir(self) -> Path:
        return self.root / "vault"  # the folder opened in Obsidian

    @property
    def raw_dir(self) -> Path:
        return self.vault_dir / "raw"  # original sources, never modified

    @property
    def wiki_dir(self) -> Path:
        return self.vault_dir / "wiki"  # generated notes, in topic folders

    @property
    def plan_path(self) -> Path:
        return self.root / "wiki-plan.toml"  # which notes exist; outside the vault

    @property
    def backup_dir(self) -> Path:
        return self.root / "data" / "backup"  # old versions of overwritten notes

    @property
    def index_path(self) -> Path:
        return self.root / "data" / "index.db"  # machine-generated, outside the vault

    @property
    def prompts_dir(self) -> Path:
        return self.root / "prompts"  # persona.md, wiki-instructions.md, ...

    @property
    def log_dir(self) -> Path:
        return self.root / "data" / "logs"  # saved runs; machine files stay outside the vault
