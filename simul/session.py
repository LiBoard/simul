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

"""Handles the actual communication with the API."""

from urllib.parse import urljoin

from . import utils
from httpx import AsyncClient

from .endpoints import Endpoint
from .formats import FormatHandler


class TokenSession(AsyncClient):
    """An AsyncClient using token authentication."""

    def __init__(self, token: str):
        """Intialize a new TokenSession."""
        super().__init__()
        self.token = token
        self.headers['Authorization'] = f'Bearer {token}'


class Requestor:
    """Makes the actual requests."""

    def __init__(self, session: AsyncClient, base_url: str,
                 default_fmt: FormatHandler):
        """Initialize a new Requestor."""
        self.session = session
        self.base_url = base_url
        self.default_fmt = default_fmt

    async def request(self, ep: Endpoint, *args, **kwargs):
        """Make a request to an endpoint."""
        fmt = ep.fmt or self.default_fmt
        kwargs['headers'] = fmt.headers
        url = urljoin(self.base_url, ep.path)

        if ep.stream:
            async with self.session.stream(ep.method, url, *args, **kwargs) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    yield fmt.handle(line)
        else:
            response = await self.session.request(ep.method, url, *args, **kwargs)
            response.raise_for_status()
            yield fmt.handle(response, ep.converter or utils.noop)
