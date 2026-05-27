"""Shared auth sub-commands (status, logout) used by all three CLIs.

Each tool defines its own `auth` Click group and its own `login` command,
then adds these shared commands to keep status/logout consistent everywhere.
"""

import click
from rich.console import Console

from atlassian_tools.shared import config

console = Console()


@click.command()
def logout():
    """Remove all saved Atlassian credentials."""
    creds_file = config.CREDENTIALS_FILE
    if not creds_file.exists():
        console.print("\n[dim]No credentials found — already logged out.[/dim]\n")
        return
    creds_file.unlink()
    console.print(f"\n[green]✓[/green] Credentials removed from {creds_file}\n")


@click.command()
def status():
    """Show saved Atlassian credentials."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError:
        console.print(
            "\n[dim]Not logged in. Run [bold]<tool> auth login[/bold] first.[/dim]\n"
        )
        raise SystemExit(1)

    def _token_state(key: str) -> str:
        return "[green]✓ configured[/green]" if creds.get(key) else "[dim]not configured[/dim]"

    domain = creds.get("atlassian_domain")
    domain_str = f"{domain}.atlassian.net" if domain else "[dim]not set[/dim]"

    console.print("\n[bold]Atlassian credentials[/bold]")
    console.print(f"  Email:   {creds.get('email', '[dim]not set[/dim]')}")
    console.print(f"  Domain:  {domain_str}  [dim](jira / cfl)[/dim]")
    console.print(f"  bb:      {_token_state('bb_token')}")
    console.print(f"  jira:    {_token_state('jira_token')}")
    console.print(f"  cfl:     {_token_state('cfl_token')}")
    console.print(f"  File:    {config.CREDENTIALS_FILE}\n")
