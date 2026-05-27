"""Shared Atlassian authentication command.

All three CLIs (bb, jira, cfl) expose this same `auth` group so that
`bb auth login`, `jira auth login`, and `cfl auth login` are all identical —
one credential store, one login flow.

Credentials are written to ~/.config/atlassian-tools/credentials.yaml (mode 600):

    email: user@example.com
    api_token: xxxx
    atlassian_domain: mycompany   # e.g. for mycompany.atlassian.net (jira / cfl)

Verification uses Bitbucket if the domain is omitted, or Jira if a domain is
provided — whichever is available confirms the token is valid.
"""

import click
from rich.console import Console

from atlassian_tools.shared import config

console = Console()


def _verify_bitbucket(email: str, api_token: str) -> str:
    from atlassian_tools.bb.api import verify_credentials
    user = verify_credentials(email, api_token)
    return user.get("display_name", email)


def _verify_jira(email: str, api_token: str, domain: str) -> str:
    from atlassian_tools.jira.api import verify_credentials
    user = verify_credentials(email, api_token, domain)
    return user.get("displayName") or user.get("emailAddress", email)


@click.group()
def auth():
    """Manage Atlassian credentials (shared across bb, jira, and cfl)."""


@auth.command()
def login():
    """Authenticate with Atlassian and save credentials.

    Credentials are stored at ~/.config/atlassian-tools/credentials.yaml
    and are used by all atlassian-tools CLIs (bb, jira, cfl).
    """
    console.print("\n[bold]Atlassian login[/bold]")
    console.print(
        "Create an API token at: "
        "[link]https://id.atlassian.com/manage-profile/security/api-tokens[/link]\n"
        "[dim]Tip: create one token scoped to all products you use.[/dim]\n"
    )

    email = click.prompt("Email")
    api_token = click.prompt("API token", hide_input=True)
    domain = click.prompt(
        "Atlassian domain (optional — needed for jira/cfl)",
        default="",
        show_default=False,
    ).strip() or None

    console.print("\n[dim]Verifying token...[/dim]")
    display_name: str | None = None
    error: str | None = None

    if domain:
        try:
            display_name = _verify_jira(email, api_token, domain)
        except RuntimeError as e:
            error = str(e)
    else:
        try:
            display_name = _verify_bitbucket(email, api_token)
        except RuntimeError as e:
            error = str(e)

    if error:
        console.print(f"\n[red]Login failed:[/red] {error}")
        raise SystemExit(1)

    config.save_credentials(email=email, api_token=api_token, atlassian_domain=domain)
    console.print(
        f"\n[green]✓[/green] Logged in as [bold]{display_name or email}[/bold]"
    )
    console.print(f"[dim]Credentials saved to {config.CREDENTIALS_FILE}[/dim]\n")


@auth.command()
def logout():
    """Remove saved Atlassian credentials."""
    creds_file = config.CREDENTIALS_FILE
    if not creds_file.exists():
        console.print("\n[dim]No credentials found — already logged out.[/dim]\n")
        return
    creds_file.unlink()
    console.print(f"\n[green]✓[/green] Credentials removed from {creds_file}\n")


@auth.command()
def status():
    """Show the currently saved Atlassian credentials."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError:
        console.print("\n[dim]Not logged in. Run [bold]<tool> auth login[/bold] first.[/dim]\n")
        raise SystemExit(1)

    console.print("\n[bold]Atlassian credentials[/bold]")
    console.print(f"  Email:   {creds.get('email', '[dim]not set[/dim]')}")
    domain = creds.get("atlassian_domain")
    if domain:
        console.print(f"  Domain:  {domain}.atlassian.net")
    else:
        console.print("  Domain:  [dim]not set (jira/cfl unavailable)[/dim]")
    console.print(f"  File:    {config.CREDENTIALS_FILE}\n")
