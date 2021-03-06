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
async def test_get(client, api_user):
    acc = await client.account.get()
    assert acc['username'] == api_user


@pytest.mark.asyncio
async def test_email(client, api_email):
    email = await client.account.get_email()
    assert email == api_email


@pytest.mark.asyncio
async def test_preferences(client):
    prefs = await client.account.get_preferences()
    assert isinstance(prefs, dict)


@pytest.mark.asyncio
async def test_kid_mode(client):
    assert (await client.account.set_kid_mode(True)) is True
    assert (await client.account.get_kid_mode()) is True
    assert (await client.account.set_kid_mode(False)) is True
    assert (await client.account.get_kid_mode()) is False

# TODO upgrade_to_bot
