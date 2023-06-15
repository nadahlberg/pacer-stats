import click
from pacer_stats import utils
from pacer_stats.registry import command_registry


@click.command()
@click.argument('project-name')
@click.option('--reset/--no-reset', default=False)
def build(project_name, reset):
    project = utils.load_project(project_name)
    if reset:
        if project.case_index_path.exists():
            project.case_index_path.unlink()
    if not project.case_index_path.exists():
        project.build_case_index()
    if not project.judge_data_path.exists():
        project.init_judge_data()
    if not project.processed_judge_data_path.exists():
        project.process_judge_data()


command_registry.register('build', build)

