import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hexaviz",
    version="1.2.0",
    author="Shawn Chin",
    author_email="shawnchin@gmail.com",
    description="Visualisation utility for an abstract hexagonal architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shawnchin/hexaviz",
    packages=setuptools.find_packages(),
    install_requires=[
        'Jinja2',
    ],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)