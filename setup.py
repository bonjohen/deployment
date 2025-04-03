from setuptools import setup, find_packages

setup(
    name="pythonweb-installer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click>=8.0",
        "rich>=10.0",
        "pyyaml>=6.0",
        "jinja2>=3.0",
        "paramiko>=2.7",  # For SSH operations
        "python-dotenv>=0.19",
        "requests>=2.25",
        "cryptography>=3.4",
    ],
    entry_points={
        "console_scripts": [
            "pythonweb-install=pythonweb_installer.cli:main",
        ],
    },
    python_requires=">=3.7",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated installer for PythonWeb template application",
    long_description="A tool to automate the deployment of PythonWeb template application",
    url="https://github.com/yourusername/deployment",
)

