import click
from atlassian_tools.bb.commands.auth import auth
from atlassian_tools.bb.commands.pr import pr


@click.group()
def cli():
    """bb — Bitbucket CLI."""


cli.add_command(auth)
cli.add_command(pr)
