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


from .globals import PN, VARIABLES, ClipNamingModes
from .save_buffer import save_buffer_with_force_mode

import obspython as obs


def load_hotkeys():
    keys = (
        (PN.HK_SAVE_BUFFER_MODE_1, "[Smart Replays] Save buffer (active exe)",
         lambda pressed: save_buffer_with_force_mode(ClipNamingModes.CURRENT_PROCESS) if pressed else None),

        (PN.HK_SAVE_BUFFER_MODE_2, "[Smart Replays] Save buffer (most recorded exe)",
         lambda pressed: save_buffer_with_force_mode(ClipNamingModes.MOST_RECORDED_PROCESS) if pressed else None),

        (PN.HK_SAVE_BUFFER_MODE_3, "[Smart Replays] Save buffer (active scene)",
         lambda pressed: save_buffer_with_force_mode(ClipNamingModes.CURRENT_SCENE) if pressed else None)
    )

    for key_name, key_desc, key_callback in keys:
        key_id = obs.obs_hotkey_register_frontend(key_name, key_desc, key_callback)
        VARIABLES.hotkey_ids.update({key_name: key_id})
        key_data = obs.obs_data_get_array(VARIABLES.script_settings, key_name)
        obs.obs_hotkey_load(key_id, key_data)
        obs.obs_data_array_release(key_data)
