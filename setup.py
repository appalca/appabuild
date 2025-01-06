from setuptools import find_packages, setup

setup(
    name="appabuild",
    version="0.2.0",
    author="Maxime Peralta",
    author_email="maxime.peralta@cea.fr",
    description="Appa Build is a package to build impact models",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "appabuild=app.cli.lca:app",
        ],
    },
)