"""Setup script for Dagster project."""
from setuptools import setup, find_packages

setup(
    name="omc-flywheel-dagster",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dagster>=1.6.0",
        "dagster-aws>=0.23.0",
        "boto3>=1.34.0",
        "botocore>=1.34.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
)

