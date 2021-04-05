"""Package manifest for this template repo."""

from setuptools import find_packages, setup

__version__ = "0.1.0"

setup(
    name="src",
    packages=find_packages(),
    version=__version__,
    description="Hard drive failure prediction models",
    author="aicoe-aiops",
    license="",
    install_requires=["click", "python-dotenv>=0.5.1"],
)
