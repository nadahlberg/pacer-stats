import click
import pandas as pd
from pacer_stats import utils
from pacer_stats.registry import command_registry


@click.command()
def build_global_index():
    out_path = utils.BASE_DIR / 'data' / 'global_index.csv'
    if out_path.exists():
        out_path.unlink()

    courts = utils.get_court_data()

    for batch in utils.iter_case_paths(batch_size=10000):
        batch_data = []
        for case_path in batch:
            case_json = utils.load_json(case_path)

            # docket entry features
            case_json['first_entry_date'] = None
            case_json['last_entry_date'] = None
            if len(case_json['docket']) > 0:
                case_json['first_entry_date'] = case_json['docket'][0]['date_filed']
                case_json['last_entry_date'] = case_json['docket'][-1]['date_filed']

            case_json['num_entries'] = len(case_json['docket'])

            # party features
            case_json['has_pro_se_party'] = utils.has_pro_se_party(case_json['parties'])
            case_json['num_defendants'] = utils.count_party_type(case_json['parties'], 'defendant')
            case_json['num_plaintiffs'] = utils.count_party_type(case_json['parties'], 'plaintiff')
            case_json['num_parties'] = len(case_json['parties'])

            del case_json['docket']
            del case_json['parties']
            del case_json['is_multi']
            del case_json['case_pacer_id']
            del case_json['download_url']
            del case_json['n_docket_reports']
            batch_data.append(case_json)
        batch_data = pd.DataFrame(batch_data)
        
        # fix dates
        batch_data = utils.process_index(batch_data, fix_dates=True)
        # get nos code from nature suit field
        batch_data['nature_suit_code'] = batch_data['nature_suit'].str.split().str[0].astype(pd.Int64Dtype(), errors='ignore')
        # case is closed if terminating date is not null or case flags contain 'CLOSED'
        batch_data['is_closed'] = batch_data['terminating_date'].notnull() | batch_data['case_flags'].apply(lambda x: 'CLOSED' in x)
        # merge court data
        batch_data = batch_data.merge(courts, how='left', left_on='court', right_on='court')

        utils.save_or_append(batch_data, out_path)
    print(utils.load_global_index())


command_registry.register('build-global-index', build_global_index)

