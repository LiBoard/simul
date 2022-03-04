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
    c = 0
    async for i in client.users.get_puzzle_activity(10):
        c += 1
    assert c >= 5


@pytest.mark.asyncio
async def test_realtime_status(client):
    users = ['user1', 'user2', 'simul']
    for i in await client.users.get_realtime_statuses(*users):
        assert i['id']


@pytest.mark.asyncio
async def test_top_10(client):
    assert 'blitz' in await client.users.get_all_top_10()


@pytest.mark.asyncio
async def test_leaderboard(client):
    assert (await client.users.get_leaderboard('blitz', 10))[0]['username']


@pytest.mark.asyncio
async def test_public_data(client):
    assert (await client.users.get_public_data('user1'))['username'] == 'user1'


@pytest.mark.asyncio
async def test_activity_feed(client):
    assert (await client.users.get_activity_feed('user1'))[0]['interval']


@pytest.mark.asyncio
async def test_by_id(client):
    users = ['user1', 'user2', 'simul']
    for u in await client.users.get_by_id(*users):
        assert u['username'] in users


@pytest.mark.asyncio
async def test_live_streamers(client):
    assert len(await client.users.get_live_streamers()) == 0


@pytest.mark.asyncio
async def test_rating_history(client):
    hist = await client.users.get_rating_history('user1')
    for perf in hist:
        assert 'points' in perf
