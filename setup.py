from setuptools import setup, find_packages

setup(
    name="alter_ego_llm",
    version="1.1.0",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "ego=ego:cli.main",  # Adjust if necessary
        ],
    },
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.8",
    author="Max R. P. Grossmann",
    author_email="ego@mg.sb",
    description="Library to run experiments with LLMs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://ego.mg.sb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
)
