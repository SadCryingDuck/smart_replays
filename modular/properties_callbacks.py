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

from .globals import CONSTANTS, VARIABLES, ConfigTypes, PropertiesNames
from .exceptions import *
from .obs_related import get_base_path
from .clipname_gen import gen_filename
from .script_helpers import load_aliases, get_obs_config

import os
import json
import subprocess
import webbrowser
from pathlib import Path

import obspython as obs


# All UI callbacks have the same parameters:
# p: properties object (controls the properties UI)
# prop: property that changed
# data: script settings
# Usually I don't use `data`, cuz we have script_settings global variable.
def open_github_callback(*args):
    webbrowser.open('https://github.com/qvvonk/smart_replays', 1)


def update_aliases_callback(p, prop, data):
    """
    Checks the list of aliases and updates aliases menu (shows / hides error texts).
    """
    python_exe = os.path.join(
        get_obs_config('Python', 'Path64bit', str, ConfigTypes.USER),
        'pythonw.exe',
    )

    settings_json: dict = json.loads(obs.obs_data_get_json(data))
    if not settings_json:
        return False

    try:
        load_aliases(settings_json)
        return True

    except AliasParsingError as e:
        index = e.index

        if isinstance(e, AliasInvalidCharacters):
            error_text = (
                'Invalid path or clip name value.\n'
                'Clip name cannot contain < < / \\ | * ? : " % characters.\n'
                'Path cannot contain < > | * ? " % characters.'
            )
        elif isinstance(e, AliasInvalidFormat):
            error_text = (
                'Invalid alias format.\n'
                'Required format: DISK:\\path\\to\\folder\\or\\executable > NameYouWantToSee.\n'
                'Example: C:\\Program Files\\Minecraft > Minecraft'
            )
        elif isinstance(e, AliasPathAlreadyExists):
            error_text = 'This path has already been added to the list.'
        else:
            error_text = 'Unknown error'

        subprocess.Popen([python_exe, __file__, 'error', error_text])

    # If error in parsing
    settings_json[PropertiesNames.ALIASES_LIST_PROP].pop(index)
    new_aliases_array = obs.obs_data_array_create()

    for index, alias in enumerate(settings_json[PropertiesNames.ALIASES_LIST_PROP]):
        alias_data = obs.obs_data_create_from_json(json.dumps(alias))
        obs.obs_data_array_insert(new_aliases_array, index, alias_data)

    obs.obs_data_set_array(data, PropertiesNames.ALIASES_LIST_PROP, new_aliases_array)
    obs.obs_data_array_release(new_aliases_array)
    return True


def check_filename_template_callback(p, prop, data):
    """
    Checks filename template.
    If template is invalid, shows warning.
    """
    error_text = obs.obs_properties_get(p, PropertiesNames.CLIPS_FILENAME_TEMPLATE_ERR_TEXT)

    try:
        gen_filename(
            'clipname', obs.obs_data_get_string(data, PropertiesNames.CLIPS_FILENAME_TEMPLATE_PROP),
        )
        obs.obs_property_set_visible(error_text, False)
    except:
        obs.obs_property_set_visible(error_text, True)
    return True


def update_links_path_prop_visibility(p, prop, data):
    path_prop = obs.obs_properties_get(p, PropertiesNames.CLIPS_LINKS_FOLDER_PATH_PROP)
    path_warn_prop = obs.obs_properties_get(
        p, PropertiesNames.CLIPS_LINKS_FOLDER_PATH_WARNING_TEXT,
    )
    is_visible = obs.obs_data_get_bool(data, obs.obs_property_name(prop))

    obs.obs_property_set_visible(path_prop, is_visible)
    obs.obs_property_set_visible(path_warn_prop, is_visible)
    return True


def check_clips_links_folder_path_callback(p, prop, data):
    """
    Checks clips links folder path is in the same disk as OBS recordings path.
    If it's not - sets OBS records path as base path for clips + '_links' and shows warning.
    """
    warn_text = obs.obs_properties_get(p, PropertiesNames.CLIPS_LINKS_FOLDER_PATH_WARNING_TEXT)

    obs_records_path = Path(get_base_path())
    curr_path = Path(obs.obs_data_get_string(data, PropertiesNames.CLIPS_LINKS_FOLDER_PATH_PROP))

    if not len(curr_path.parts) or obs_records_path.parts[0] == curr_path.parts[0]:
        obs.obs_property_text_set_info_type(warn_text, obs.OBS_TEXT_INFO_WARNING)
    else:
        obs.obs_property_text_set_info_type(warn_text, obs.OBS_TEXT_INFO_ERROR)
        obs.obs_data_set_string(
            data,
            PropertiesNames.CLIPS_LINKS_FOLDER_PATH_PROP,
            str(obs_records_path / '_links'),
        )
    return True


def update_notifications_menu_callback(p, prop, data):
    """
    Updates notifications settings menu.
    If notification is enabled, shows path widget.
    """
    success_path_prop = obs.obs_properties_get(
        p, PropertiesNames.NOTIFY_CLIPS_ON_SUCCESS_PATH_PROP,
    )
    failure_path_prop = obs.obs_properties_get(
        p, PropertiesNames.NOTIFY_CLIPS_ON_FAILURE_PATH_PROP,
    )

    on_success = obs.obs_data_get_bool(data, PropertiesNames.NOTIFY_CLIPS_ON_SUCCESS_PROP)
    on_failure = obs.obs_data_get_bool(data, PropertiesNames.NOTIFY_CLIPS_ON_FAILURE_PROP)

    obs.obs_property_set_visible(success_path_prop, on_success)
    obs.obs_property_set_visible(failure_path_prop, on_failure)
    return True


def check_base_path_callback(p, prop, data):
    """
    Checks base path is in the same disk as OBS recordings path.
    If it's not - sets OBS records path as base path for clips and shows warning.
    """
    warn_text = obs.obs_properties_get(p, PropertiesNames.CLIPS_BASE_PATH_WARNING_TEXT)

    obs_records_path = Path(get_base_path())
    curr_path = Path(obs.obs_data_get_string(data, PropertiesNames.CLIPS_BASE_PATH_PROP))

    if not len(curr_path.parts) or obs_records_path.parts[0] == curr_path.parts[0]:
        obs.obs_property_text_set_info_type(warn_text, obs.OBS_TEXT_INFO_WARNING)
    else:
        obs.obs_property_text_set_info_type(warn_text, obs.OBS_TEXT_INFO_ERROR)
        obs.obs_data_set_string(data, PropertiesNames.CLIPS_BASE_PATH_PROP, str(obs_records_path))
        print('WARN')
    return True


def import_aliases_from_json_callback(*args):
    """
    Imports aliases from JSON file.
    """
    path = obs.obs_data_get_string(
        VARIABLES.script_settings, PropertiesNames.ALIASES_IMPORT_PATH_PROP,
    )
    if not path or not os.path.exists(path) or not os.path.isfile(path):
        return False

    with open(path, 'r') as f:
        data = f.read()

    try:
        data = json.loads(data)
    except:
        return False

    arr = obs.obs_data_array_create()
    for index, i in enumerate(data):
        item = obs.obs_data_create_from_json(json.dumps(i))
        obs.obs_data_array_insert(arr, index, item)

    obs.obs_data_set_array(VARIABLES.script_settings, PropertiesNames.ALIASES_LIST_PROP, arr)
    return True


def export_aliases_to_json_callback(*args):
    """
    Exports aliases to JSON file.
    """
    path = obs.obs_data_get_string(
        VARIABLES.script_settings, PropertiesNames.ALIASES_EXPORT_PATH_PROP,
    )
    if not path or not os.path.exists(path) or not os.path.isdir(path):
        return False

    aliases_dict = json.loads(obs.obs_data_get_last_json(VARIABLES.script_settings))
    aliases_dict = aliases_dict.get(PropertiesNames.ALIASES_LIST_PROP) or CONSTANTS.DEFAULT_ALIASES

    with open(os.path.join(path, 'obs_smart_replays_aliases.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(aliases_dict, ensure_ascii=False))
