#!/usr/bin/env python3
import os
import sys

import yaml

DOC_HEADER = """# File auto-generated on build process. Do not change it.
# Add new dependencies to dependencies.yaml file instead.
#
"""


def generate_files(os_distro):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, '../dependencies.yaml')) as fd:
        content = yaml.safe_load(fd)

    dev_deps = content.get('development-deps', {})
    dev_deps = dev_deps.get('common', []) + dev_deps.get(os_distro, [])

    runtime_deps = content.get('runtime-deps', {})
    runtime_deps = runtime_deps.get('common', []) + runtime_deps.get(os_distro, [])

    if os_distro == 'ubuntu':
        pkg_deps = 'Depends: ' + ',\n\t'.join(runtime_deps)
        pkg_deps += '\nBuild-Depends: ' + ',\n\t'.join(dev_deps)

    elif os_distro in ['fedora', 'opensuse-leap']:
        pkg_deps = '\n'.join(['Requires:\t' + d for d in runtime_deps])
        pkg_deps += '\n' + '\n'.join(['BuildRequires:\t' + d for d in dev_deps])

    else:
        raise Exception('Unsupported OS distribution')

    with open(f'{current_dir}/{os_distro}-pkg-deps', 'w') as fd:
        fd.write(pkg_deps)

    with open(f'{current_dir}/../{os_distro}-dev-deps.list', 'w') as fd:
        fd.write(DOC_HEADER + '\n'.join(dev_deps))

    with open(f'{current_dir}/../{os_distro}-runtime-deps.list', 'w') as fd:
        fd.write(DOC_HEADER + '\n'.join(runtime_deps))


if __name__ == '__main__':
    for os_distro in ['ubuntu', 'fedora', 'opensuse-leap']:
        try:
            generate_files(os_distro)
        except Exception:
            sys.exit(1)

    sys.exit(0)
