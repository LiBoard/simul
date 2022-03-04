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

from ..test_fixtures import *
from simul.endpoints import Endpoint, PostEndpoint
from simul import models
from simul.formats import *


@pytest.mark.asyncio
async def test_json(requestor, config):
    account = await Endpoint('api/account')(requestor)()
    assert account['username'] == config['username']


@pytest.mark.asyncio
async def test_post(requestor):
    users = ['user1', 'user2', 'simul']
    accounts = await PostEndpoint('api/users', converter=models.User.convert)(requestor)(
        content=','.join(users))
    assert len(accounts) == len(users)
    for acc in accounts:
        assert acc['username'] in users


@pytest.mark.asyncio
async def test_pgn(requestor):
    game_id = 'V8aUuLJq'
    game = await Endpoint(f'game/export/{game_id}', fmt=PGN)(requestor)()
    assert "4. Nxf3 Nf6 5. Bc4 Bg4 6. Ne5 Bxd1" in game


@pytest.mark.asyncio
async def test_lijson(requestor):
    lb = await Endpoint(f'player/top/10/blitz', fmt=LIJSON)(requestor)()
    assert isinstance(lb['users'][0]['username'], str)
