import click
from atlassian_tools.jira.commands.auth import auth
from atlassian_tools.jira.commands.issues import list_issues


@click.group()
def cli():
    """jira — Jira CLI."""


cli.add_command(auth)
cli.add_command(list_issues)
