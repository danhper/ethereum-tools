from setuptools import setup, find_packages


setup(
    name="ethereum-tools",
    version="0.1.1",
    packages=find_packages(exclude="tests"),
    description="High-level tools and library to interact with Ethereum",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Daniel Perez",
    author_email="daniel@perez.sh",
    url="https://github.com/danhper/ethereum-tools",
    download_url="https://github.com/danhper/ethereum-tools/archive/master.zip",
    license="MIT",
    install_requires=[
        "web3",
        "smart-open",
        "retry",
    ],
    extras_require={
        "dev": [
            "pylint",
            "black",
            "pytest",
        ]
    },
    entry_points={"console_scripts": ["eth-tools=eth_tools.cli:run"]},
)
