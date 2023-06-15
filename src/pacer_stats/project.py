import pandas as pd
from pacer_stats import project_registry
from pacer_stats import utils


class Scope:
    def __init__(self, 
        case_type=None, 
        min_date=None, 
        max_date=None, 
        closed_only=False,
        exclude_courts=[], 
        exclude_nos_codes=[],
    ):
        self.case_type = case_type
        self.min_date = min_date if min_date is None else pd.to_datetime(min_date).date()
        self.max_date = max_date if max_date is None else pd.to_datetime(max_date).date()
        self.closed_only = closed_only
        self.exclude_courts = exclude_courts
        self.exclude_nos_codes = exclude_nos_codes

    def index_filter(self, data):
        index_filter = pd.Series(True, index=data.index)
        if self.case_type:
            index_filter &= data['case_type'] == self.case_type
        if self.min_date:
            index_filter &= data['filing_date'] >= self.min_date
        if self.max_date:
            index_filter &= data['filing_date'] <= self.max_date
        if self.closed_only:
            index_filter &= data['is_closed']
        if self.exclude_courts:
            index_filter &= ~data['court'].isin(self.exclude_courts)
        if self.exclude_nos_codes:
            index_filter &= ~data['nature_suit_code'].isin(self.exclude_nos_codes)
        return index_filter


class Project:
    def __init__(self, name, scope=Scope()):
        self.name = name
        self.scope = scope
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def build_case_index(self):
        data = utils.load_global_index()
        data = data[self.scope.index_filter(data)]
        data.to_csv(self.case_index_path, index=False)
        print(self.case_index)

    def init_judge_data(self):
        if self.judge_data_path.exists():
            self.judge_data_path.unlink()

        data = self.case_index
        ucids = data['ucid'].unique()

        for batch in utils.iter_judge_batches(1000000):
            batch = batch[batch['ucid'].isin(ucids)]
            utils.save_or_append(batch, self.judge_data_path)

        if self.processed_judge_data_path.exists():
            self.processed_judge_data_path.unlink()
        print(self.judge_data)

    def process_judge_data(self):
        data = self.case_index
        judges = self.judge_data

        assigned_judge = judges[
            (judges['_entity_extraction_method'] == 'assigned_judge') & 
            (judges['docket_source'] == 'header_metadata')
        ]
        assigned_judge = assigned_judge.drop(columns=['_entity_extraction_method', 'docket_source'])
        assigned_judge = assigned_judge.drop_duplicates(subset=['ucid'])

        assigned_judge = assigned_judge.merge(data[['ucid', 'last_entry_date']], how='left', on='ucid')
        fjc_position_data = utils.get_fjc_position_data(assigned_judge[['ucid', 'last_entry_date', 'judge_label', 'fjc_nid']])
        assigned_judge = assigned_judge.drop(columns=['last_entry_date'])
        assigned_judge = assigned_judge.merge(fjc_position_data, how='left', on='ucid')

        judge_counts = judges[~judges['judge_label'].isin(['Ambiguous', 'Inconclusive'])]
        judge_counts['judge_label'] = judge_counts['judge_label'].apply(lambda x: 'District Judge' if x == 'Article III Judge' else x)
        judge_counts = judge_counts[['ucid', 'sjid', 'judge_label']].drop_duplicates(subset=['ucid', 'sjid'])
        judge_counts = judge_counts.groupby(['ucid', 'judge_label']).size().reset_index(name='counts')
        judge_counts = judge_counts.pivot(index='ucid', columns='judge_label', values='counts').fillna(0).reset_index()
        judge_counts.columns = ['ucid'] + ['judge_count_' + x.lower().replace(' ', '_') for x in judge_counts.columns[1:]]

        judge_data = judge_counts.merge(assigned_judge, how='left', on='ucid')

        judge_data.to_csv(self.processed_judge_data_path, index=False)
        print(self.processed_judge_data)

    def register(self):
        project_registry.register(self)
    
    @property
    def project_dir(self):
        return utils.BASE_DIR / 'projects' / self.name

    @property
    def data_dir(self):
        return self.project_dir / 'data'
    
    @property
    def case_index_path(self):
        return self.data_dir / 'case_index.csv'
    
    @property
    def case_index(self):
        data = pd.read_csv(self.case_index_path)
        return utils.process_index(data)
    
    @property
    def judge_data_path(self):
        return self.data_dir / 'judges.csv'
    
    @property
    def judge_data(self):
        return pd.read_csv(self.judge_data_path)
    
    @property
    def processed_judge_data_path(self):
        return self.data_dir / 'processed_judges.csv'
    
    @property
    def processed_judge_data(self):
        return pd.read_csv(self.processed_judge_data_path)

    def __str__(self):
        return self.name

