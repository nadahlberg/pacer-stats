from setuptools import setup, find_packages

setup(
    name='pacer-stats',
    version='0.2',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'click',
        'fuzzywuzzy',
        'pandas',
        'pathlib',
        'scales-nlp',
        'simplejson',
        'torch',
        'toolz',
        'tqdm',
    ],
    entry_points={
        "console_scripts": [
            "pacer-stats=pacer_stats:cli",
        ],
    },
)

