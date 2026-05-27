import click
from atlassian_tools.cfl.commands.auth import auth


@click.group()
def cli():
    """cfl — Confluence CLI."""


cli.add_command(auth)
