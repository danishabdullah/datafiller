from __future__ import print_function, unicode_literals

from setuptools import setup, find_packages

__author__ = "danishabdullah"

with open("requirements.txt", 'r') as file:
    requirements = file.readlines()

with open("README.md", 'r') as file:
    readme = file.read()

with open("COPYING", 'r') as file:
    license = file.read()

setup(
    name='datafiller',
    version='0.1',
    packages=find_packages(),
    url='https://www.cri.ensmp.fr/people/coelho/datafiller.html',
    install_requires=requirements,
    license=license,
    zip_safe=False,
    keywords='Automatically populate, fill PostgreSQL database with test data. Generate test data with a data generation tool (data generator) for PostgreSQL. Import test data into PostgreSQL.',
    author='Fabien Coelho',
    author_email='fabien@coelho.net',
    description='$Package_name',
    package_data={
        '': ['requirements.txt', 'README.md', 'COPYING'],
        'datafiller/examples': ['datafiller/examples/comics.sql', 'datafiller/examples/internal.schema.checks.sql',
                                'datafiller/examples/internal.schema.sql', 'datafiller/examples/library.sql',
                                'datafiller/examples/pgbench.sql', ]
    },
    entry_points={
        'console_scripts': ['datafiller=datafiller.scripts.cli']
    },
    long_description=readme,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
