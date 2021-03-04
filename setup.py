#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The setup script."""
from setuptools import setup, find_packages
from typing import List

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements: List[str] = ['typing_extensions', 'PyYAML']

setup_requirements: List[str] = ['pytest-runner']

test_requirements: List[str] = ['pytest>=3']


setup(
    author="Vince Broz",
    author_email='vince@broz.cc',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="op-env allows you to use 1Password entries as environment variable-style secrets",  # noqa: E501
    entry_points={
        'console_scripts': [
            'op-env=op_env._cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords='op_env',
    name='op_env',
    packages=find_packages(include=['op_env',
                                    'op_env.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/apiology/op_env',
    version='0.6.0',
    zip_safe=False,
)
