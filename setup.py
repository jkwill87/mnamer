#!/usr/bin/env python3

from setuptools import setup

from mnamer.__version__ import VERSION

with open("docs/README.md", "r") as fp:
    LONG_DESCRIPTION = fp.read()

with open("requirements.txt", "r") as fp:
    REQUIREMENTS = fp.read().splitlines()

setup(
    author="Jessy Williams",
    author_email="jessy@jessywilliams.com",
    description="A media file organiser",
    entry_points={"console_scripts": ["mnamer=mnamer.__main__:main"]},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    license="MIT",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    name="mnamer",
    packages=["mnamer"],
    python_requires="~=3.7",
    url="https://github.com/jkwill87/mnamer",
    version=VERSION,
)
