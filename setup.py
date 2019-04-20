from setuptools import setup, find_packages
setup(
    name="concavehull_evaluation",
    version="0.0.1",
    packages=['concave_evaluation'],
    scripts=[],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    # polylidar
    install_requires=['Click', 'numpy', 'colorama','shapely','scipy', 'matplotlib','descartes', 'pandas', 'seaborn', 'rasterio', 'sklearn', 'shapely_geojson', 'psycopg2'],

    entry_points='''
        [console_scripts]
        concave=concave_evaluation.scripts.simple:cli
    ''',

    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     'challenge': ['*.txt', '*.rst', '*.md', '*.pyx', '*.json'],
    #     'afrl': ['*.xml', '*.html', '*.md', '*.json'],
    #     'lmcp': ['*.xml', '*.html', '*.md', '*.json'],
    # },

    # metadata to display on PyPI
    author="Jeremy Castagno",
    author_email="jdcasta@umich.edu",
    description="Concave Hull Evaluation",
    license="MIT",
    keywords="concave hull benchmark",
    url="https://github.com/JeremyBYU/concavehull-evaluation",   # project home page, if any
    project_urls={
        "Bug Tracker": "https://github.com/JeremyBYU/concavehull-evaluation/issues",
    }
)