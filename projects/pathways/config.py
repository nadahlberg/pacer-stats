from pacer_stats import Project, Scope


scope = Scope(
    case_type='cv',

    min_date='2016-01-01',
    max_date='2017-12-31',

    exclude_nos_codes=[
        422, 423, # Bankruptcy
        462, 463, 465, # Immigration
        510, 530, 535, 540, 560, # Prisoner
        861, 862, 863, 864, 865, # Social Security
    ],
)

project = Project(
    name='pathways',
    scope=scope,
)


project.register()

