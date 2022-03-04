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

from test_fixtures import *
from simul.endpoints import Endpoint
from simul.formats import PGN, NDJSON


@pytest.mark.asyncio
async def test_games_by_user(requestor, event_tag_re):
    ep = Endpoint(f'api/games/user/user1', stream=True, fmt=PGN)
    count = 0
    async for line in requestor.request(ep):
        if event_tag_re.match(line):
            count += 1
    assert count >= 10


@pytest.mark.asyncio
async def test_games_by_user_ndjson(requestor, game_id_re):
    ep = Endpoint(f'api/games/user/user1', stream=True, fmt=NDJSON)
    count = 0
    async for game in requestor.request(ep):
        assert game_id_re.match(game['id'])
        count += 1
    assert count >= 10
