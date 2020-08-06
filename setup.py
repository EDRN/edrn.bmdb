# -*- coding: utf-8 -*-
"""Setup for the edrn.bmdb package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='edrn.bmdb',
    version='1.0.0',
    description="EDRN Biomarker Database",
    long_description=long_description,
    # Get more from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    keywords='Early Detection biomarker cancer Python',
    author='Sean Kelly',
    author_email='kelly@seankelly.biz',
    url='https://pypi.python.org/pypi/edrn.bmdb',
    license='ALv2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['edrn'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'setuptools',
        'rdflib',
        'pymysql',
    ],
    entry_points={
        'console_scripts': [
            'generate-bmdb-rdf=edrn.bmdb.rdf:main',
            'fix-genenames-links=edrn.bmdb.genenames:main',
            'query-into-csv=edrn.bmdb.query:main'
        ],
    },
)
