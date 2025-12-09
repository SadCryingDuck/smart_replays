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

from .globals import VARIABLES, CONSTANTS, PN, ClipNamingModes

from .tech import get_active_window_pid, get_executable_path, _print
from .obs_related import get_current_scene_name

import obspython as obs
from pathlib import Path
from datetime import datetime
import traceback


def gen_clip_base_name(mode: ClipNamingModes | None = None) -> str:
    """
    Generates the base name of the clip based on the selected naming mode.
    It does NOT generate a new path for the clip or filename, only its base name.

    :param mode: Clip naming mode. If None, the mode is fetched from the script config.
                 If a value is provided, it overrides the configs value.
    :return: The base name of the clip based on the selected naming mode.
    """
    _print("Generating clip base name...")
    mode = obs.obs_data_get_int(VARIABLES.script_settings, PN.PROP_CLIPS_NAMING_MODE) if mode is None else mode
    mode = ClipNamingModes(mode)

    if mode in [ClipNamingModes.CURRENT_PROCESS, ClipNamingModes.MOST_RECORDED_PROCESS]:
        if mode is ClipNamingModes.CURRENT_PROCESS:
            _print("Clip file name depends on the name of an active app (.exe file name) at the moment of clip saving.")
            pid = get_active_window_pid()
            executable_path = get_executable_path(pid)
            _print(f"Current active window process ID: {pid}")
            _print(f"Current active window executable: {executable_path}")

        else:
            _print("Clip file name depends on the name of an app (.exe file name) "
                   "that was active most of the time during the clip recording.")
            if VARIABLES.clip_exe_history:
                executable_path = max(VARIABLES.clip_exe_history, key=VARIABLES.clip_exe_history.count)
            else:
                executable_path = get_executable_path(get_active_window_pid())

        _print(f'Searching for {executable_path} in aliases list...')
        if alias := get_alias(executable_path, VARIABLES.aliases):
            _print(f'Alias found: {alias}.')
            return alias
        else:
            _print(f"{executable_path} or its parents weren't found in aliases list. "
                   f"Assigning the name of the executable: {executable_path.stem}")
            return executable_path.stem

    else:
        _print("Clip filename depends on the name of the current scene name.")
        return get_current_scene_name()


def get_alias(executable_path: str | Path, aliases_dict: dict[Path, str]) -> str | None:
    """
    Retrieves an alias for the given executable path from the provided dictionary.

    The function first checks if the exact `executable_path` exists in `aliases_dict`.
    If not, it searches for the closest parent directory that is present in the dictionary.

    :param executable_path: A file path or string representing the executable.
    :param aliases_dict: A dictionary where keys are `Path` objects representing executable file paths
                         or directories, and values are their corresponding aliases.
    :return: The corresponding alias if found, otherwise `None`.
    """
    exe_path = Path(executable_path)
    if exe_path in aliases_dict:
        return aliases_dict[exe_path]

    for parent in exe_path.parents:
        if parent in aliases_dict:
            return aliases_dict[parent]



def gen_filename(base_name: str, template: str, dt: datetime | None = None) -> str:
    """
    Generates a file name based on the template.
    If the template is invalid or formatting fails, raises ValueError.
    If the generated name contains prohibited characters, raises SyntaxError.

    :param base_name: Base name for the file.
    :param template: Template for generating the file name.
    :param dt: Optional datetime object; uses current time if None.
    :return: Formatted file name.
    """
    if not template:
        raise ValueError

    dt = dt or datetime.now()
    filename = template.replace("%NAME", base_name)

    try:
        filename = dt.strftime(filename)
    except Exception as e:
        _print(f"An error occurred while generating the file name using the template {template}.")
        _print(traceback.format_exc())
        raise ValueError from e

    if any(i in filename for i in CONSTANTS.FILENAME_PROHIBITED_CHARS):
        raise SyntaxError
    return filename


def ensure_unique_filename(file_path: str | Path) -> Path:
    """
    Generates a unique filename by adding a numerical suffix if the file already exists.

    :param file_path: A string or Path object representing the target file.
    :return: A unique Path object with a modified name if necessary.
    """
    file_path = Path(file_path)
    parent, stem, suffix = file_path.parent, file_path.stem, file_path.suffix
    counter = 1

    while file_path.exists():
        file_path = parent / f"{stem} ({counter}){suffix}"
        counter += 1

    return file_path
