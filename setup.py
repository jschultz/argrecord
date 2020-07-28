from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name = "argrecord",
    description = "Automates logfile and self-describing output file generation; provides Make-like functionality to re-run a script.",
    long_description=readme(),
    long_description_content_type = "text/x-rst",
    version = "0.1.2",
    author = "Jonathan Schultz",
    author_email = "jonathan@schultz.la",
    license = "GPL3",
    packages = ["argrecord"],
    install_requires = ["argparse"],
    entry_points = {
        "console_scripts": ['argreplay = argrecord.argreplay:main']
        },
    include_package_data=True,
    classifiers = [
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        ],
    )
