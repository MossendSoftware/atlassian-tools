import subprocess
import tempfile
import os
import click
from rich.console import Console

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
            api_token=creds["api_token"],
            workspace=ctx.workspace,
            repo_slug=ctx.repo_slug,
            title=title,
            description=description,
            source_branch=ctx.current_branch,
            destination_branch=destination,
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)

    pr_id = pr_data["id"]
    pr_url = pr_data["links"]["html"]["href"]
    console.print(f"\n[green]✓[/green] Created PR [bold]#{pr_id}[/bold]: {title}")
    console.print(f"[link]{pr_url}[/link]\n")
