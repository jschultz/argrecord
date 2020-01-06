from setuptools import setup

setup(
    name = "argrecord",
    packages = ["argrecord"],
    install_requires = ["argparse"],
    entry_points = {
        "console_scripts": ['argreplay = argrecord.argreplay:main']
        },
    include_package_data=True,
    version = "0.1",
    description = "",
    author = "Jonathan Schultz",
    author_email = "jonathan@schultz.la",
    license = "GPL3",
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GPL3 License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        'Intended Audience :: Developers',
        ],
    )
