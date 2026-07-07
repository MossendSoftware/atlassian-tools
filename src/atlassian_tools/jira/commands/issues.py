import click
from rich.console import Console
from rich.table import Table

from atlassian_tools.jira import api
from atlassian_tools.shared import config

console = Console()


@click.command("list")
@click.option("-a", "--assigned", is_flag=True, default=False, help="List tickets assigned to you.")
@click.option("-n", "--limit", default=50, show_default=True, metavar="N", help="Maximum number of results.")
@click.option("-s", "--status", default=None, metavar="STATUSES", help="Comma-separated status filter (e.g. 'In Progress, Done').")
def list_issues(assigned: bool, limit: int, status: str | None):
    """List Jira issues."""
    if not assigned:
        console.print("\n[dim]Tip: use [bold]-a / --assigned[/bold] to list tickets assigned to you.[/dim]\n")
        raise SystemExit(0)

    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    domain = creds.get("atlassian_domain")
    if not domain:
        console.print(
            "\n[red]Error:[/red] No Atlassian domain set. "
            "Run [bold]jira auth login[/bold] and provide your domain."
        )
        raise SystemExit(1)

    statuses = [s.strip() for s in status.split(",")] if status else None

    console.print("\n[dim]Fetching assigned issues...[/dim]")
    try:
        issues = api.list_assigned_issues(
            email=creds["email"],
            api_token=creds["jira_token"],
            domain=domain,
            max_results=limit,
            statuses=statuses,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not issues:
        console.print("\n[dim]No issues assigned to you.[/dim]\n")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Priority", no_wrap=True)
    table.add_column("Summary")

    for issue in issues:
        fields = issue.get("fields", {})
        key = issue.get("key", "")
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else ""
        issue_type = fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else ""
        table.add_row(key, issue_type, status, priority, summary)

    console.print()
    console.print(table)
    console.print(f"\n[dim]{len(issues)} issue(s) assigned to you[/dim]\n")
