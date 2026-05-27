import click
from rich.console import Console

from atlassian_tools.bb import api
from atlassian_tools.shared import config
from atlassian_tools.shared.commands.auth import status, logout

console = Console()


@click.group()
def auth():
    """Manage Bitbucket credentials."""


@auth.command()
def login():
    """Save a Bitbucket API token to ~/.config/atlassian-tools/credentials.yaml.

    Bitbucket only allows one app per API token, so this token must be
    created with Bitbucket selected as the app.
    """
    console.print("\n[bold]Bitbucket login[/bold]")
    console.print(
        "Create an API token scoped to [bold]Bitbucket[/bold] at:\n"
        "[link]https://id.atlassian.com/manage-profile/security/api-tokens[/link]\n"
        "[dim]Required scopes: Account → Read, Repositories → Read, "
        "Pull requests → Read + Write[/dim]\n"
    )

    email = click.prompt("Email")
    bb_token = click.prompt("Bitbucket API token", hide_input=True)

    console.print("\n[dim]Verifying token...[/dim]")
    try:
        user = api.verify_credentials(email, bb_token)
    except RuntimeError as e:
        console.print(f"\n[red]Login failed:[/red] {e}")
        raise SystemExit(1)

    config.save_credentials(email=email, bb_token=bb_token)
    console.print(
        f"\n[green]✓[/green] Logged in as [bold]{user.get('display_name', email)}[/bold]"
    )
    console.print(f"[dim]Credentials saved to {config.CREDENTIALS_FILE}[/dim]\n")


auth.add_command(status)
auth.add_command(logout)
