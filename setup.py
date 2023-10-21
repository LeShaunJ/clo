#!/usr/bin/env python3
from setuptools import setup


def read_files(*files: str):
    data = []
    for file in files:
        with open(file, encoding="utf-8") as f:
            data.append(f.read())
    return "\n".join(data)


meta = {}
with open("./src/clo/meta.py", encoding="utf-8") as f:
    exec(f.read(), meta)

setup(
    name=meta["__prog__"],
    version=meta["__version__"],
    author=meta["__author__"],
    author_email=meta["__contact__"],
    description=meta["__doc__"],
    license=meta["__license__"],
    keywords="cli python3 odoo command-line-tool api xmlrpc",
    url=f'https://leshaunj.github.io/{meta["__prog__"]}',
    packages=[
        meta["__prog__"],
    ],
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=["python-dotenv", "requests"],
    long_description=read_files("README.md", "CHANGELOG.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    entry_points={
        "console_scripts": [
            f'{meta["__prog__"]}={meta["__prog__"]}:Main',
        ],
    },
)
