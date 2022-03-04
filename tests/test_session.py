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

import json

import httpx
from .test_fixtures import *


def test_token_read(api_token: str):
    assert api_token.startswith('lip_')

@pytest.mark.asyncio
async def test_token_session(token_session, api_token):
    assert token_session.token == api_token
    assert token_session.headers['Authorization'] == f'Bearer {api_token}'

@pytest.mark.asyncio
async def test_get_account(token_session, config):
    response = await token_session.get(f'{config["api_url"]}api/account')
    assert response.status_code == httpx.codes.OK
    account = json.loads(response.text)
    assert account['username'] == config['username']
