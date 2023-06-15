from pacer_stats import Project, Scope

scope = Scope(
    # Civil only
    case_type='cv',

    # 2016-2017
    min_date='2016-01-01',
    max_date='2017-12-31',

    # Closed defined as having a terminating date OR a CLOSED flag
    closed_only=True,

    exclude_nos_codes=[
        # Charlotte says keep: 151 Medicare act
        220, # Forclosure
        422, 423, # Bankruptcy
        462, 463, 465, # Immigration
        510, 530, 535, 540, 560, # Prisoner
        # Charlotte says keep: 710 FLSA
        861, 862, 863, 864, 865, # Social Security
        # Maybe? 870 Taxes
    ],
)

project = Project(
    name='settlement',
    scope=scope,
)


project.register()

