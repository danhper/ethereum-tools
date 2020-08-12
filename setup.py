from setuptools import setup, find_packages


setup(
    name="eth-tools",
    packages=find_packages(exclude="tests"),
    install_requires=[
        "web3",
        "smart-open",
        "retry",
    ],
    extras_require={
        "dev": [
            "pylint",
            "pytest",
        ]
    },
    entry_points={"console_scripts": ["eth-tools=eth_tools.cli:run"]}
)
