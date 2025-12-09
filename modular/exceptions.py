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

class AliasParsingError(Exception):
    """
    Base exception for all alias related exceptions.
    """
    def __init__(self, index):
        """
        :param index: alias index.
        """
        super(Exception).__init__()
        self.index = index


class AliasPathAlreadyExists(AliasParsingError):
    """
    Exception raised when an alias is already exists.
    """


class AliasInvalidCharacters(AliasParsingError):
    """
    Exception raised when an alias has invalid characters.
    """


class AliasInvalidFormat(AliasParsingError):
    """
    Exception raised when an alias is invalid format.
    """
