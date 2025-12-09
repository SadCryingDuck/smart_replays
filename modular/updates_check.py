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

from .tech import _print

from urllib.request import urlopen
import json
import traceback


def get_latest_release_tag() -> dict | None:  # todo: for future updates
    url = "https://api.github.com/repos/qvvonk/smart_replays/releases/latest"

    try:
        with urlopen(url, timeout=2) as response:
            if response.status == 200:
                data = json.load(response)
                return data.get('tag_name')
    except:
        _print(f"Failed to check updates.")
        _print(traceback.format_exc())
    return None


def check_updates(current_version: str):  # todo: for future updates
    latest_version = get_latest_release_tag()
    _print(latest_version)
    if latest_version and f'v{current_version}' != latest_version:
        return True
    return False
