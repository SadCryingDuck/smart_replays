#  OBS Smart Replays is an OBS script that allows more flexible replay buffer management:
#  set the clip name depending on the current window, set the file name format, etc.
#  Copyright (C) 2024 qvvonk
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

import ast
import logging
from typing import TypeAlias


logger = logging.getLogger()

import_dict: TypeAlias = dict[str, set[str | None]]
from_import_dict: TypeAlias = dict[str, import_dict]


class Imports:
    def __init__(self):
        self.imports: import_dict = {}  # {module_name: {module_as_name1, module_as_name2, None, etc.}}
        self.from_imports: from_import_dict = {}  # {module_name: {name: {as_name1, None, etc.}}}

    def add_import(self,
                   module_name: str,
                   module_asname: str | None,
                   name: str | None,
                   asname: str | None,
                   verbose: bool = True):
        if module_name == 'obspython':
            return

        module_asname = module_asname if module_asname != module_name else None
        name = name or None
        asname = asname if asname != name else None

        if name is None:  # if it is normal import
            if module_name not in self.imports:
                self.imports[module_name] = {module_asname}
            else:
                self.imports[module_name].add(module_asname)

            if verbose:
                logger.info(f'Absolute import of {module_name} as {module_asname or module_name} added.')

        else:  # if it is from import
            if module_name not in self.from_imports:
                self.from_imports[module_name] = {name: {asname}}
            elif name not in self.from_imports[module_name]:
                self.from_imports[module_name][name] = {asname}
            else:
                self.from_imports[module_name][name].add(asname)

            if verbose:
                logger.info(f'Absolute import of {name} as {asname or name} from {module_name} found.')

    def update(self, other: 'Imports') -> None:
        assert isinstance(other, Imports)

        for module_name, module_as_names in other.imports.items():
            for module_as_name in module_as_names:
                self.add_import(module_name, module_as_name, None, None, verbose=False)

        for module_name, names_dicts in other.from_imports.items():
            for name, asnames in names_dicts.items():
                for asname in asnames:
                    self.add_import(module_name, None, name, asname, verbose=False)

    def as_str(self):
        result = ''
        for module_name, module_as_names in self.imports.items():
            if None in module_as_names:
                result += f'import {module_name}\n'
            for asname in module_as_names:
                if asname is None:
                    continue
                result += f'import {module_name} as {asname}\n'

        for module_name, names_dicts in self.from_imports.items():
            for name, asnames in names_dicts.items():
                if None in asnames:
                    result += f'from {module_name} import {name}\n'
                for asname in asnames:
                    if asname is None:
                        continue
                    result += f'from {module_name} import {name} as {asname}\n'
        return result.strip()

    def __iadd__(self, other: 'Imports') -> 'Imports':
        assert isinstance(other, Imports)
        self.update(other)
        return self

    def __str__(self):
        return self.as_str()


def find_imports(file_name: str) -> tuple[Imports, int]:
    with open(file_name, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_name)

    code_starts_from_line_no = 0

    imports = Imports()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            continue

        if isinstance(node, ast.Import):
            for module_name in node.names:
                imports.add_import(module_name.name, module_name.asname, None, None)
            code_starts_from_line_no = node.end_lineno + 1

        elif isinstance(node, ast.ImportFrom):
            if node.level:  # if it's relative import
                logger.info(f'Relative import from {node.module} found: skipping.')
                continue

            for name in node.names:
                imports.add_import(node.module, None, name.name, name.asname)
            code_starts_from_line_no = node.end_lineno + 1
        else:
            break

    return imports, code_starts_from_line_no


FILES_ORDER = ['ui',
               'globals',
               'exceptions',
               'updates_check',
               'properties',
               'properties_callbacks',
               'tech',
               'obs_related',
               'script_helpers',
               'clipname_gen',
               'save_buffer',
               'obs_events_callbacks',
               'other_callbacks',
               'hotkeys',
               'obs_script_other']

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    imports = Imports()
    code_without_imports = ''

    with open('_license_small', 'r', encoding='utf-8') as f:
        license_text = f.read() + '\n\n'

    for file in FILES_ORDER:
        file += '.py' if not file.endswith('.py') else ''
        file_path = f'modular/{file}'

        file_imports, code_start_line = find_imports(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            file_code = ''.join(f.readlines()[code_start_line:]).strip().replace(license_text, "")

        curr_code = f'# {"-"*20} {file} {"-"*20}\n'
        curr_code += file_code + '\n\n\n'
        code_without_imports += curr_code

        imports.update(file_imports)

    total_code = license_text
    total_code += str(imports) + '\n\n'
    total_code += (
'''if __name__ != '__main__':
    import obspython as obs'''
    )
    total_code += '\n\n\n'
    total_code += code_without_imports.strip()

    with open('smart_replays.py', 'w', encoding='utf-8') as f:
        f.write(total_code)