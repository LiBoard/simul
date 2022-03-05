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
async def test_members(client, data):
    team = data['tests']['team']
    members = {m['username'] async for m in client.teams.get_members(team['id'])}
    assert set(team['members']) == members


@pytest.mark.asyncio
async def test_join(client, data, api_user):
    team = data['tests']['team']
    assert (await client.teams.join(team['id'])) is True
    assert api_user in {m['username'] async for m in client.teams.get_members(team['id'])}
    assert (await client.teams.leave(team['id'])) is True
    assert api_user not in {m['username'] async for m in client.teams.get_members(team['id'])}
