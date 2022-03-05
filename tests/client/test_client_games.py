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


@pytest.mark.asyncio
async def test_export(client, data):
    game = data['tests']['game']
    assert game['moves'] == (await client.games.export(game['id']))['moves']
    assert game['pgn'] == await client.games.export(game['id'], as_pgn=True)


@pytest.mark.asyncio
async def test_multi(client, data, game_id_re):
    # by player
    u = data['tests']['public-data']
    by_player_ids = [g['id'] async for g in client.games.export_by_player(u)]
    assert by_player_ids  # not empty
    assert all(game_id_re.match(g) for g in by_player_ids)

    # by id
    multi = [g['id'] async for g in client.games.export_multi(*by_player_ids)]
    assert set(multi) == set(by_player_ids)

# TODO
