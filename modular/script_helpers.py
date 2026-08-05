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

from .globals import (VARIABLES, CONSTANTS, PN)

from .exceptions import AliasInvalidFormat, AliasInvalidCharacters, AliasPathAlreadyExists
from .globals import PopupPathDisplayModes
from .obs_related import get_python_exe
from .tech import log, play_sound, show_popup_notification

from pathlib import Path
import os
import obspython as obs


def notify_saving(clip_name: str) -> bool:
    if not VARIABLES.popups_enabled or not VARIABLES.popup_on_success:
        return False

    show_popup_notification(get_python_exe(), "Saving clip", clip_name)
    return True


def notify(success: bool, clip_path: Path, path_display_mode: PopupPathDisplayModes, skip_popup: bool = False):
    """
    Plays and shows success / failure notification if it's enabled in notifications settings.
    """
    sound_notifications = obs.obs_data_get_bool(VARIABLES.script_settings, PN.GR_SOUND_NOTIFICATION_SETTINGS)
    popup_notifications = obs.obs_data_get_bool(VARIABLES.script_settings, PN.GR_POPUP_NOTIFICATION_SETTINGS)
    python_exe = get_python_exe()

    if path_display_mode == PopupPathDisplayModes.JUST_FILE:
        clip_path = clip_path.name
    elif path_display_mode == PopupPathDisplayModes.JUST_FOLDER:
        clip_path = clip_path.parent.name
    elif path_display_mode == PopupPathDisplayModes.FOLDER_AND_FILE:
        clip_path = Path(clip_path.parent.name) / clip_path.name

    if success:
        if sound_notifications and obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_SUCCESS):
            path = obs.obs_data_get_string(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_SUCCESS_PATH)
            play_sound(path)

        if popup_notifications and not skip_popup and obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_POPUP_CLIPS_ON_SUCCESS):
            show_popup_notification(python_exe, "Clip saved", f"Clip saved to {clip_path}")
    else:
        if sound_notifications and obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_FAILURE):
            path = obs.obs_data_get_string(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_FAILURE_PATH)
            play_sound(path)

        if popup_notifications and obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_POPUP_CLIPS_ON_FAILURE):
            show_popup_notification(python_exe, "Clip not saved", "More in the logs.", "#C00000")


def load_aliases(script_settings_dict: dict):
    """
    Loads aliases to `VARIABLES.aliases`.
    Raises exception if path or name are invalid.

    :param script_settings_dict: Script settings as dict.
    """
    log.debug("Loading aliases...")

    new_aliases = {}
    aliases_list = script_settings_dict.get(PN.PROP_ALIASES_LIST)
    if aliases_list is None:
        aliases_list = CONSTANTS.DEFAULT_ALIASES

    for index, i in enumerate(aliases_list):
        value = i.get("value")
        spl = value.split(">", 1)
        try:
            path, name = spl[0].strip(), spl[1].strip()
        except IndexError:
            raise AliasInvalidFormat(index) from None

        path = os.path.expandvars(path)
        if any(i in path for i in CONSTANTS.PATH_PROHIBITED_CHARS) or any(i in name for i in CONSTANTS.FILENAME_PROHIBITED_CHARS):
            raise AliasInvalidCharacters(index)

        if Path(path) in new_aliases.keys():
            raise AliasPathAlreadyExists(index)

        new_aliases[Path(path)] = name

    VARIABLES.aliases = new_aliases
    log.debug(f"{len(VARIABLES.aliases)} aliases are loaded.")
