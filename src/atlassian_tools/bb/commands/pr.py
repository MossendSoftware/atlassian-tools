import subprocess
import tempfile
import os
import click
from rich.console import Console
from rich.table import Table

from atlassian_tools.bb import api
from atlassian_tools.shared import config
from atlassian_tools.bb.git_context import get_git_context, branch_name_to_title

console = Console()

DESCRIPTION_TEMPLATE = """\
<!-- Describe your changes. Lines starting with <!-- are stripped. -->

## What

## Why

## Notes
"""


def _open_editor(initial_text: str) -> str:
    editor = os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write(initial_text)
        tmp_path = f.name
    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path) as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


def _strip_comments(text: str) -> str:
    lines = [l for l in text.splitlines() if not l.strip().startswith("<!--")]
    return "\n".join(lines).strip()


@click.group()
def pr():
    """Manage pull requests."""


@pr.command("list")
@click.option("-n", "--limit", default=50, show_default=True, metavar="N", help="Maximum number of results.")
def list_prs(limit: int):
    """List open pull requests for the current repo."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    try:
        ctx = get_git_context()
    except (RuntimeError, ValueError) as e:
        console.print(f"\n[red]Git error:[/red] {e}")
        raise SystemExit(1)

    console.print(f"\n[dim]Fetching open PRs for {ctx.workspace}/{ctx.repo_slug}...[/dim]")
    try:
        prs = api.list_pull_requests(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            max_results=limit,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not prs:
        console.print("\n[dim]No open pull requests.[/dim]\n")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("#", style="bold cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Author", no_wrap=True)
    table.add_column("Branch", no_wrap=True)

    for p in prs:
        pr_id = str(p.get("id", ""))
        title = p.get("title", "")
        author = p.get("author", {}).get("display_name", "")
        source = p.get("source", {}).get("branch", {}).get("name", "")
        destination = p.get("destination", {}).get("branch", {}).get("name", "")
        table.add_row(pr_id, title, author, f"{source} → {destination}")

    console.print()
    console.print(table)
    console.print(f"\n[dim]{len(prs)} open PR(s)[/dim]\n")


@pr.command("inspect")
@click.argument("pr_id", type=int)
def inspect_pr(pr_id: int):
    """Open a PR description in a temporary editor."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    try:
        ctx = get_git_context()
    except (RuntimeError, ValueError) as e:
        console.print(f"\n[red]Git error:[/red] {e}")
        raise SystemExit(1)

    try:
        pr_data = api.get_pull_request(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            pr_id=pr_id,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    title = pr_data.get("title", "")
    author = pr_data.get("author", {}).get("display_name", "")
    source = pr_data.get("source", {}).get("branch", {}).get("name", "")
    destination = pr_data.get("destination", {}).get("branch", {}).get("name", "")
    description = pr_data.get("description", "").strip()
    url = pr_data.get("links", {}).get("html", {}).get("href", "")

    content = f"# {title}\n\n"
    content += f"**Author:** {author}  \n"
    content += f"**Branch:** `{source}` → `{destination}`  \n"
    if url:
        content += f"**URL:** {url}  \n"
    content += "\n---\n\n"
    content += description if description else "_No description._"

    _open_editor(content)


@pr.command("merge")
@click.argument("pr_id", type=int)
@click.option("-m", "--message", default=None, help="Custom merge commit message.")
def merge_pr(pr_id: int, message: str | None):
    """Merge a pull request."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    try:
        ctx = get_git_context()
    except (RuntimeError, ValueError) as e:
        console.print(f"\n[red]Git error:[/red] {e}")
        raise SystemExit(1)

    try:
        pr_data = api.get_pull_request(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            pr_id=pr_id,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    title = pr_data.get("title", f"PR #{pr_id}")
    destination = pr_data.get("destination", {}).get("branch", {}).get("name", "")

    if not click.confirm(f"\nMerge [bold]#{pr_id}[/bold] '{title}' into [bold]{destination}[/bold]?"):
        console.print("[dim]Aborted.[/dim]\n")
        raise SystemExit(0)

    source = pr_data.get("source", {}).get("branch", {}).get("name", "")
    delete_branch = click.confirm(f"Delete source branch [bold]{source}[/bold] after merge?", default=False)

    try:
        api.merge_pull_request(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            pr_id=pr_id,
            message=message,
            close_source_branch=delete_branch,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    branch_note = f" and deleted [bold]{source}[/bold]" if delete_branch else ""
    console.print(f"\n[green]✓[/green] Merged PR [bold]#{pr_id}[/bold] into [bold]{destination}[/bold]{branch_note}\n")


@pr.command("approve")
@click.argument("pr_id", type=int)
def approve_pr(pr_id: int):
    """Approve a pull request."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    try:
        ctx = get_git_context()
    except (RuntimeError, ValueError) as e:
        console.print(f"\n[red]Git error:[/red] {e}")
        raise SystemExit(1)

    try:
        api.approve_pull_request(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            pr_id=pr_id,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    console.print(f"\n[green]✓[/green] Approved PR [bold]#{pr_id}[/bold]\n")


@pr.command()
def create():
    """Create a pull request from the current branch."""
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    try:
        ctx = get_git_context()
    except (RuntimeError, ValueError) as e:
        console.print(f"\n[red]Git error:[/red] {e}")
        raise SystemExit(1)

    console.print(f"\n[dim]Repository:[/dim] {ctx.workspace}/{ctx.repo_slug}")
    console.print(f"[dim]Source branch:[/dim] {ctx.current_branch}\n")

    title = click.prompt("Title", default=branch_name_to_title(ctx.current_branch))
    destination = click.prompt("Destination branch", default=ctx.default_branch)
    delete_branch = click.confirm("Delete source branch after merge?", default=False)

    console.print("\n[dim]Opening editor for description...[/dim]")
    raw_description = _open_editor(DESCRIPTION_TEMPLATE)
    description = _strip_comments(raw_description)

    if not description:
        if not click.confirm("\nDescription is empty. Create PR anyway?"):
            console.print("[dim]Aborted.[/dim]\n")
            raise SystemExit(0)

    console.print("\n[dim]Creating pull request...[/dim]")
    try:
        pr_data = api.create_pull_request(
            email=creds["email"],
            api_token=creds["bb_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            title=title,
            description=description,
            source_branch=ctx.current_branch,
            destination_branch=destination,
            close_source_branch=delete_branch,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    pr_id = pr_data["id"]
    pr_url = pr_data["links"]["html"]["href"]
    console.print(f"\n[green]✓[/green] Created PR [bold]#{pr_id}[/bold]: {title}")
    console.print(f"[link]{pr_url}[/link]\n")
