#!/usr/bin/env python
if __name__ == '__main__':
    import logging
    from pkg_resources import Requirement
    from setuptools import setup, find_packages

    log = logging.getLogger(__name__)

    with open('requirements.txt') as f:
        REQUIREMENTS = []
        for req in f.readlines():
            req = req.strip()
            try:
                Requirement.parse(req)
            except:
                log.warning('failed to parse `{0}` from requirements.txt, skipping\n'.format(req))
                continue
            if len(req) is 0:
                continue
            REQUIREMENTS.append(req)


    setup(
        name='Sublime Text Utility for Ansible',
        version='0.0.1',
        description='',
        author='Flavien Chantelot',
        author_email='contact@flavien.io',
        url='https://github.com/Dorn-/sublime_avault',
        packages=find_packages(),
        include_package_data=True,
        install_requires=REQUIREMENTS,
        zip_safe=False,
    )