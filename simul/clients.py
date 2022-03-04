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

from simul.session import Requestor
from simul.formats import *
from simul.endpoints import Endpoint
from berserk import models
from httpx import AsyncClient

API_URL = 'https://lichess.org/'


class BaseClient:
    def __init__(self, session: AsyncClient, base_url: str | None = None):
        self._r = Requestor(session, base_url or API_URL, default_fmt=JSON)


class FmtClient(BaseClient):
    """Client that can return PGN or not."""

    def __init__(self, session, base_url=None, pgn_as_default=False):
        super().__init__(session, base_url)
        self.pgn_as_default = pgn_as_default

    def _use_pgn(self, as_pgn=None):
        # helper to merge default with provided arg
        return as_pgn if as_pgn is not None else self.pgn_as_default


class Client(BaseClient):
    """Main touchpoint for the API.

    All endpoints are namespaced into the clients below:

    - :class:`account <berserk.clients.Account>` - managing account information
    - :class:`bots <berserk.clients.Bots>` - performing bot operations
    - :class:`broadcasts <berserk.clients.Broadcasts>` - getting and creating
      broadcasts
    - :class:`challenges <berserk.clients.Challenges>` - using challenges
    - :class:`games <berserk.clients.Games>` - getting and exporting games
    - :class:`simuls <berserk.clients.Simuls>` - getting simultaneous
      exhibition games
    - :class:`studies <berserk.clients.Studies>` - exporting studies
    - :class:`teams <berserk.clients.Teams>` - getting information about teams
    - :class:`tournaments <berserk.clients.Tournaments>` - getting and
      creating tournaments
    - :class:`users <berserk.clients.Users>` - getting information about users

    :param session: httpx.AsyncClient, authenticated as needed
    :param str base_url: base API URL to use (if other than the default)
    :param bool pgn_as_default: ``True`` if PGN should be the default format
                                for game exports when possible. This defaults
                                to ``False`` and is used as a fallback when
                                ``as_pgn`` is left as ``None`` for methods that
                                support it.
    """

    def __init__(self, session: AsyncClient = None, base_url=None, pgn_as_default=False):
        session = session or AsyncClient
        super().__init__(session, base_url)
        self.account = Account(session, base_url)
        self.users = Users(session, base_url)
        self.teams = Teams(session, base_url)
        self.games = Games(session, base_url, pgn_as_default=pgn_as_default)
        self.challenges = Challenges(session, base_url)
        self.board = Board(session, base_url)
        self.bots = Bots(session, base_url)
        self.tournaments = Tournaments(session, base_url,
                                       pgn_as_default=pgn_as_default)
        self.broadcasts = Broadcasts(session, base_url)
        self.simuls = Simuls(session, base_url)
        self.studies = Studies(session, base_url)


class Account(BaseClient):
    """Client for account-related endpoints."""

    async def get(self):
        """Get your public information.

        :return: public information about the authenticated user
        :rtype: dict
        """
        return await anext(
            self._r.request(Endpoint('api/account', converter=models.Account.convert)))

    async def get_email(self):
        """Get your email address.

        :return: email address of the authenticated user
        :rtype: str
        """
        return (await anext(self._r.request(Endpoint('api/account/mail'))))['email']

    async def get_preferences(self):
        """Get your account preferences.

        :return: preferences of the authenticated user
        :rtype: dict
        """
        path = 'api/account/preferences'
        return (await anext(self._r.request(Endpoint('api/account/preferences'))))['prefs']

    async def get_kid_mode(self):
        """Get your kid mode status.

        :return: current kid mode status
        :rtype: bool
        """
        return (await anext(self._r.request(Endpoint('api/account/kid'))))['kid']

    async def set_kid_mode(self, value):
        """Set your kid mode status.

        :param bool value: whether to enable or disable kid mode
        :return: success
        :rtype: bool
        """
        ep = Endpoint('api/account/kid', method='POST')
        params = {'v': value}
        return (await anext(self._r.request(ep, params=params)))['ok']

    async def upgrade_to_bot(self):
        """Upgrade your account to a bot account.

        Requires bot:play oauth scope. User cannot have any previously played
        games.

        :return: success
        :rtype: bool
        """
        return (await anext(
            self._r.request(Endpoint('api/bot/account/upgrade', method='POST'))))['ok']


class Users(BaseClient):
    """Client for user-related endpoints."""

    async def get_puzzle_activity(self, max=None):
        """Stream puzzle activity history starting with the most recent.

        :param int max: maximum number of entries to stream
        :return: puzzle activity history
        :rtype: iter
        """
        ep = Endpoint('api/user/puzzle-activity', True, fmt=NDJSON,
                      converter=models.PuzzleActivity.convert)
        params = {'max': max}
        return self._r.request(ep, params)

    async def get_realtime_statuses(self, *user_ids):
        """Get the online, playing, and streaming statuses of players.

        Only id and name fields are returned for offline users.

        :param user_ids: one or more user IDs (names)
        :return: statuses of given players
        :rtype: list
        """
        params = {'ids': ','.join(user_ids)}
        return await anext(self._r.request(Endpoint('api/users/status'), params=params))

    async def get_all_top_10(self):
        """Get the top 10 players for each speed and variant.

        :return: top 10 players in each speed and variant
        :rtype: dict
        """
        return await anext(self._r.request(Endpoint('player', fmt=LIJSON)))

    async def get_leaderboard(self, perf_type, count=10):
        """Get the leaderboard for one speed or variant.

        :param perf_type: speed or variant
        :type perf_type: :class:`~berserk.enums.PerfType`
        :param int count: number of players to get
        :return: top players for one speed or variant
        :rtype: list
        """
        ep = Endpoint(f'player/top/{count}/{perf_type}', fmt=LIJSON)
        return (await anext(self._r.request(ep)))['users']

    async def get_public_data(self, username):
        """Get the public data for a user.

        :param str username: username
        :return: public data available for the given user
        :rtype: dict
        """
        return await anext(
            self._r.request(Endpoint(f'api/user/{username}', converter=models.User.convert)))

    async def get_activity_feed(self, username):
        """Get the activity feed of a user.

        :param str username: username
        :return: activity feed of the given user
        :rtype: list
        """
        return await anext(self._r.request(
            Endpoint(f'api/user/{username}/activity', converter=models.Activity.convert)))

    async def get_by_id(self, *usernames):
        """Get multiple users by their IDs.

        :param usernames: one or more usernames
        :return: user data for the given usernames
        :rtype: list
        """
        ep = Endpoint('api/users', method='POST', converter=models.User.convert)
        return await anext(self._r.request(ep, data=','.join(usernames)))

    async def get_live_streamers(self):
        """Get basic information about currently streaming users.

        :return: users currently streaming a game
        :rtype: list
        """
        return await anext(self._r.request(Endpoint('streamer/live')))

    async def get_users_followed(self, username):
        """Stream users followed by a user.

        :param str username: a username
        :return: iterator over the users the given user follows
        :rtype: iter
        """
        ep = Endpoint(f'/api/user/{username}/following', True, fmt=NDJSON,
                      converter=models.User.convert)
        return self._r.request(ep)

    async def get_users_following(self, username):
        """Stream users who follow a user.

        :param str username: a username
        :return: iterator over the users that follow the given user
        :rtype: iter
        """
        ep = Endpoint(f'/api/user/{username}/followers', True, fmt=NDJSON,
                      converter=models.User.convert)
        return self._r.request(ep)

    async def get_rating_history(self, username):
        """Get the rating history of a user.

        :param str username: a username
        :return: rating history for all game types
        :rtype: list
        """
        ep = Endpoint(f'/api/user/{username}/rating-history',
                      converter=models.RatingHistory.convert)
        return await anext(self._r.request(ep))


class Teams(BaseClient):
    """Client for team-related endpoints."""

    async def get_members(self, team_id):
        """Get members of a team.

        :param str team_id: ID of a team
        :return: users on the given team
        :rtype: iter
        """
        ep = Endpoint(f'team/{team_id}/users', True, fmt=NDJSON, converter=models.User.convert)
        return self._r.request(ep)

    async def join(self, team_id):
        """Join a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        return (await anext(self._r.request(Endpoint(f'team/{team_id}/join', method='POST'))))['ok']

    async def leave(self, team_id):
        """Leave a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        return (await anext(self._r.request(Endpoint(f'team/{team_id}/quit', method='POST'))))['ok']

    async def kick_member(self, team_id, user_id):
        """Kick a member out of your team.

        :param str team_id: ID of a team
        :param str user_id: ID of a team member
        :return: success
        :rtype: bool
        """
        return (await anext(
            self._r.request(Endpoint(f'team/{team_id}/kick/{user_id}', method='POST'))))['ok']


class Games(FmtClient):
    """Client for games-related endpoints."""

    async def export(self, game_id, as_pgn=None, moves=None, tags=None, clocks=None,
                     evals=None, opening=None, literate=None):
        """Get one finished game as PGN or JSON.

        :param str game_id: the ID of the game to export
        :param bool as_pgn: whether to return the game in PGN format
        :param bool moves: whether to include the PGN moves
        :param bool tags: whether to include the PGN tags
        :param bool clocks: whether to include clock comments in the PGN moves
        :param bool evals: whether to include analysis evaluation comments in
                           the PGN moves when available
        :param bool opening: whether to include the opening name
        :param bool literate: whether to include literate the PGN
        :return: exported game, as JSON or PGN
        """
        ep = Endpoint(f'game/export/{game_id}', fmt=PGN if self._use_pgn(as_pgn) else JSON,
                      converter=models.Game.convert)
        params = {
            'moves': moves,
            'tags': tags,
            'clocks': clocks,
            'evals': evals,
            'opening': opening,
            'literate': literate,
        }
        return await anext(self._r.request(ep, params))

    async def export_by_player(self, username, as_pgn=None, since=None, until=None,
                               max=None, vs=None, rated=None, perf_type=None,
                               color=None, analysed=None, moves=None, tags=None,
                               evals=None, opening=None):
        """Get games by player.

        :param str username: which player's games to return
        :param bool as_pgn: whether to return the game in PGN format
        :param int since: lowerbound on the game timestamp
        :param int until: upperbound on the game timestamp
        :param int max: limit the number of games returned
        :param str vs: filter by username of the opponent
        :param bool rated: filter by game mode (``True`` for rated, ``False``
                           for casual)
        :param perf_type: filter by speed or variant
        :type perf_type: :class:`~berserk.enums.PerfType`
        :param color: filter by the color of the player
        :type color: :class:`~berserk.enums.Color`
        :param bool analysed: filter by analysis availability
        :param bool moves: whether to include the PGN moves
        :param bool tags: whether to include the PGN tags
        :param bool clocks: whether to include clock comments in the PGN moves
        :param bool evals: whether to include analysis evaluation comments in
                           the PGN moves when available
        :param bool opening: whether to include the opening name
        :param bool literate: whether to include literate the PGN
        :return: iterator over the exported games, as JSON or PGN
        """
        ep = Endpoint(f'api/games/user/{username}', True,
                      fmt=PGN if self._use_pgn(as_pgn) else NDJSON, converter=models.Game.convert)
        params = {
            'since': since,
            'until': until,
            'max': max,
            'vs': vs,
            'rated': rated,
            'perfType': perf_type,
            'color': color,
            'analysed': analysed,
            'moves': moves,
            'tags': tags,
            'evals': evals,
            'opening': opening,
        }
        return self._r.request(ep, params)

    async def export_multi(self, *game_ids, as_pgn=None, moves=None, tags=None,
                           clocks=None, evals=None, opening=None):
        """Get multiple games by ID.

        :param game_ids: one or more game IDs to export
        :param bool as_pgn: whether to return the game in PGN format
        :param bool moves: whether to include the PGN moves
        :param bool tags: whether to include the PGN tags
        :param bool clocks: whether to include clock comments in the PGN moves
        :param bool evals: whether to include analysis evaluation comments in
                           the PGN moves when available
        :param bool opening: whether to include the opening name
        :return: iterator over the exported games, as JSON or PGN
        """
        ep = Endpoint('games/export/_ids', True, 'POST', PGN if self._use_pgn(as_pgn) else NDJSON,
                      models.Game.convert)
        params = {
            'moves': moves,
            'tags': tags,
            'clocks': clocks,
            'evals': evals,
            'opening': opening,
        }
        payload = ','.join(game_ids)
        return self._r.request(ep, params=params, content=payload)

    async def get_among_players(self, *usernames):
        """Get the games currently being played among players.

        Note this will not includes games where only one player is in the given
        list of usernames.

        :param usernames: two or more usernames
        :return: iterator over all games played among the given players
        """
        ep = Endpoint('api/stream/games-by-users', True, 'POST', NDJSON, models.Game.convert)
        payload = ','.join(usernames)
        return self._r.request(ep, content=payload)

    # move this to Account?
    async def get_ongoing(self, count=10):
        """Get your currently ongoing games.

        :param int count: number of games to get
        :return: some number of currently ongoing games
        :rtype: list
        """
        path = 'api/account/playing'
        params = {'nb': count}
        return (await anext(
            self._r.request(Endpoint('api/account/playing'), params=params)))['nowPlaying']

    async def get_tv_channels(self):
        """Get basic information about the best games being played.

        :return: best ongoing games in each speed and variant
        :rtype: dict
        """
        return await anext(self._r.request(Endpoint('tv/channels')))


class Challenges(BaseClient):
    """Client for challenge-related endpoints."""

    async def create(self, username, rated, clock_limit=None, clock_increment=None,
                     days=None, color=None, variant=None, position=None):
        """Challenge another player to a game.

        :param str username: username of the player to challege
        :param bool rated: whether or not the game will be rated
        :param int clock_limit: clock initial time (in seconds)
        :param int clock_increment: clock increment (in seconds)
        :param int days: days per move (for correspondence games; omit clock)
        :param color: color of the accepting player
        :type color: :class:`~berserk.enums.Color`
        :param variant: game variant to use
        :type variant: :class:`~berserk.enums.Variant`
        :param position: custom intial position in FEN (variant must be
                         standard and the game cannot be rated)
        :type position: str
        :return: challenge data
        :rtype: dict
        """
        ep = Endpoint(f'api/challenge/{username}', method='POST',
                      converter=models.Tournament.convert)
        payload = {
            'rated': rated,
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'days': days,
            'color': color,
            'variant': variant,
            'fen': position,
        }
        return await anext(self._r.request(ep, json=payload))

    async def create_with_accept(self, username, rated, token, clock_limit=None,
                                 clock_increment=None, days=None, color=None,
                                 variant=None, position=None):
        """Start a game with another player.

        This is just like the regular challenge create except it forces the
        opponent to accept. You must provide the OAuth token of the opponent
        and it must have the challenge:write scope.

        :param str username: username of the opponent
        :param bool rated: whether or not the game will be rated
        :param str token: opponent's OAuth token
        :param int clock_limit: clock initial time (in seconds)
        :param int clock_increment: clock increment (in seconds)
        :param int days: days per move (for correspondence games; omit clock)
        :param color: color of the accepting player
        :type color: :class:`~berserk.enums.Color`
        :param variant: game variant to use
        :type variant: :class:`~berserk.enums.Variant`
        :param position: custom intial position in FEN (variant must be
                         standard and the game cannot be rated)
        :type position: :class:`~berserk.enums.Position`
        :return: game data
        :rtype: dict
        """
        ep = Endpoint(f'api/challenge/{username}', method='POST',
                      converter=models.Tournament.convert)
        payload = {
            'rated': rated,
            'acceptByToken': token,
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'days': days,
            'color': color,
            'variant': variant,
            'fen': position,
        }
        return await anext(self._r.request(ep, json=payload))

    async def create_ai(self, level=8, clock_limit=None, clock_increment=None,
                        days=None, color=None, variant=None, position=None):
        """Challenge AI to a game.

        :param int level: level of the AI (1 to 8)
        :param int clock_limit: clock initial time (in seconds)
        :param int clock_increment: clock increment (in seconds)
        :param int days: days per move (for correspondence games; omit clock)
        :param color: color of the accepting player
        :type color: :class:`~berserk.enums.Color`
        :param variant: game variant to use
        :type variant: :class:`~berserk.enums.Variant`
        :param position: use one of the custom initial positions (variant must
                         be standard and cannot be rated)
        :type position: str
        :return: success indicator
        :rtype: bool
        """
        ep = Endpoint(f'api/challenge/ai', method='POST', converter=models.Tournament.convert)
        payload = {
            'level': level,
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'days': days,
            'color': color,
            'variant': variant,
            'fen': position,
        }
        return await anext(self._r.request(ep, json=payload))

    async def create_open(self, clock_limit=None, clock_increment=None,
                          variant=None, position=None):
        """Create a challenge that any two players can join.

        :param int clock_limit: clock initial time (in seconds)
        :param int clock_increment: clock increment (in seconds)
        :param variant: game variant to use
        :type variant: :class:`~berserk.enums.Variant`
        :param position: custom intial position in FEN (variant must be
                         standard and the game cannot be rated)
        :type position: str
        :return: challenge data
        :rtype: dict
        """
        ep = Endpoint(f'api/challenge/open', method='POST', converter=models.Tournament.convert)
        payload = {
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'variant': variant,
            'fen': position,
        }
        return await anext(self._r.request(ep, json=payload))

    async def accept(self, challenge_id):
        """Accept an incoming challenge.

        :param str challenge_id: id of the challenge to accept
        :return: success indicator
        :rtype: bool
        """
        ep = Endpoint(f'api/challenge/{challenge_id}/accept', method='POST')
        return (await anext(self._r.request(ep)))['ok']

    async def decline(self, challenge_id):
        """Decline an incoming challenge.

        :param str challenge_id: id of the challenge to decline
        :return: success indicator
        :rtype: bool
        """
        ep = Endpoint(f'api/challenge/{challenge_id}/decline', method='POST')
        return (await anext(self._r.request(Endpoint)))['ok']
