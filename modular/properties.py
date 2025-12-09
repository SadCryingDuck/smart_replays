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

from .globals import VARIABLES, PN, ClipNamingModes, VideoNamingModes, PopupPathDisplayModes
from .properties_callbacks import (open_github_callback,
                                   update_notifications_menu_callback,
                                   import_aliases_from_json_callback,
                                   export_aliases_to_json_callback,
                                   check_base_path_callback,
                                   check_filename_template_callback,
                                   update_aliases_callback,
                                   update_links_path_prop_visibility,
                                   check_clips_links_folder_path_callback)
from .obs_related import get_base_path

import obspython as obs
import sys


variables_tip = """<table>
<tr><th align='left'>%NAME</th><td> - name of the clip.</td></tr>

<tr><th align='left'>%a</th><td> - Weekday as locale’s abbreviated name.<br/>
Example: Sun, Mon, …, Sat (en_US); So, Mo, …, Sa (de_DE)</td></tr>

<tr><th align='left'>%A</th><td> - Weekday as locale’s full name.<br/>
Example: Sunday, Monday, …, Saturday (en_US); Sonntag, Montag, …, Samstag (de_DE)</td></tr>

<tr><th align='left'>%w</th><td> - Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.<br/>
Example: 0, 1, …, 6</td></tr>

<tr><th align='left'>%d</th><td> - Day of the month as a zero-padded decimal number.<br/>
Example: 01, 02, …, 31</td></tr>

<tr><th align='left'>%b</th><td> - Month as locale’s abbreviated name.<br/>
Example: Jan, Feb, …, Dec (en_US); Jan, Feb, …, Dez (de_DE)</td></tr>

<tr><th align='left'>%B</th><td> - Month as locale’s full name.<br/>
Example: January, February, …, December (en_US); Januar, Februar, …, Dezember (de_DE)</td></tr>

<tr><th align='left'>%m</th><td> - Month as a zero-padded decimal number.<br/>
Example: 01, 02, …, 12</td></tr>

<tr><th align='left'>%y</th><td> - Year without century as a zero-padded decimal number.<br/>
Example: 00, 01, …, 99</td></tr>

<tr><th align='left'>%Y</th><td> - Year with century as a decimal number.<br/>
Example: 0001, 0002, …, 2013, 2014, …, 9998, 9999</td></tr>

<tr><th align='left'>%H</th><td> - Hour (24-hour clock) as a zero-padded decimal number.<br/>
Example: 00, 01, …, 23</td></tr>

<tr><th align='left'>%I</th><td> - Hour (12-hour clock) as a zero-padded decimal number.<br/>
Example: 01, 02, …, 12</td></tr>

<tr><th align='left'>%p</th><td> - Locale’s equivalent of either AM or PM.<br/>
Example: AM, PM (en_US); am, pm (de_DE)</td></tr>

<tr><th align='left'>%M</th><td> - Minute as a zero-padded decimal number.<br/>
Example: 00, 01, …, 59</td></tr>

<tr><th align='left'>%S</th><td> - Second as a zero-padded decimal number.<br/>
Example: 00, 01, …, 59</td></tr>

<tr><th align='left'>%f</th><td> - Microsecond as a decimal number, zero-padded to 6 digits.<br/>
Example: 000000, 000001, …, 999999</td></tr>

<tr><th align='left'>%z</th><td> - UTC offset in the form ±HHMM[SS[.ffffff]]<br/>
Example: +0000, -0400, +1030, +063415, -030712.345216</td></tr>

<tr><th align='left'>%Z</th><td> - Time zone name<br/>
Example: UTC, GMT</td></tr>

<tr><th align='left'>%j</th><td> - Day of the year as a zero-padded decimal number.<br/>
Example: 001, 002, …, 366</td></tr>

<tr><th align='left'>%U</th><td> - Week number of the year (Sunday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Sunday are considered to be in week 0.<br/>
Example: 00, 01, …, 53</td></tr>

<tr><th align='left'>%W</th><td> - Week number of the year (Monday as the first day of the week) as a zero-padded decimal number. All days in a new year preceding the first Monday are considered to be in week 0.<br/>
Example: 00, 01, …, 53</td></tr>

<tr><th align='left'>%%</th><td> - A literal '%' character.</td></tr>
</table>"""


def setup_clip_paths_settings(group_obj):
    # ----- Clips base path -----
    base_path_prop = obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_CLIPS_BASE_PATH,
        description="Base path for clips",
        type=obs.OBS_PATH_DIRECTORY,
        filter=None,
        default_path=str(get_base_path())
    )

    t = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_CLIPS_BASE_PATH_WARNING,
        description="The path must be on the same disk as the path for OBS records "
                    "(File -> Settings -> Output -> Recording -> Recording Path).\n"
                    "Otherwise, the script will not be able to move the clip to the correct folder.",
        type=obs.OBS_TEXT_INFO
    )

    obs.obs_property_text_set_info_type(t, obs.OBS_TEXT_INFO_WARNING)

    # ----- Clip naming mode -----
    clip_naming_mode_prop = obs.obs_properties_add_list(
        props=group_obj,
        name=PN.PROP_CLIPS_NAMING_MODE,
        description="Clip name based on",
        type=obs.OBS_COMBO_TYPE_RADIO,
        format=obs.OBS_COMBO_FORMAT_INT
    )
    obs.obs_property_list_add_int(
        p=clip_naming_mode_prop,
        name="the name of an active app (.exe file name) at the moment of clip saving;",
        val=ClipNamingModes.CURRENT_PROCESS.value
    )
    obs.obs_property_list_add_int(
        p=clip_naming_mode_prop,
        name="the name of an app (.exe file name) that was active most of the time during the clip recording;",
        val=ClipNamingModes.MOST_RECORDED_PROCESS.value
    )
    obs.obs_property_list_add_int(
        p=clip_naming_mode_prop,
        name="the name of the current scene;",
        val=ClipNamingModes.CURRENT_SCENE.value
    )

    t = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_CLIPS_HOTKEY_TIP,
        description="You can set up hotkeys for each mode in File -> Settings -> Hotkeys",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_text_set_info_type(t, obs.OBS_TEXT_INFO_WARNING)

    # ----- Clip file name format -----
    filename_format_prop = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.PROP_CLIPS_FILENAME_TEMPLATE,
        description="File name format",
        type=obs.OBS_TEXT_DEFAULT
    )
    obs.obs_property_set_long_description(
        filename_format_prop,
        variables_tip)

    t = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_CLIPS_FILENAME_TEMPLATE_ERR,
        description="<font color=\"red\"><pre> Invalid format!</pre></font>",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_set_visible(t, False)

    # ----- Save to folders checkbox -----
    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_CLIPS_SAVE_TO_FOLDER,
        description="Sort clips into folders by application or scene",
    )

    # ----- Create links -----
    create_links_prop = obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_CLIPS_CREATE_LINKS,
        description="Create hard links for clips",
    )

    links_path_prop = obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_CLIPS_LINKS_FOLDER_PATH,
        description="Links folder",
        type=obs.OBS_PATH_DIRECTORY,
        filter=None,
        default_path=str(get_base_path())
    )
    links_path_warn = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_CLIPS_LINKS_FOLDER_PATH_WARNING,
        description="The path must be on the same disk as the path for OBS records "
                    "(File -> Settings -> Output -> Recording -> Recording Path).\n"
                    "Otherwise, the script will not be able to create link to the file.",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_text_set_info_type(links_path_warn, obs.OBS_TEXT_INFO_WARNING)

    obs.obs_property_set_visible(links_path_prop,
                                 obs.obs_data_get_bool(VARIABLES.script_settings,
                                                       PN.PROP_CLIPS_CREATE_LINKS))
    obs.obs_property_set_visible(links_path_warn,
                                 obs.obs_data_get_bool(VARIABLES.script_settings,
                                                       PN.PROP_CLIPS_CREATE_LINKS))

    # ----- Callbacks -----
    obs.obs_property_set_modified_callback(base_path_prop, check_base_path_callback)
    obs.obs_property_set_modified_callback(filename_format_prop, check_filename_template_callback)
    obs.obs_property_set_modified_callback(create_links_prop, update_links_path_prop_visibility)
    obs.obs_property_set_modified_callback(links_path_prop, check_clips_links_folder_path_callback)


def setup_video_paths_settings(group_obj):
    # ----- Video name condition -----
    filename_condition = obs.obs_properties_add_list(
        props=group_obj,
        name=PN.PROP_VIDEOS_NAMING_MODE,
        description="Video name based on",
        type=obs.OBS_COMBO_TYPE_RADIO,
        format=obs.OBS_COMBO_FORMAT_INT
    )
    obs.obs_property_list_add_int(
        p=filename_condition,
        name="the name of an active app (.exe file name) at the moment of video saving",
        val=1
    )
    obs.obs_property_list_add_int(
        p=filename_condition,
        name="the name of an app (.exe file name) that was active most of the time during the video recording",
        val=2
    )
    obs.obs_property_list_add_int(
        p=filename_condition,
        name="the name of the current scene",
        val=3
    )

    t = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_VIDEOS_HOTKEY_TIP,
        description="You can set up hotkeys for each mode in File -> Settings -> Hotkeys",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_text_set_info_type(t, obs.OBS_TEXT_INFO_WARNING)

    # ----- Video file name format -----
    filename_format_prop = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.PROP_VIDEOS_FILENAME_FORMAT,
        description="File name format",
        type=obs.OBS_TEXT_DEFAULT
    )
    obs.obs_property_set_long_description(
        filename_format_prop,
        variables_tip)

    t = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_VIDEOS_FILENAME_FORMAT_ERR,
        description="<font color=\"red\"><pre> Invalid format!</pre></font>",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_set_visible(t, False)

    # ----- Save to folders checkbox -----
    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_VIDEOS_SAVE_TO_FOLDER,
        description="Create different folders for different video names",
    )

    # ----- Rename only if force mode -----
    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_VIDEOS_ONLY_FORCE_MODE,
        description="Rename and move the video only if it was saved using the script's hotkeys"
    )


def setup_notifications_settings(group_obj):
    notification_success_prop = obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_NOTIFY_CLIPS_ON_SUCCESS,
        description="On success"
    )
    success_path_prop = obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_NOTIFY_CLIPS_ON_SUCCESS_PATH,
        description="",
        type=obs.OBS_PATH_FILE,
        filter=None,
        default_path="C:\\"
    )

    notification_failure_prop = obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_NOTIFY_CLIPS_ON_FAILURE,
        description="On failure"
    )
    failure_path_prop = obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_NOTIFY_CLIPS_ON_FAILURE_PATH,
        description="",
        type=obs.OBS_PATH_FILE,
        filter=None,
        default_path="C:\\"
    )

    obs.obs_property_set_visible(success_path_prop,
                                 obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_SUCCESS))
    obs.obs_property_set_visible(failure_path_prop,
                                 obs.obs_data_get_bool(VARIABLES.script_settings, PN.PROP_NOTIFY_CLIPS_ON_FAILURE))

    # ----- Callbacks ------
    obs.obs_property_set_modified_callback(notification_success_prop, update_notifications_menu_callback)
    obs.obs_property_set_modified_callback(notification_failure_prop, update_notifications_menu_callback)


def setup_popup_notification_settings(group_obj):
    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_POPUP_CLIPS_ON_SUCCESS,
        description="On success"
    )

    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_POPUP_CLIPS_ON_FAILURE,
        description="On failure"
    )

    popup_path_type = obs.obs_properties_add_list(
        props=group_obj,
        name=PN.PROP_POPUP_PATH_DISPLAY_MODE,
        description="Show",
        type=obs.OBS_COMBO_TYPE_RADIO,
        format=obs.OBS_COMBO_FORMAT_INT
    )
    obs.obs_property_list_add_int(
        p=popup_path_type,
        name="full path",
        val=PopupPathDisplayModes.FULL_PATH.value
    )
    obs.obs_property_list_add_int(
        p=popup_path_type,
        name="folder and file name",
        val=PopupPathDisplayModes.FOLDER_AND_FILE.value
    )
    obs.obs_property_list_add_int(
        p=popup_path_type,
        name="just folder",
        val=PopupPathDisplayModes.JUST_FOLDER.value
    )

    obs.obs_property_list_add_int(
        p=popup_path_type,
        name="just file name",
        val=PopupPathDisplayModes.JUST_FILE.value
    )


def setup_aliases_settings(group_obj):
    obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_ALIASES_DESC,
        description="Executable (.exe) files often have names that don't match the actual game title "
                    "(e.g., the game is called Deadlock, but the .exe file is named project8.exe)."
                    "You can create an alias for the executable file or folder. "
                    "Smart Replays will use this alias for renaming, rather than the .exe file name.",
        type=obs.OBS_TEXT_INFO
    )

    err_text_1 = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_ALIASES_INVALID_CHARACTERS,
        description="""
    <div style="font-size: 14px">
    <span style="color: red">Invalid path or clip name value.<br></span>
    <span style="color: orange">Clip name cannot contain <code style="color: cyan">&lt; &gt; / \\ | * ? : " %</code> characters.<br>
    Path cannot contain <code style="color: cyan">&lt; &gt; | * ? " %</code> characters.</span>
    </div>
    """,
        type=obs.OBS_TEXT_INFO
    )

    err_text_2 = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_ALIASES_PATH_EXISTS,
        description="""<div style="font-size: 14px; color: red">This path has already been added to the list.</div>""",
        type=obs.OBS_TEXT_INFO
    )

    err_text_3 = obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_ALIASES_INVALID_FORMAT,
        description="""
    <div style="font-size: 14px">
    <span style="color: red">Invalid format.<br></span>
    <span style="color: orange">Required format: DISK:\\path\\to\\folder\\or\\executable > ClipName<br></span>
    <span style="color: lightgreen">Example: C:\\Program Files\\Minecraft > Minecraft</span>
    </div>""",
        type=obs.OBS_TEXT_INFO
    )

    obs.obs_property_set_visible(err_text_1, False)
    obs.obs_property_set_visible(err_text_2, False)
    obs.obs_property_set_visible(err_text_3, False)

    aliases_list = obs.obs_properties_add_editable_list(
        props=group_obj,
        name=PN.PROP_ALIASES_LIST,
        description="",
        type=obs.OBS_EDITABLE_LIST_TYPE_STRINGS,
        filter=None,
        default_path=None
    )

    t = obs.obs_properties_add_text(
        props=group_obj,
        name="temp",
        description="Format:  DISK:\\path\\to\\folder\\or\\executable > ClipName\n"
                    f"Example: {sys.executable} > OBS",
        type=obs.OBS_TEXT_INFO
    )
    obs.obs_property_text_set_info_type(t, obs.OBS_TEXT_INFO_WARNING)

    obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_ALIASES_IMPORT_PATH,
        description="",
        type=obs.OBS_PATH_FILE,
        filter=None,
        default_path="C:\\"
    )

    obs.obs_properties_add_button(
        group_obj,
        PN.BTN_ALIASES_IMPORT,
        "Import aliases",
        import_aliases_from_json_callback,
    )

    obs.obs_properties_add_path(
        props=group_obj,
        name=PN.PROP_ALIASES_EXPORT_PATH,
        description="",
        type=obs.OBS_PATH_DIRECTORY,
        filter=None,
        default_path="C:\\"
    )

    obs.obs_properties_add_button(
        group_obj,
        PN.BTN_ALIASES_EXPORT,
        "Export aliases",
        export_aliases_to_json_callback,
    )

    # ----- Callbacks -----
    obs.obs_property_set_modified_callback(aliases_list, update_aliases_callback)


def setup_other_settings(group_obj):
    obs.obs_properties_add_text(
        props=group_obj,
        name=PN.TXT_RESTART_BUFFER_LOOP,
        description="""If replay buffering runs too long without a restart, saving clips may become slow, and bugs can occur (thanks, OBS).
It's recommended to restart it every 1-2 hours (3600-7200 seconds). Before restarting, the script checks OBS's max clip length and detects keyboard or mouse input. If input is detected, the restart is delayed by the max clip length; otherwise, it proceeds immediately.
To disable scheduled restarts, set the value to 0.""",
        type=obs.OBS_TEXT_INFO
    )

    obs.obs_properties_add_int(
        props=group_obj,
        name=PN.PROP_RESTART_BUFFER_LOOP,
        description="Restart every (s)",
        min=0, max=7200,
        step=10
    )

    obs.obs_properties_add_bool(
        props=group_obj,
        name=PN.PROP_RESTART_BUFFER,
        description="Restart replay buffer after clip saving"
    )


def script_properties():
    p = obs.obs_properties_create()  # main properties object

    # ----- Ungrouped properties -----
    # Updates text
    t = obs.obs_properties_add_text(p, 'check_updates', 'New update available', obs.OBS_TEXT_INFO)
    obs.obs_property_set_visible(t, VARIABLES.update_available)

    # Like btn
    obs.obs_properties_add_button(
        p,
        "like_btn",
        "🌟 Like this script? Star it! 🌟",
        open_github_callback
    )

    # ----- Groups -----
    clip_path_gr = obs.obs_properties_create()
    # video_path_gr = obs.obs_properties_create()  # todo: for future updates
    notification_gr = obs.obs_properties_create()
    popup_gr = obs.obs_properties_create()
    aliases_gr = obs.obs_properties_create()
    other_gr = obs.obs_properties_create()

    obs.obs_properties_add_group(p, PN.GR_CLIPS_PATH_SETTINGS, "Clip path settings", obs.OBS_GROUP_NORMAL, clip_path_gr)
    # obs.obs_properties_add_group(p, PN.GR_VIDEOS_PATH_SETTINGS, "Video path settings", obs.OBS_GROUP_NORMAL, video_path_gr)   # todo: for future updates
    obs.obs_properties_add_group(p, PN.GR_SOUND_NOTIFICATION_SETTINGS, "Sound notifications", obs.OBS_GROUP_CHECKABLE, notification_gr)
    obs.obs_properties_add_group(p, PN.GR_POPUP_NOTIFICATION_SETTINGS, "Popup notifications", obs.OBS_GROUP_CHECKABLE, popup_gr)
    obs.obs_properties_add_group(p, PN.GR_ALIASES_SETTINGS, "Aliases", obs.OBS_GROUP_NORMAL, aliases_gr)
    obs.obs_properties_add_group(p, PN.GR_OTHER_SETTINGS, "Other", obs.OBS_GROUP_NORMAL, other_gr)

    # ------ Setup properties ------
    setup_clip_paths_settings(clip_path_gr)
    # setup_video_paths_settings(video_path_gr)   # todo: for future updates
    setup_notifications_settings(notification_gr)
    setup_popup_notification_settings(popup_gr)
    setup_aliases_settings(aliases_gr)
    setup_other_settings(other_gr)

    return p