#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
import distutils
from distutils.cmd import Command
import distutils.command.clean
from distutils.dir_util import remove_tree
import subprocess
import os
from typing import List, Tuple, Optional

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements: List[str] = ['typing_extensions']

setup_requirements: List[str] = ['pytest-runner']

test_requirements: List[str] = ['pytest>=3']


class MypyCleanCommand(Command):
    """Regular clean plus mypy cache"""

    description = 'Run mypy on source code'
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        if os.path.exists('.mypy_cache'):
            remove_tree('.mypy_cache')


class MypyCommand(Command):
    description = 'Run mypy on source code'
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        """Run command."""
        command = ['mypy', '--html-report', 'types/coverage', '.']
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)  # type: ignore
        subprocess.check_call(command)


class QualityCommand(Command):
    quality_target: Optional[str]

    description = 'Run quality tools on source code'
    user_options: List[Tuple[str, Optional[str], str]] = []

    def initialize_options(self) -> None:
        pass

    def finalize_options(self) -> None:
        pass

    def run(self) -> None:
        """Run command."""
        command = ['overcommit', '--run']
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)  # type: ignore
        subprocess.check_call(command)


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
    version='0.2.0',
    zip_safe=False,
    cmdclass={
        'quality': QualityCommand,
        'typesclean': MypyCleanCommand,
        'types': MypyCommand,
    },
)
