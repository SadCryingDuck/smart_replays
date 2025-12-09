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

import re
import sys
import ctypes
from enum import Enum
from pathlib import Path
from threading import Lock
from collections import deque, defaultdict

import obspython as obs


user32 = ctypes.windll.user32


class CONSTANTS:
    VERSION = '1.0.8'
    OBS_VERSION_STRING = obs.obs_get_version_string()
    OBS_VERSION_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    OBS_VERSION = [int(i) for i in OBS_VERSION_RE.match(OBS_VERSION_STRING).groups()]
    CLIPS_FORCE_MODE_LOCK = Lock()
    VIDEOS_FORCE_MODE_LOCK = Lock()
    FILENAME_PROHIBITED_CHARS = r'/\:"<>*?|%'
    PATH_PROHIBITED_CHARS = r'"<>*?|%'
    DEFAULT_FILENAME_FORMAT = '%NAME_%d.%m.%Y_%H-%M-%S'
    DEFAULT_ALIASES = (
        {'value': 'C:\\Windows\\explorer.exe > Desktop', 'selected': False, 'hidden': False},
        {'value': f'{sys.executable} > OBS', 'selected': False, 'hidden': False},
    )


class VARIABLES:
    update_available: bool = False
    clip_exe_history: deque[Path, ...] | None = None
    video_exe_history: defaultdict[Path, int] | None = (
        None  # {Path(path/to/executable): active_seconds_amount
    )
    exe_path_on_video_stopping_event: Path | None = None
    aliases: dict[Path, str] = {}
    script_settings = None
    hotkey_ids: dict = {}
    force_mode = None


class ConfigTypes(Enum):
    PROFILE = 0
    APP = 1
    USER = 2


class ClipNamingModes(Enum):
    CURRENT_PROCESS = 0
    MOST_RECORDED_PROCESS = 1
    CURRENT_SCENE = 2


class VideoNamingModes(Enum):
    CURRENT_PROCESS = 0
    MOST_RECORDED_PROCESS = 1
    CURRENT_SCENE = 2


class PopupPathDisplayModes(Enum):
    FULL_PATH = 0
    FOLDER_AND_FILE = 1
    JUST_FOLDER = 2
    JUST_FILE = 3


class PropertiesNames:
    # Prop groups
    CLIPS_PATH_SETTINGS_GROUP = 'clips_path_settings'
    VIDEOS_PATH_SETTINGS_GROUP = 'videos_path_settings'
    SOUND_NOTIFICATION_SETTINGS_GROUP = 'sound_notification_settings'
    POPUP_NOTIFICATION_SETTINGS_GROUP = 'popup_notification_settings'
    ALIASES_SETTINGS_GROUP = 'aliases_settings'
    OTHER_SETTINGS_GROUP = 'other_settings'

    # Clips path settings
    CLIPS_BASE_PATH_PROP = 'clips_base_path'
    CLIPS_BASE_PATH_WARNING_TEXT = 'clips_base_path_warning'
    CLIPS_NAMING_MODE_PROP = 'clips_naming_mode'
    CLIPS_HOTKEY_TIP_TEXT = 'clips_hotkey_tip'
    CLIPS_FILENAME_TEMPLATE_PROP = 'clips_filename_template'
    CLIPS_FILENAME_TEMPLATE_ERR_TEXT = 'clips_filename_template_err'
    CLIPS_SAVE_TO_FOLDER_PROP = 'clips_save_to_folder'
    CLIPS_ONLY_FORCE_MODE_PROP = 'clips_only_force_mode'  # todo
    CLIPS_CREATE_LINKS_PROP = 'clips_create_links'
    CLIPS_LINKS_FOLDER_PATH_PROP = 'clips_links_folder_path'
    CLIPS_LINKS_FOLDER_PATH_WARNING_TEXT = 'clips_links_folder_path_warning'

    # Videos path settings
    VIDEOS_NAMING_MODE_PROP = 'videos_naming_mode'
    VIDEOS_HOTKEY_TIP_TEXT = 'videos_hotkey_tip'
    VIDEOS_FILENAME_FORMAT_PROP = 'videos_filename_format'
    VIDEOS_FILENAME_FORMAT_ERR_TEXT = 'videos_filename_format_err'
    VIDEOS_SAVE_TO_FOLDER_PROP = 'videos_save_to_folder'
    VIDEOS_ONLY_FORCE_MODE_PROP = 'videos_only_force_mode'

    # Sound notification settings
    NOTIFY_CLIPS_ON_SUCCESS_PROP = 'notify_clips_on_success'
    NOTIFY_CLIPS_ON_SUCCESS_PATH_PROP = 'notify_clips_on_success_path'
    NOTIFY_CLIPS_ON_FAILURE_PROP = 'notify_clips_on_failure'
    NOTIFY_CLIPS_ON_FAILURE_PATH_PROP = 'notify_clips_on_failure_path'
    NOTIFY_VIDEOS_ON_SUCCESS_PROP = 'notify_videos_on_success'
    NOTIFY_VIDEOS_ON_SUCCESS_PATH_PROP = 'notify_videos_on_success_path'
    NOTIFY_VIDEOS_ON_FAILURE_PROP = 'notify_videos_on_failure'
    NOTIFY_VIDEOS_ON_FAILURE_PATH_PROP = 'notify_videos_on_failure_path'

    # Popup notification settings
    POPUP_CLIPS_ON_SUCCESS_PROP = 'popup_clips_on_success'
    POPUP_CLIPS_ON_FAILURE_PROP = 'popup_clips_on_failure'
    POPUP_VIDEOS_ON_SUCCESS_PROP = 'popup_videos_on_success'
    POPUP_VIDEOS_ON_FAILURE_PROP = 'popup_videos_on_failure'
    POPUP_PATH_DISPLAY_MODE_PROP = 'prop_popup_path_display_mode'

    # Aliases settings
    ALIASES_LIST_PROP = 'aliases_list'
    ALIASES_DESC_TEXT = 'aliases_desc'

    # # Aliases parsing error texts
    # ALIASES_PATH_EXISTS_TEXT = 'aliases_path_exists_err'
    # ALIASES_INVALID_FORMAT_TEXT = 'aliases_invalid_format_err'
    # ALIASES_INVALID_CHARACTERS_TEXT = 'aliases_invalid_characters_err'

    # Export / Import aliases section
    ALIASES_EXPORT_PATH_PROP = 'aliases_export_path'
    ALIASES_EXPORT_BUTTON = 'aliases_export_btn'
    ALIASES_IMPORT_PATH_PROP = 'aliases_import_path'
    ALIASES_IMPORT_BUTTON = 'aliases_import_btn'

    # Other section
    RESTART_BUFFER_PROP = 'restart_buffer'
    RESTART_BUFFER_LOOP_PROP = 'restart_buffer_loop'
    RESTART_BUFFER_LOOP_TEXT = 'restart_buffer_loop_desc'

    # Hotkeys
    SAVE_BUFFER_MODE_1_HOTKEY = 'save_buffer_force_mode_1'
    SAVE_BUFFER_MODE_2_HOTKEY = 'save_buffer_force_mode_2'
    SAVE_BUFFER_MODE_3_HOTKEY = 'save_buffer_force_mode_3'
    SAVE_VIDEO_MODE_1_HOTKEY = 'save_video_force_mode_1'
    SAVE_VIDEO_MODE_2_HOTKEY = 'save_video_force_mode_2'
    SAVE_VIDEO_MODE_3_HOTKEY = 'save_video_force_mode_3'
