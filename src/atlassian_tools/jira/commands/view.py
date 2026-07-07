import os
import tempfile
import webbrowser

import click
from rich.console import Console
from rich.panel import Panel

from atlassian_tools.jira import api
from atlassian_tools.shared import config

console = Console()


def _adf_to_text(node: dict, _indent: int = 0) -> str:
    if not node:
        return ""
    t = node.get("type", "")
    children = node.get("content", [])

    if t == "text":
        return node.get("text", "")
    if t == "hardBreak":
        return "\n"
    if t == "mention":
        return node.get("attrs", {}).get("text", "@?")
    if t == "emoji":
        return node.get("attrs", {}).get("text", "")
    if t in ("inlineCard", "blockCard"):
        return node.get("attrs", {}).get("url", "")
    if t == "rule":
        return "\n---\n\n"
    if t in ("doc", "listItem"):
        return "".join(_adf_to_text(c, _indent) for c in children)
    if t == "paragraph":
        return "".join(_adf_to_text(c, _indent) for c in children) + "\n\n"
    if t == "heading":
        level = node.get("attrs", {}).get("level", 1)
        text = "".join(_adf_to_text(c, _indent) for c in children)
        return "#" * level + " " + text + "\n\n"
    if t == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        text = "".join(_adf_to_text(c, _indent) for c in children)
        return f"```{lang}\n{text}\n```\n\n"
    if t == "blockquote":
        inner = "".join(_adf_to_text(c, _indent) for c in children)
        return "\n".join("> " + line for line in inner.splitlines()) + "\n\n"
    if t == "bulletList":
        out = ""
        for item in children:
            item_text = "".join(_adf_to_text(c, _indent + 1) for c in item.get("content", [])).strip()
            out += "  " * _indent + "- " + item_text + "\n"
        return out + "\n"
    if t == "orderedList":
        out = ""
        for i, item in enumerate(children, 1):
            item_text = "".join(_adf_to_text(c, _indent + 1) for c in item.get("content", [])).strip()
            out += "  " * _indent + f"{i}. " + item_text + "\n"
        return out + "\n"
    if t == "table":
        rows = []
        for row in children:
            cells = [
                "".join(_adf_to_text(c) for c in cell.get("content", [])).strip().replace("\n", " ")
                for cell in row.get("content", [])
            ]
            rows.append(" | ".join(cells))
        return "\n".join(rows) + "\n\n"
    return "".join(_adf_to_text(c, _indent) for c in children)


def _load_creds():
    try:
        creds = config.load_credentials()
    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)
    if not creds.get("atlassian_domain"):
        console.print(
            "\n[red]Error:[/red] No Atlassian domain set. "
            "Run [bold]jira auth login[/bold] and provide your domain."
        )
        raise SystemExit(1)
    return creds


def _fetch_issue(creds: dict, ticket: str) -> dict:
    try:
        return api.get_issue(
            email=creds["email"],
            api_token=creds["jira_token"],
            domain=creds["atlassian_domain"],
            key=ticket.upper(),
        )
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)


def _build_plain(issue: dict) -> str:
    fields = issue.get("fields", {})
    key = issue.get("key", "")
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else ""
    issue_type = fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else ""
    assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
    reporter = fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else ""
    description_adf = fields.get("description")
    description = _adf_to_text(description_adf).strip() if description_adf else "(no description)"

    header = f"{key}: {summary}"
    text = f"{header}\n{'=' * len(header)}\n\n"
    text += f"Type:     {issue_type}\n"
    text += f"Status:   {status}\n"
    text += f"Priority: {priority}\n"
    text += f"Assignee: {assignee}\n"
    text += f"Reporter: {reporter}\n\n"
    text += "Description\n-----------\n"
    text += description + "\n"

    comments = fields.get("comment", {}).get("comments", [])
    if comments:
        text += "\nComments\n--------\n"
        for c in comments:
            author = c.get("author", {}).get("displayName", "?")
            body = _adf_to_text(c.get("body")).strip() if c.get("body") else ""
            text += f"\n{author}:\n{body}\n"

    return text


@click.command("view")
@click.argument("ticket")
@click.option("-a", "--attachments", is_flag=True, help="Download and open all attachments.")
@click.option("-v", "--editor", "open_editor", is_flag=True, help="Open ticket in text editor.")
def view_issue(ticket: str, attachments: bool, open_editor: bool):
    """View a Jira issue."""
    creds = _load_creds()
    issue = _fetch_issue(creds, ticket)
    fields = issue.get("fields", {})

    if attachments:
        _open_attachments(creds, fields, issue.get("key", ticket.upper()))
        return

    plain = _build_plain(issue)

    if open_editor:
        click.edit(plain, require_save=False, extension=".md")
        return

    key = issue.get("key", "")
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "") if fields.get("priority") else ""
    issue_type = fields.get("issuetype", {}).get("name", "") if fields.get("issuetype") else ""
    assignee = fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned"
    reporter = fields.get("reporter", {}).get("displayName", "") if fields.get("reporter") else ""
    description_adf = fields.get("description")
    description = _adf_to_text(description_adf).strip() if description_adf else "[dim](no description)[/dim]"

    console.print()
    console.print(Panel(f"[bold cyan]{key}[/bold cyan]  {summary}", expand=False))
    console.print(f"  [dim]Type:[/dim]     {issue_type}")
    console.print(f"  [dim]Status:[/dim]   {status}")
    console.print(f"  [dim]Priority:[/dim] {priority}")
    console.print(f"  [dim]Assignee:[/dim] {assignee}")
    console.print(f"  [dim]Reporter:[/dim] {reporter}")
    console.print()
    console.rule("Description", align="left")
    console.print(description)

    comments = fields.get("comment", {}).get("comments", [])
    if comments:
        console.print()
        console.rule("Comments", align="left")
        for c in comments:
            author = c.get("author", {}).get("displayName", "?")
            body = _adf_to_text(c.get("body")).strip() if c.get("body") else ""
            console.print(f"\n[bold]{author}[/bold]")
            console.print(body)

    console.print()


def _open_attachments(creds: dict, fields: dict, key: str) -> None:
    att_list = fields.get("attachment", [])
    if not att_list:
        console.print(f"\n[dim]No attachments on {key}.[/dim]\n")
        return

    tmp_dir = tempfile.mkdtemp(prefix=f"jira-{key}-")
    console.print(f"\n[dim]Downloading {len(att_list)} attachment(s)...[/dim]\n")

    for att in att_list:
        filename = att.get("filename", "attachment")
        url = att.get("content")
        try:
            data = api.download_attachment(
                email=creds["email"],
                api_token=creds["jira_token"],
                url=url,
            )
        except RuntimeError as e:
            console.print(f"  [red]✗[/red] {filename}: {e}")
            continue

        path = os.path.join(tmp_dir, filename)
        with open(path, "wb") as f:
            f.write(data)
        console.print(f"  [green]✓[/green] {filename}")
        webbrowser.open(f"file://{path}")

    console.print()
