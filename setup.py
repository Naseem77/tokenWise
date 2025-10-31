"""Setup script for TokenWise package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tokenwise-optimizer",
    version="1.0.0",
    author="TokenWise Team",
    author_email="team@tokenwise.ai",
    description="Smart Context Optimization for LLMs - Reduce tokens by 70-90%",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Naseem77/tokenWise",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tokenwise=tokenwise.__main__:main",
        ],
    },
    package_data={
        "tokenwise": ["*.py"],
    },
    include_package_data=True,
    keywords="llm, tokens, optimization, context, ai, gpt, openai, cost-reduction",
    project_urls={
        "Bug Reports": "https://github.com/Naseem77/tokenWise/issues",
        "Source": "https://github.com/Naseem77/tokenWise",
        "Documentation": "https://github.com/Naseem77/tokenWise#readme",
    },
)
