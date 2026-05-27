import click
from atlassian_tools.shared.commands.auth import auth


@click.group()
def cli():
    """jira — Jira CLI."""


cli.add_command(auth)
