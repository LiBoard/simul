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

from simul import models
from simul.endpoints import Endpoint, PostEndpoint, StreamEndpoint
from simul.formats import PGN, LIJSON, NDJSON
from tests.test_fixtures import *


@pytest.mark.asyncio
async def test_json(requestor, api_user):
    account = await anext(requestor.request(Endpoint('api/account')))
    assert account['username'] == api_user


@pytest.mark.asyncio
async def test_post(requestor, data):
    users = set(data['tests']['users'])
    ep = PostEndpoint('api/users', converter=models.User.convert)
    accounts = await anext(requestor.request(ep, content=','.join(users)))
    assert len(accounts) == len(users)
    assert users == {acc['username'] for acc in accounts}


@pytest.mark.asyncio
async def test_pgn(requestor, data):
    game = data['tests']['game']
    exported = await anext(requestor.request(Endpoint(f'game/export/{game["id"]}', fmt=PGN)))
    assert game['pgn-contains'] in exported


@pytest.mark.asyncio
async def test_lijson(requestor):
    lb = await anext(requestor.request(Endpoint(f'player/top/10/blitz', fmt=LIJSON)))
    assert isinstance(lb['users'][0]['username'], str)


@pytest.mark.asyncio
async def test_games_by_user(requestor, data, event_tag_re):
    conf = data['tests']['games-by-user']
    ep = StreamEndpoint(f'api/games/user/{conf["user"]}', fmt=PGN)
    lines = [line async for line in requestor.request(ep) if event_tag_re.match(line)]
    assert len(lines) >= conf['min-number']


@pytest.mark.asyncio
async def test_games_by_user_ndjson(requestor, data, game_id_re):
    conf = data['tests']['games-by-user']
    ep = StreamEndpoint(f'api/games/user/{conf["user"]}', fmt=NDJSON)
    games = [game async for game in requestor.request(ep)]
    assert len(games) >= conf['min-number']
    assert all(game_id_re.match(game['id']) for game in games)
