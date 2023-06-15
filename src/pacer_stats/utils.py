from dotenv import load_dotenv
import importlib
import os
from pathlib import Path
import pandas as pd
import pkgutil
import simplejson as json
import sys
import scales_nlp
from tqdm import tqdm
from toolz import partition_all
from pacer_stats.registry import project_registry


tqdm.pandas()
load_dotenv()


PACER_DIR = Path(os.getenv('PACER_DIR', None))
BASE_DIR = Path(__file__).parents[2]


def load_local_projects():
    for project_dir in (BASE_DIR / 'projects').iterdir():
        if project_dir.is_dir():
            sys.path.insert(0, str(project_dir))
            config_path = project_dir / "config.py"
            if config_path.exists():
                module_name = f"{project_dir.name}_config"
                spec = importlib.util.spec_from_file_location(module_name, config_path)
                config_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = config_module
                spec.loader.exec_module(config_module)
            sys.path.pop(0)


def load_project(name):
    return project_registry.get(name)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def iter_case_paths(batch_size=None, verbose=True):
    paths = list(PACER_DIR.glob('*/json/*/*.json'))
    if batch_size is not None:
        return tqdm(list(partition_all(batch_size, paths)), disable=not verbose)
    return tqdm(paths, disable=not verbose)


def iter_judge_batches(batch_size=10000):
    judge_index = pd.read_csv(BASE_DIR / 'data' / 'judge_index.csv')
    judge_index = judge_index[['SJID', 'NID']]
    batches = pd.read_csv(
        BASE_DIR / 'data' / 'judge_entities.csv',
        chunksize=batch_size,
        low_memory=False,
    )
    for batch in batches:
        batch = batch.merge(judge_index, on='SJID', how='left')
        batch.columns = batch.columns.str.lower()
        batch = batch[['ucid', 'judge_label', '_entity_extraction_method', 'docket_source', 'sjid', 'nid']]
        batch = batch.rename(columns={'nid': 'fjc_nid'})
        yield batch


def process_index(data, fix_dates=False):
    to_datetime = pd.to_datetime
    if fix_dates:
        to_datetime = lambda x: pd.to_datetime(x, format='mixed', errors='coerce')

    data['filing_date'] = to_datetime(data['filing_date']).dt.date
    data['terminating_date'] = to_datetime(data['terminating_date']).dt.date
    data['first_entry_date'] = to_datetime(data['first_entry_date']).dt.date
    data['last_entry_date'] = to_datetime(data['last_entry_date']).dt.date
    data['download_timestamp'] = to_datetime(data['download_timestamp'])
    return data


def load_global_index():
    data = pd.read_csv(BASE_DIR / 'data' / 'global_index.csv')
    return process_index(data)


def load_fjc_data():
    data = pd.read_csv(BASE_DIR / 'data' / 'fjc_judges.csv')
    data.columns = ['fjc_' + x.lower().replace(' ', '_') for x in data.columns]
    return data


def get_fjc_position(row):
    if row['fjc_nid'] is None or row['judge_label'] not in ['Nondescript Judge', 'Article III Judge', 'District Judge']:
        return pd.Series({'ucid': row['ucid']})
    latest_allowed = row['last_entry_date'] if row['last_entry_date'] is not None else pd.to_datetime('today').dt.date

    position_cols = [
        'fjc_court_type',
        'fjc_court_name',
        'fjc_party_of_appointing_president',
        'fjc_commission_date',
    ]
    selected_position = None
    for position in reversed(range(1,6)):
        court_type = row[f'fjc_court_type_({position})']
        if court_type == "U.S. District Court":
            commission_date = pd.to_datetime(row[f'fjc_commission_date_({position})'], errors='coerce')
            if not pd.isnull(commission_date) and not pd.isnull(latest_allowed):
                if commission_date.date() <= latest_allowed:
                    selected_position = position
                    break

    other_cols = [
        'fjc_nid',
        'fjc_first_name',
        'fjc_middle_name',
        'fjc_last_name',
        'fjc_suffix',
        'fjc_birth_year',
        'fjc_gender',
        'fjc_race_or_ethnicity',
    ]

    data = {'ucid': row['ucid']}
    if selected_position is not None:
        for col in position_cols:
            data[col] = row[f'{col}_({selected_position})']
            data['fjc_position_used'] = selected_position
        for col in other_cols:
            data[col] = row[col]
        return pd.Series(data)
    return pd.Series({'ucid': row['ucid']})


def get_fjc_position_data(data):
    data = data.merge(load_fjc_data(), on='fjc_nid', how='left')
    data = data.progress_apply(get_fjc_position, axis=1)
    data = data.rename(columns={'fjc_party_of_appointing_president': 'fjc_party_of_appointing_pres'})
    return data

def save_or_append(data, path):
    if path.exists():
        data.to_csv(path, mode='a', header=False, index=False)
    else:
        data.to_csv(path, index=False)


def has_pro_se_party(parties):
    for party in parties:
        if party['name'] is not None:
            name = party['name'].lower()
            for counsel in party['counsel']:
                if counsel['name'] is not None and counsel['name'].lower() == name:
                    return True
    return False


def count_party_type(parties, party_type):
    return sum(party['party_type'] == party_type for party in parties)


def get_court_data():
    pending_cases = pd.read_csv(BASE_DIR / 'data' / 'cases_pending.csv', skiprows=4)
    pending_cases = pending_cases[['abbreviation', 'civil', 'criminal']]
    pending_cases.columns = ['court', 'pending_cases_civil', 'pending_cases_criminal']
    pending_cases['court'] = pending_cases['court'].str.strip()

    courts = scales_nlp.courts()
    courts = courts[['abbreviation', 'name', 'circuit', 'cardinal']]
    courts.columns = ['court', 'court_name', 'circuit', 'district']
    courts = courts.merge(pending_cases, on='court', how='left')
    return courts


