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
async def test_puzzle_activity(client):
    assert len([i async for i in client.users.get_puzzle_activity(10)]) >= 5


@pytest.mark.asyncio
async def test_realtime_status(client, data):
    for i in await client.users.get_realtime_statuses(*data['tests']['users']):
        assert isinstance(i['id'], str)


@pytest.mark.asyncio
async def test_top_10(client):
    assert 'blitz' in await client.users.get_all_top_10()


@pytest.mark.asyncio
async def test_leaderboard(client):
    assert isinstance((await client.users.get_leaderboard('blitz', 10))[0]['username'], str)


@pytest.mark.asyncio
async def test_public_data(client, data):
    u = data['tests']['public-data']
    assert (await client.users.get_public_data(u))['username'] == u


@pytest.mark.asyncio
async def test_activity_feed(client, data):
    u = data['tests']['public-data']
    assert isinstance((await client.users.get_activity_feed(u))[0]['interval'], dict)


@pytest.mark.asyncio
async def test_by_id(client, data):
    users = set(data['tests']['users'])
    assert users == {u['username'] for u in await client.users.get_by_id(*users)}


@pytest.mark.asyncio
async def test_live_streamers(client):
    live = await client.users.get_live_streamers()
    assert len(live) == 0
    assert isinstance(live, list)


@pytest.mark.asyncio
async def test_rating_history(client, data):
    u = data['tests']['public-data']
    hist = await client.users.get_rating_history(u)
    assert isinstance(hist, list)
    assert all('points' in perf for perf in hist)
