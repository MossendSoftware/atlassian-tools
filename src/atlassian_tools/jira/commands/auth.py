import click
from rich.console import Console

from atlassian_tools.jira import api
from atlassian_tools.shared import config
from atlassian_tools.shared.commands.auth import status, logout

console = Console()


@click.group()
def auth():
    """Manage Jira credentials."""


@auth.command()
def login():
    """Save a Jira API token to ~/.config/atlassian-tools/credentials.yaml.

    Bitbucket only allows one app per API token, so this token must be
    created with Jira selected as the app — separate from your bb token.
    """
    console.print("\n[bold]Jira login[/bold]")
    console.print(
        "Create an API token scoped to [bold]Jira[/bold] at:\n"
        "[link]https://id.atlassian.com/manage-profile/security/api-tokens[/link]\n"
        "[dim]Required scopes: View user data → Read, "
        "View Jira issue data → Read[/dim]\n"
    )

    email = click.prompt("Email")
    jira_token = click.prompt("Jira API token", hide_input=True)
    domain = click.prompt(
        "Atlassian domain",
        help="Your site name — e.g. 'mycompany' for mycompany.atlassian.net",
    )

    console.print("\n[dim]Verifying token...[/dim]")
    try:
        user = api.verify_credentials(email, jira_token, domain)
    except RuntimeError as e:
        console.print(f"\n[red]Login failed:[/red] {e}")
        raise SystemExit(1)

    config.save_credentials(email=email, jira_token=jira_token, atlassian_domain=domain)
    display = user.get("displayName") or user.get("emailAddress", email)
    console.print(f"\n[green]✓[/green] Logged in as [bold]{display}[/bold]")
    console.print(f"[dim]Credentials saved to {config.CREDENTIALS_FILE}[/dim]\n")


auth.add_command(status)
auth.add_command(logout)
