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

import sys
from enum import Enum
import ctypes
from threading import Lock
from pathlib import Path
from collections import deque, defaultdict
import obspython as obs
import re

user32 = ctypes.windll.user32


class CONSTANTS:
    VERSION = "1.0.8"
    OBS_VERSION_STRING = obs.obs_get_version_string()
    OBS_VERSION_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    OBS_VERSION = [int(i) for i in OBS_VERSION_RE.match(OBS_VERSION_STRING).groups()]
    CLIPS_FORCE_MODE_LOCK = Lock()
    VIDEOS_FORCE_MODE_LOCK = Lock()
    FILENAME_PROHIBITED_CHARS = r'/\:"<>*?|%'
    PATH_PROHIBITED_CHARS = r'"<>*?|%'
    DEFAULT_FILENAME_FORMAT = "%NAME_%d.%m.%Y_%H-%M-%S"
    DEFAULT_ALIASES = (
        {"value": "C:\\Windows\\explorer.exe > Desktop", "selected": False, "hidden": False},
        {"value": f"{sys.executable} > OBS", "selected": False, "hidden": False}
    )


class VARIABLES:
    update_available: bool = False
    clip_exe_history: deque[Path, ...] | None = None
    video_exe_history: defaultdict[Path, int] | None = None  # {Path(path/to/executable): active_seconds_amount
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
    GR_CLIPS_PATH_SETTINGS = "clips_path_settings"
    GR_VIDEOS_PATH_SETTINGS = "videos_path_settings"
    GR_SOUND_NOTIFICATION_SETTINGS = "sound_notification_settings"
    GR_POPUP_NOTIFICATION_SETTINGS = "popup_notification_settings"
    GR_ALIASES_SETTINGS = "aliases_settings"
    GR_OTHER_SETTINGS = "other_settings"

    # Clips path settings
    PROP_CLIPS_BASE_PATH = "clips_base_path"
    TXT_CLIPS_BASE_PATH_WARNING = "clips_base_path_warning"
    PROP_CLIPS_NAMING_MODE = "clips_naming_mode"
    TXT_CLIPS_HOTKEY_TIP = "clips_hotkey_tip"
    PROP_CLIPS_FILENAME_TEMPLATE = "clips_filename_template"
    TXT_CLIPS_FILENAME_TEMPLATE_ERR = "clips_filename_template_err"
    PROP_CLIPS_SAVE_TO_FOLDER = "clips_save_to_folder"
    PROP_CLIPS_ONLY_FORCE_MODE = "clips_only_force_mode" # todo
    PROP_CLIPS_CREATE_LINKS = "clips_create_links"
    PROP_CLIPS_LINKS_FOLDER_PATH = "clips_links_folder_path"
    TXT_CLIPS_LINKS_FOLDER_PATH_WARNING = "clips_links_folder_path_warning"

    # Videos path settings
    PROP_VIDEOS_NAMING_MODE = "videos_naming_mode"
    TXT_VIDEOS_HOTKEY_TIP = "videos_hotkey_tip"
    PROP_VIDEOS_FILENAME_FORMAT = "videos_filename_format"
    TXT_VIDEOS_FILENAME_FORMAT_ERR = "videos_filename_format_err"
    PROP_VIDEOS_SAVE_TO_FOLDER = "videos_save_to_folder"
    PROP_VIDEOS_ONLY_FORCE_MODE = "videos_only_force_mode"

    # Sound notification settings
    PROP_NOTIFY_CLIPS_ON_SUCCESS = "notify_clips_on_success"
    PROP_NOTIFY_CLIPS_ON_SUCCESS_PATH = "notify_clips_on_success_path"
    PROP_NOTIFY_CLIPS_ON_FAILURE = "notify_clips_on_failure"
    PROP_NOTIFY_CLIPS_ON_FAILURE_PATH = "notify_clips_on_failure_path"
    PROP_NOTIFY_VIDEOS_ON_SUCCESS = "notify_videos_on_success"
    PROP_NOTIFY_VIDEOS_ON_SUCCESS_PATH = "notify_videos_on_success_path"
    PROP_NOTIFY_VIDEOS_ON_FAILURE = "notify_videos_on_failure"
    PROP_NOTIFY_VIDEOS_ON_FAILURE_PATH = "notify_videos_on_failure_path"

    # Popup notification settings
    PROP_POPUP_CLIPS_ON_SUCCESS = "popup_clips_on_success"
    PROP_POPUP_CLIPS_ON_FAILURE = "popup_clips_on_failure"
    PROP_POPUP_VIDEOS_ON_SUCCESS = "popup_videos_on_success"
    PROP_POPUP_VIDEOS_ON_FAILURE = "popup_videos_on_failure"
    PROP_POPUP_PATH_DISPLAY_MODE = "prop_popup_path_display_mode"

    # Aliases settings
    PROP_ALIASES_LIST = "aliases_list"
    TXT_ALIASES_DESC = "aliases_desc"

    # Aliases parsing error texts
    TXT_ALIASES_PATH_EXISTS = "aliases_path_exists_err"
    TXT_ALIASES_INVALID_FORMAT = "aliases_invalid_format_err"
    TXT_ALIASES_INVALID_CHARACTERS = "aliases_invalid_characters_err"

    # Export / Import aliases section
    PROP_ALIASES_EXPORT_PATH = "aliases_export_path"
    BTN_ALIASES_EXPORT = "aliases_export_btn"
    PROP_ALIASES_IMPORT_PATH = "aliases_import_path"
    BTN_ALIASES_IMPORT = "aliases_import_btn"

    # Other section
    PROP_RESTART_BUFFER = "restart_buffer"
    PROP_RESTART_BUFFER_LOOP = "restart_buffer_loop"
    TXT_RESTART_BUFFER_LOOP = "restart_buffer_loop_desc"

    # Hotkeys
    HK_SAVE_BUFFER_MODE_1 = "save_buffer_force_mode_1"
    HK_SAVE_BUFFER_MODE_2 = "save_buffer_force_mode_2"
    HK_SAVE_BUFFER_MODE_3 = "save_buffer_force_mode_3"
    HK_SAVE_VIDEO_MODE_1 = "save_video_force_mode_1"
    HK_SAVE_VIDEO_MODE_2 = "save_video_force_mode_2"
    HK_SAVE_VIDEO_MODE_3 = "save_video_force_mode_3"

PN = PropertiesNames
