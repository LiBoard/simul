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
async def test_create_cancel(client, data, game_id_re):
    opponent = data['tests']['public-data']
    challenge = (await client.challenges.create(opponent, True))['challenge']
    print(challenge)
    assert challenge['rated'] is True
    assert game_id_re.match(challenge['id'])
    assert await client.challenges.cancel(challenge['id']) is True

# TODO create_with_accept, create_ai, accept, decline
