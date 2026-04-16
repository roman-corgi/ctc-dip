#! /usr/bin/env python

import os
import setuptools


def read_requirements():
    requirements = []
    with open('./requirements.txt', 'rt', encoding='utf-8') as file:
        for line in file:
            # exclude comments
            line = line[: line.find("#")] if "#" in line else line
            # clean
            line = line.strip()
            if line:
                requirements.append(line)
    return requirements


data_files_names = ["README.md", "LICENSE.txt"]
data_files_locations = [
    ('.', [f]) if os.path.exists(f) else ('.', ["../" + f])
    for f in data_files_names
]
deps = read_requirements()
dip = os.path.join('dip', '__init__.py')
version = 'esp-git-rev'
with open(os.path.join(os.path.dirname(__file__), dip)) as f:
    t = f.read()
t = t.replace('${ESP_GIT_REV}', version)
with open(os.path.join(os.path.dirname(__file__), dip), 'tw') as f:
    f.write(t)
description = 'Data Integration Processor (DIP) - the clerk that wants to be a registrar\n\n'
with open(data_files_names[0], "rt", encoding='utf-8') as f:
    description += f.read()
with open(data_files_names[1], "rt", encoding='utf-8') as f:
    license = f.read()
setuptools.setup(
    name='dip',
    version='1.0.0',
    packages=setuptools.find_packages(),
    setup_requires=deps,
    src_root=os.path.abspath(os.path.dirname(__file__)),
    install_requires=deps,
    package_data={
        'dip.basis': ['*.dot'],
        'dip.base': ['*.xml'],
    },
    author='Al Niessner',
    author_email='Al.Niessner@jpl.nasa.gov',
    description='ROMAN CGI Data Integration Processor (DIP)',
    license=license,
    keywords='clerk',
    url='https://github.com/??/??dip',
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.12',
        "Operating System :: OS Independent",
        'Development Status :: 5 - Production/Stable',
    ],
    data_files=data_files_locations,
    long_description=description,
    long_description_content_type="text/markdown",
    python_requires='>3.10',
)
