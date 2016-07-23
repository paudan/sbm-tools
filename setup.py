
from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sbm-tools',
    version='1.0',
    description='API implementations and analytics tools for various social bookmarking services',
    long_description=long_description,
    url='http://www.github.com/paudan/sbm-tools',
    author='Paulius Danenas',
    author_email='danpaulius@gmail.com',
    license='MIT',
    keywords='social bookmarking api links analysis',
    packages=['sbmtools', 'sbmtools.examples'],
    package_dir={'sbmtools': 'sbmtools',
                 'sbmtools.examples': 'examples'},
    install_requires=['requests', 'mechanize', 'lxml', 'cssselect'],
)