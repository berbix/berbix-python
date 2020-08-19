import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="berbix",
    version="0.0.13",
    author="Eric Levine",
    author_email="eric@berbix.com",
    description="SDK for Berbix integrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/berbix/berbix-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
    ],
)
