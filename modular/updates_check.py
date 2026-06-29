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

from .globals import VARIABLES
from .tech import log

from urllib.request import urlopen
from threading import Thread
import json
import traceback


def get_latest_release_tag() -> str | None:
    url = "https://api.github.com/repos/SadCryingDuck/smart_replays/releases/latest"

    try:
        with urlopen(url, timeout=2) as response:
            if response.status == 200:
                data = json.load(response)
                return data.get('tag_name')
    except Exception:
        log.warning("Failed to check updates.")
        log.debug(traceback.format_exc())
    return None


def _parse_version(tag: str) -> tuple[int, ...]:
    parts = tag.lstrip("v").split(".")
    if not all(part.isdigit() for part in parts):
        return ()
    return tuple(int(part) for part in parts)


def check_updates(current_version: str) -> bool:
    latest_tag = get_latest_release_tag()
    log.debug(f"Latest release: {latest_tag}, current: {current_version}")
    latest = _parse_version(latest_tag or "")
    current = _parse_version(current_version)
    return bool(latest) and bool(current) and latest > current


def check_updates_in_background(current_version: str) -> None:
    Thread(target=_apply_update_check, args=(current_version,), daemon=True).start()


def _apply_update_check(current_version: str) -> None:
    VARIABLES.update_available = check_updates(current_version)
