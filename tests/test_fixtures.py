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

from pathlib import Path

import json
import re
import pytest
import pytest_asyncio
from simul.session import Requestor
from simul.session import TokenSession
from simul.formats import JSON
from simul.clients import Client

pytest_plugins = ('pytest_asyncio',)


# region data/config
@pytest.fixture
def data():
    with open(Path(__file__).parent / 'test_data.json') as f:
        return json.load(f)


@pytest.fixture
def api_token(data):
    return data['api']['token']


@pytest.fixture
def api_url(data):
    return data['api']['url']


@pytest.fixture
def api_user(data):
    return data['api']['user']


@pytest.fixture()
def api_email(data):
    return data['api']['email']


# endregion

# region session
@pytest_asyncio.fixture
async def token_session(api_token: str):
    async with TokenSession(api_token) as ts:
        yield ts


@pytest.fixture
def requestor(token_session, data):
    return Requestor(token_session, data['api']['url'], JSON)


@pytest.fixture
def client(token_session, data):
    return Client(token_session, data['api']['url'])


# endregion

# region RegEx
@pytest.fixture
def event_tag_re():
    return re.compile(r'^\[Event ".+"]$')


@pytest.fixture
def game_id_re():
    return re.compile(r'^[A-z0-9]{8}$')

# endregion
