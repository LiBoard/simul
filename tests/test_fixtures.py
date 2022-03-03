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

from configparser import ConfigParser
from pathlib import Path

import pytest
import pytest_asyncio
from simul.session import Requestor
from simul.session import TokenSession

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def config() -> dict:
    c = ConfigParser()
    c.read(Path(__file__).parent / 'tests.ini')
    return c['DEFAULT']


@pytest.fixture
def api_token(config: ConfigParser) -> str:
    return config['token']


@pytest_asyncio.fixture
async def token_session(api_token: str) -> TokenSession:
    async with TokenSession(api_token) as ts:
        yield ts


@pytest.fixture
def requestor(token_session, config):
    return Requestor(token_session, config['api_url'])
