"""Shared credential storage for all atlassian-tools CLIs.

Credentials are stored at ~/.config/atlassian-tools/credentials.yaml (mode 600).

Schema
------
email: str                  # Atlassian account email (shared across all tools)
atlassian_domain: str       # e.g. "mycompany" for mycompany.atlassian.net
                            #   required for jira / cfl, not used by bb
bb_token: str               # API token scoped to Bitbucket only
jira_token: str             # API token scoped to Jira only
cfl_token: str              # API token scoped to Confluence only

Each token is created separately at id.atlassian.com — Bitbucket only allows
one app per token, so bb_token, jira_token, and cfl_token must be distinct.
"""

from pathlib import Path
import yaml

CONFIG_DIR = Path.home() / ".config" / "atlassian-tools"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.yaml"


def load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "No credentials found. Run [bold]<tool> auth login[/bold] first."
        )
    with CREDENTIALS_FILE.open() as f:
        return yaml.safe_load(f) or {}


def save_credentials(**fields: str | None) -> None:
    """Merge *fields* into the stored credentials file."""
    existing: dict = {}
    if CREDENTIALS_FILE.exists():
        with CREDENTIALS_FILE.open() as f:
            existing = yaml.safe_load(f) or {}
    existing.update({k: v for k, v in fields.items() if v is not None})
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(yaml.dump(existing))
    CREDENTIALS_FILE.chmod(0o600)
