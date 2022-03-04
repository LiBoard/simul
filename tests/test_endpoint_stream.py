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
from simul.endpoints import StreamEndpoint
from simul.formats import *


@pytest.mark.asyncio
async def test_games_by_user(requestor, event_tag_re, game_id_re):
    ep = StreamEndpoint(f'api/games/user/user1', fmt=PGN)
    count = 0
    async for line in ep(requestor)():
        if event_tag_re.match(line):
            count += 1
    assert count >= 10

    ep.fmt = NDJSON
    async for game in ep(requestor)():
        assert game_id_re.match(game['id'])
        count -= 1
    assert count == 0
