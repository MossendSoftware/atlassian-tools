import click
from rich.console import Console

from atlassian_tools.cfl import api
from atlassian_tools.shared import config
from atlassian_tools.shared.commands.auth import status, logout

console = Console()


@click.group()
def auth():
    """Manage Confluence credentials."""


@auth.command()
def login():
    """Save a Confluence API token to ~/.config/atlassian-tools/credentials.yaml.

    Scoped API tokens are product-specific — create a token with Confluence
    selected, or use a Classic API token which works across all products.
    """
    console.print("\n[bold]Confluence login[/bold]")
    console.print(
        "Create an API token scoped to [bold]Confluence[/bold] at:\n"
        "[link]https://id.atlassian.com/manage-profile/security/api-tokens[/link]\n"
        "[dim]Required scopes: View user data → Read, "
        "View Confluence content → Read[/dim]\n"
    )

    email = click.prompt("Email")
    cfl_token = click.prompt("Confluence API token", hide_input=True)
    domain = click.prompt("Atlassian domain (e.g. 'mycompany' for mycompany.atlassian.net)")

    console.print("\n[dim]Verifying token...[/dim]")
    try:
        user = api.verify_credentials(email, cfl_token, domain)
    except RuntimeError as e:
        console.print(f"\n[red]Login failed:[/red] {e}")
        raise SystemExit(1)

    config.save_credentials(email=email, cfl_token=cfl_token, atlassian_domain=domain)
    display = user.get("displayName") or user.get("username", email)
    console.print(f"\n[green]✓[/green] Logged in as [bold]{display}[/bold]")
    console.print(f"[dim]Credentials saved to {config.CREDENTIALS_FILE}[/dim]\n")


auth.add_command(status)
auth.add_command(logout)
