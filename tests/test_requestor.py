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

from berserk import models
from test_fixtures import *  #
from simul.endpoints import Endpoint
from simul.formats import PGN, LIJSON


@pytest.mark.asyncio
async def test_json(requestor, config):
    endpoint = Endpoint('api/account')
    account = await requestor.request(endpoint)
    assert account['username'] == config['username']


# TODO load username/ids from data file
@pytest.mark.asyncio
async def test_post(requestor):
    users = ['user1', 'user2', 'simul']
    ep = Endpoint('api/users', method='POST', converter=models.User.convert,
                  content=','.join(users))
    accounts = await requestor.request(ep)
    assert len(accounts) == len(users)
    for acc in accounts:
        assert acc['username'] in users


@pytest.mark.asyncio
async def test_pgn(requestor):
    id = 'V8aUuLJq'
    ep = Endpoint(f'game/export/{id}', fmt=PGN)
    game = await requestor.request(ep)
    assert "4. Nxf3 Nf6 5. Bc4 Bg4 6. Ne5 Bxd1" in game


@pytest.mark.asyncio
async def test_lijson(requestor):
    ep = Endpoint(f'player/top/10/blitz', fmt=LIJSON)
    lb = await requestor.request(ep)
    assert lb
