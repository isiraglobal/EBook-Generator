from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="editorial-studio",
    version="1.0.0",
    author="Editorial Studio Team",
    author_email="team@editorial-studio.dev",
    description="AI Editorial Publishing Software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/editorial-studio/editorial-studio",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "mypy>=1.7.1",
            "ruff>=0.1.15",
            "black>=23.12.0",
            "isort>=5.13.0",
            "pre-commit>=3.6.0",
        ],
        "web": ["jinja2>=3.1.3"],
    },
    entry_points={
        "console_scripts": [
            "editorial-studio = editorial_studio.__main__:main",
            "editorial-studio-api = editorial_studio.__main__:run_api",
            "editorial-studio-web = editorial_studio.__main__:run_web",
            "editorial-studio-mcp = editorial_studio.__main__:run_mcp",
        ],
    },
    include_package_data=True,
    package_data={
        "editorial_studio": [
            "assets/fonts/*",
            "assets/templates/*",
            "web/templates/*",
            "web/static/*",
        ],
    },
)