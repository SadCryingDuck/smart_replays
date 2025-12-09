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

from .tech import _print, play_sound
from .globals import PropertiesNames, CONSTANTS, VARIABLES, ConfigTypes, PopupPathDisplayModes
from .exceptions import AliasInvalidFormat, AliasInvalidCharacters, AliasPathAlreadyExists
from .obs_related import get_obs_config

import os
import subprocess
from pathlib import Path

import obspython as obs


def notify(success: bool, clip_path: Path, path_display_mode: PopupPathDisplayModes):
    """
    Plays and shows success / failure notification if it's enabled in notifications settings.
    """
    sound_notifications = obs.obs_data_get_bool(
        VARIABLES.script_settings, PropertiesNames.SOUND_NOTIFICATION_SETTINGS_GROUP,
    )
    popup_notifications = obs.obs_data_get_bool(
        VARIABLES.script_settings, PropertiesNames.POPUP_NOTIFICATION_SETTINGS_GROUP,
    )
    python_exe = os.path.join(
        get_obs_config('Python', 'Path64bit', str, ConfigTypes.APP), 'pythonw.exe',
    )

    if path_display_mode == PopupPathDisplayModes.JUST_FILE:
        clip_path = clip_path.name
    elif path_display_mode == PopupPathDisplayModes.JUST_FOLDER:
        clip_path = clip_path.parent.name
    elif path_display_mode == PopupPathDisplayModes.FOLDER_AND_FILE:
        clip_path = Path(clip_path.parent.name) / clip_path.name

    if success:
        if sound_notifications and obs.obs_data_get_bool(
            VARIABLES.script_settings, PropertiesNames.NOTIFY_CLIPS_ON_SUCCESS_PROP,
        ):
            path = obs.obs_data_get_string(
                VARIABLES.script_settings, PropertiesNames.NOTIFY_CLIPS_ON_SUCCESS_PATH_PROP,
            )
            play_sound(path)

        if popup_notifications and obs.obs_data_get_bool(
            VARIABLES.script_settings, PropertiesNames.POPUP_CLIPS_ON_SUCCESS_PROP,
        ):
            subprocess.Popen([python_exe, __file__, 'Clip saved', f'Clip saved to {clip_path}'])
    else:
        if sound_notifications and obs.obs_data_get_bool(
            VARIABLES.script_settings, PropertiesNames.NOTIFY_CLIPS_ON_FAILURE_PROP,
        ):
            path = obs.obs_data_get_string(
                VARIABLES.script_settings, PropertiesNames.NOTIFY_CLIPS_ON_FAILURE_PATH_PROP,
            )
            play_sound(path)

        if popup_notifications and obs.obs_data_get_bool(
            VARIABLES.script_settings, PropertiesNames.POPUP_CLIPS_ON_FAILURE_PROP,
        ):
            subprocess.Popen(
                [python_exe, __file__, 'Clip not saved', 'More in the logs.', '#C00000'],
            )


def load_aliases(script_settings_dict: dict):
    """
    Loads aliases to `VARIABLES.aliases`.
    Raises exception if path or name are invalid.

    :param script_settings_dict: Script settings as dict.
    """
    _print('Loading aliases...')

    new_aliases = {}
    aliases_list = script_settings_dict.get(PropertiesNames.ALIASES_LIST_PROP)
    if aliases_list is None:
        aliases_list = CONSTANTS.DEFAULT_ALIASES

    for index, i in enumerate(aliases_list):
        value = i.get('value')
        spl = value.split('>', 1)
        try:
            path, name = spl[0].strip(), spl[1].strip()
        except IndexError:
            raise AliasInvalidFormat(index)

        path = os.path.expandvars(path)
        if any(i in path for i in CONSTANTS.PATH_PROHIBITED_CHARS) or any(
            i in name for i in CONSTANTS.FILENAME_PROHIBITED_CHARS
        ):
            raise AliasInvalidCharacters(index)

        if Path(path) in new_aliases.keys():
            raise AliasPathAlreadyExists(index)

        new_aliases[Path(path)] = name

    VARIABLES.aliases = new_aliases
    _print(f'{len(VARIABLES.aliases)} aliases are loaded.')
