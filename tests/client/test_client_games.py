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
import pytest
from httpx import ReadTimeout

from ..test_fixtures import *
from simul.utils import DEFAULT_TIMEOUT, NO_READ_TIMEOUT
from asyncio import create_task, sleep


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


@pytest.mark.asyncio
async def test_among(client, data):
    try:
        users = data['tests']['users']

        async def stream():
            async for g in client.games.get_among_players(*users):
                return g

        task = create_task(stream())
        await sleep(0.3)
        assert not task.done()
        task.cancel()
        await sleep(1)
    except RuntimeError:
        pass


@pytest.mark.asyncio
async def test_ongoing(client):
    games = await client.games.get_ongoing()
    assert isinstance(games, list)
    assert len(games) == 0


@pytest.mark.asyncio
async def test_tv_channels(client):
    channels = await client.games.get_tv_channels()
    assert isinstance(channels, dict)
