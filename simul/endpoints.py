"""Submodule for implementing API Endpoints."""

#  Copyright (C) 2022  Philipp Leclercq
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .formats import FormatHandler
from dataclasses import dataclass
from typing import Callable


@dataclass
class Endpoint:
    """Represents an API endpoint."""

    path: str
    stream: bool = False
    method: str = 'GET'
    fmt: FormatHandler = None
    converter: Callable = None


@dataclass
class PostEndpoint(Endpoint):
    """API Endpoint accessed with POST."""

    method: str = 'POST'
