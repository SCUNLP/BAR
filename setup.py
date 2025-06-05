from setuptools import setup, find_packages

setup(
    name="bar",
    version="0.1.0",
    packages=find_packages(),
    author="Weihong Du",
    description="BAR: A Backward Reasoning based Agent for Complex Minecraft Tasks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
