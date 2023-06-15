import click
from pacer_stats import utils
from pacer_stats.registry import command_registry


@click.command()
@click.argument('project-name')
def test(project_name):
    project = utils.load_project(project_name)
    print(project.case_index)
    nos_counts = project.case_index['nature_suit_code'].value_counts()
    for nos_code, count in nos_counts.items():
        print(f'{nos_code}: {count}')


command_registry.register('test', test)