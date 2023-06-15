# pacer-stats

### To do
1. Add event mapping
2. Add pathway object
3. Add event timing

### Project To Do
1. Settlement: incorporate manual codings
2. Pathways: case dismissed flag
3. Pathways: 'pathway categories'

## Usage

1. Install package (from the `pacer-stats` directory): `pip install -e .`
2. Create a project directory in `./projects/myproject`
3. Create a config file `./projects/myproject/config.py`
4. Run: `pacer-stats build myproject`

Project data will be saved in:
`./projects/myproject/data`

## Config

    # contents of myproject/config.py

    from pacer_stats import Project, Scope

    scope = Scope()
    project = Project(name='myproject', scope=scope)
    project.register()

Scope object can include the following arguments:

    scope = Scope(
        case_type='cv',
        min_date='2016-01-01',
        max_date='2017-12-31',
        closed_only=True,
        exclude_court=['ilnd']
        exclude_nos_codes=[422, 423],
    )

## Updates
To update everything from a clean slate, run:
`pacer-stats build myproject --reset`


To update certain files, just delete the file from `./projects/myproject/data` and run the build command without the `--reset` flag.

## Required data

To use this, two additional data files are required:

1. `./data/judge_entities.csv`
A csv export of SCALES-OKN judge table in mongo

2. `./data/global_index.csv`
An index of SCALES-OKN case data.  If you have a directory with PACER data from the pacer-tools crawler you can set an env var `PACER_DIR=/path/to/pacer` and run `pacer-stats build-global-index` to create this file.

