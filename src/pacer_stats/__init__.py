import click
from pacer_stats import utils
from pacer_stats.registry import command_registry, project_registry
from pacer_stats import commands
from pacer_stats.project import Project, Scope


utils.load_local_projects()


@click.group()
def cli():
    pass


for name, command in command_registry._registry.items():
    cli.add_command(command, name)

