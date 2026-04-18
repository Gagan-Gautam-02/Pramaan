from setuptools import setup, find_packages

setup(
    name="pramaan_sdk",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask>=2.3",
        "pydantic>=2.0",
        "Pillow>=9.0",
    ],
    python_requires=">=3.9",
    description="Pramaan SDK — base classes for model microservices",
    author="Siddharth Kumar",
    license="MIT",
)
