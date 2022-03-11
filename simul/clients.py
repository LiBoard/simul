"""User-facing methods to make API requests."""

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

from httpx import AsyncClient
from time import time as now

from simul import models
from simul.endpoints import Endpoint, PostEndpoint, StreamEndpoint, StreamPostEndpoint
from simul.formats import TEXT, PGN, JSON, LIJSON, NDJSON
from simul.session import Requestor
from simul.utils import NO_READ_TIMEOUT

API_URL = 'https://lichess.org/'


class _BaseClient:
    def __init__(self, session: AsyncClient, base_url: str | None = None):
        self._r = Requestor(session, base_url or API_URL, default_fmt=JSON)


class _OptionalPgnClient(_BaseClient):
    """Client that can return PGN or not."""

    def __init__(self, session, base_url=None, pgn_as_default=False):
        super().__init__(session, base_url)
        self.pgn_as_default = pgn_as_default

    def _use_pgn(self, as_pgn=None):
        # helper to merge default with provided arg
        return as_pgn if as_pgn is not None else self.pgn_as_default


class Client(_BaseClient):
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
        """Intialize a new Client."""
        super().__init__(session, base_url)
        self.account = _Account(session, base_url)
        self.users = _Users(session, base_url)
        self.teams = _Teams(session, base_url)
        self.games = _Games(session, base_url, pgn_as_default=pgn_as_default)
        self.challenges = _Challenges(session, base_url)
        self.board = _Board(session, base_url)
        self.bots = _Bots(session, base_url)
        self.tournaments = _Tournaments(session, base_url,
                                        pgn_as_default=pgn_as_default)
        self.broadcasts = _Broadcasts(session, base_url)
        self.simuls = _Simuls(session, base_url)
        self.studies = _Studies(session, base_url)


class _Account(_BaseClient):
    """Client for account-related endpoints."""

    async def get(self):
        """Get your public information.

        :return: public information about the authenticated user
        :rtype: dict
        """
        return await Endpoint('api/account', converter=models.Account.convert)(self._r)()

    async def get_email(self):
        """Get your email address.

        :return: email address of the authenticated user
        :rtype: str
        """
        return (await Endpoint('api/account/email')(self._r)())['email']

    async def get_preferences(self):
        """Get your account preferences.

        :return: preferences of the authenticated user
        :rtype: dict
        """
        return (await Endpoint('api/account/preferences')(self._r)())['prefs']

    async def get_kid_mode(self):
        """Get your kid mode status.

        :return: current kid mode status
        :rtype: bool
        """
        return (await Endpoint('api/account/kid')(self._r)())['kid']

    async def set_kid_mode(self, value):
        """Set your kid mode status.

        :param bool value: whether to enable or disable kid mode
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint('api/account/kid')(self._r)(params={'v': value}))['ok']

    async def upgrade_to_bot(self):
        """Upgrade your account to a bot account.

        Requires bot:play oauth scope. User cannot have any previously played
        games.

        :return: success
        :rtype: bool
        """
        return (await PostEndpoint('api/bot/account/upgrade')(self._r)())['ok']


class _Users(_BaseClient):
    """Client for user-related endpoints."""

    def get_puzzle_activity(self, max=None):
        """Stream puzzle activity history starting with the most recent.

        :param int max: maximum number of entries to stream
        :return: puzzle activity history
        :rtype: iter
        """
        return StreamEndpoint('api/user/puzzle-activity', fmt=NDJSON,
                              converter=models.PuzzleActivity.convert)(self._r)(
            params={'max': max})

    async def get_realtime_statuses(self, *user_ids):
        """Get the online, playing, and streaming statuses of players.

        Only id and name fields are returned for offline users.

        :param user_ids: one or more user IDs (names)
        :return: statuses of given players
        :rtype: list
        """
        return await Endpoint('api/users/status')(self._r)(params={'ids': ','.join(user_ids)})

    async def get_all_top_10(self):
        """Get the top 10 players for each speed and variant.

        :return: top 10 players in each speed and variant
        :rtype: dict
        """
        return await Endpoint('player', fmt=LIJSON)(self._r)()

    async def get_leaderboard(self, perf_type, count=10):
        """Get the leaderboard for one speed or variant.

        :param perf_type: speed or variant
        :type perf_type: :class:`~berserk.enums.PerfType`
        :param int count: number of players to get
        :return: top players for one speed or variant
        :rtype: list
        """
        return (await Endpoint(f'player/top/{count}/{perf_type}', fmt=LIJSON)(self._r)())['users']

    async def get_public_data(self, username):
        """Get the public data for a user.

        :param str username: username
        :return: public data available for the given user
        :rtype: dict
        """
        return await Endpoint(f'api/user/{username}', converter=models.User.convert)(self._r)()

    async def get_activity_feed(self, username):
        """Get the activity feed of a user.

        :param str username: username
        :return: activity feed of the given user
        :rtype: list
        """
        return await Endpoint(f'api/user/{username}/activity', converter=models.Activity.convert)(
            self._r)()

    async def get_by_id(self, *usernames):
        """Get multiple users by their IDs.

        :param usernames: one or more usernames
        :return: user data for the given usernames
        :rtype: list
        """
        return await Endpoint('api/users', method='POST', converter=models.User.convert)(self._r)(
            content=','.join(usernames))

    async def get_live_streamers(self):
        """Get basic information about currently streaming users.

        :return: users currently streaming a game
        :rtype: list
        """
        return await Endpoint('streamer/live')(self._r)()

    async def get_rating_history(self, username):
        """Get the rating history of a user.

        :param str username: a username
        :return: rating history for all game types
        :rtype: list
        """
        return await Endpoint(f'/api/user/{username}/rating-history',
                              converter=models.RatingHistory.convert)(self._r)()


class _Teams(_BaseClient):
    """Client for team-related endpoints."""

    def get_members(self, team_id):
        """Get members of a team.

        :param str team_id: ID of a team
        :return: users on the given team
        :rtype: iter
        """
        return StreamEndpoint(f'api/team/{team_id}/users', fmt=NDJSON,
                              converter=models.User.convert)(self._r)()

    async def join(self, team_id):
        """Join a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'team/{team_id}/join')(self._r)())['ok']

    async def leave(self, team_id):
        """Leave a team.

        :param str team_id: ID of a team
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'team/{team_id}/quit')(self._r)())['ok']

    async def kick_member(self, team_id, user_id):
        """Kick a member out of your team.

        :param str team_id: ID of a team
        :param str user_id: ID of a team member
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'team/{team_id}/kick/{user_id}')(self._r)())['ok']


class _Games(_OptionalPgnClient):
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
        params = {
            'moves': moves,
            'tags': tags,
            'clocks': clocks,
            'evals': evals,
            'opening': opening,
            'literate': literate,
        }
        return await Endpoint(f'game/export/{game_id}', fmt=PGN if self._use_pgn(as_pgn) else JSON,
                              converter=models.Game.convert)(self._r)(params=params)

    def export_by_player(self, username, as_pgn=None, since=None, until=None,
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
        return StreamEndpoint(f'api/games/user/{username}',
                              fmt=PGN if self._use_pgn(as_pgn) else NDJSON,
                              converter=models.Game.convert)(self._r)(params=params)

    def export_multi(self, *game_ids, as_pgn=None, moves=None, tags=None,
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
        params = {
            'moves': moves,
            'tags': tags,
            'clocks': clocks,
            'evals': evals,
            'opening': opening,
        }
        payload = ','.join(game_ids)
        return StreamPostEndpoint('games/export/_ids',
                                  fmt=PGN if self._use_pgn(as_pgn) else NDJSON,
                                  converter=models.Game.convert)(self._r)(params=params,
                                                                          content=payload)

    def get_among_players(self, *usernames, timeout=NO_READ_TIMEOUT):
        """Get the games currently being played among players.

        Note this will not includes games where only one player is in the given
        list of usernames.

        :param usernames: two or more usernames
        :param timeout: optional Timeout
        :return: iterator over all games played among the given players
        """
        payload = ','.join(usernames)
        return StreamPostEndpoint('api/stream/games-by-users', fmt=NDJSON,
                                  converter=models.Game.convert)(self._r)(content=payload,
                                                                          timeout=timeout)

    # move this to Account?
    async def get_ongoing(self, count=10):
        """Get your currently ongoing games.

        :param int count: number of games to get
        :return: some number of currently ongoing games
        :rtype: list
        """
        params = {'nb': count}
        return (await Endpoint('api/account/playing')(self._r)(params=params))['nowPlaying']

    async def get_tv_channels(self):
        """Get basic information about the best games being played.

        :return: best ongoing games in each speed and variant
        :rtype: dict
        """
        return await Endpoint('api/tv/channels')(self._r)()


class _Challenges(_BaseClient):
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
        payload = {
            'rated': rated,
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'days': days,
            'color': color,
            'variant': variant,
            'fen': position,
        }
        return await PostEndpoint(f'api/challenge/{username}',
                                  converter=models.Tournament.convert)(
            self._r)(json=payload)

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
        return await PostEndpoint(f'api/challenge/{username}',
                                  converter=models.Tournament.convert)(
            self._r)(json=payload)

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
        payload = {
            'level': level,
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'days': days,
            'color': color,
            'variant': variant,
            'fen': position,
        }
        return await PostEndpoint('api/challenge/ai', converter=models.Tournament.convert)(
            self._r)(json=payload)

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
        payload = {
            'clock.limit': clock_limit,
            'clock.increment': clock_increment,
            'variant': variant,
            'fen': position,
        }
        return await PostEndpoint('api/challenge/open', converter=models.Tournament.convert)(
            self._r)(json=payload)

    async def accept(self, challenge_id):
        """Accept an incoming challenge.

        :param str challenge_id: id of the challenge to accept
        :return: success indicator
        :rtype: bool
        """
        return (await PostEndpoint(f'api/challenge/{challenge_id}/accept')(self._r)())['ok']

    async def decline(self, challenge_id):
        """Decline an incoming challenge.

        :param str challenge_id: id of the challenge to decline
        :return: success indicator
        :rtype: bool
        """
        return (await PostEndpoint(f'api/challenge/{challenge_id}/decline')(self._r)())['ok']

    async def cancel(self, challenge_id):
        """Cancel a challenge.

        :param str challenge_id: id of the challenge to cancel
        :return: success indicator
        :rtype: bool
        """
        return (await PostEndpoint(f'api/challenge/{challenge_id}/cancel')(self._r)())['ok']


class _Board(_BaseClient):
    """Client for physical board or external application endpoints."""

    def stream_incoming_events(self):
        """Get your realtime stream of incoming events.

        :return: stream of incoming events
        """
        return StreamEndpoint('api/stream/event')(self._r)()

    async def seek(self, time, increment, rated=False, variant='standard',
                   color='random', rating_range=None):
        """Create a public seek to start a game with a random opponent.

        :param int time: intial clock time in minutes
        :param int increment: clock increment in minutes
        :param bool rated: whether the game is rated (impacts ratings)
        :param str variant: game variant to use
        :param str color: color to play
        :param rating_range: range of opponent ratings
        :return: duration of the seek
        :rtype: float
        """
        if isinstance(rating_range, (list, tuple)):
            low, high = rating_range
            rating_range = f'{low}-{high}'

        payload = {
            'rated': str(bool(rated)).lower(),
            'time': time,
            'increment': increment,
            'variant': variant,
            'color': color,
            'ratingRange': rating_range or '',
        }

        # we time the seek
        start = now()

        # just keep reading to keep the search going
        async for line in StreamPostEndpoint('api/board/seek', fmt=TEXT)(self._r)(data=payload)():
            pass

        # and return the time elapsed
        return now() - start

    def stream_game_state(self, game_id):
        """Get the stream of events for a board game.

        :param str game_id: ID of a game
        :return: iterator over game states
        """
        return StreamEndpoint(f'api/board/game/stream/{game_id}',
                              converter=models.GameState.convert)(self._r)()

    async def make_move(self, game_id, move):
        """Make a move in a board game.

        :param str game_id: ID of a game
        :param str move: move to make
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/board/game/{game_id}/move/{move}')(self._r)())['ok']

    async def post_message(self, game_id, text, spectator=False):
        """Post a message in a board game.

        :param str game_id: ID of a game
        :param str text: text of the message
        :param bool spectator: post to spectator room (else player room)
        :return: success
        :rtype: bool
        """
        payload = {'room': 'spectator' if spectator else 'player', 'text': text}
        return (await PostEndpoint(f'api/board/game/{game_id}/chat')(self._r)(json=payload))['ok']

    async def abort_game(self, game_id):
        """Abort a board game.

        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/board/game/{game_id}/abort')(self._r)())['ok']

    async def resign_game(self, game_id):
        """Resign a board game.

        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/board/game/{game_id}/resign')(self._r)())['ok']

    async def handle_draw_offer(self, game_id, accept):
        """Create, accept, or decline a draw offer.

        To offer a draw, pass ``accept=True`` and a game ID of an in-progress
        game. To response to a draw offer, pass either ``accept=True`` or
        ``accept=False`` and the ID of a game in which you have recieved a
        draw offer.

        Often, it's easier to call :func:`offer_draw`, :func:`accept_draw`, or
        :func:`decline_draw`.

        :param str game_id: ID of an in-progress game
        :param bool accept: whether to accept
        :return: True if successful
        :rtype: bool
        """
        return (await PostEndpoint(f'/api/board/game/{game_id}/draw/{"yes" if accept else "no"}')(
            self._r)())['ok']

    async def offer_draw(self, game_id):
        """Offer a draw in the given game.

        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return await self.handle_draw_offer(game_id, True)

    async def accept_draw(self, game_id):
        """Accept an already offered draw in the given game.

        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return await self.handle_draw_offer(game_id, True)

    async def decline_draw(self, game_id):
        """Decline an already offered draw in the given game.

        :param str game_id: ID of an in-progress game
        :return: True if successful
        :rtype: bool
        """
        return await self.handle_draw_offer(game_id, False)


class _Bots(_BaseClient):
    """Client for bot-related endpoints."""

    async def stream_incoming_events(self):
        """Get your realtime stream of incoming events.

        :return: stream of incoming events
        :rtype: iterator over the stream of events
        """
        return PostEndpoint('api/stream/event')(self._r)()

    def stream_game_state(self, game_id):
        """Get the stream of events for a bot game.

        :param str game_id: ID of a game
        :return: iterator over game states
        """
        return StreamEndpoint(f'api/bot/game/stream/{game_id}',
                              converter=models.GameState.convert)(
            self._r)()

    async def make_move(self, game_id, move):
        """Make a move in a bot game.

        :param str game_id: ID of a game
        :param str move: move to make
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/bot/game/{game_id}/move/{move}')(self._r)())['ok']

    async def post_message(self, game_id, text, spectator=False):
        """Post a message in a bot game.

        :param str game_id: ID of a game
        :param str text: text of the message
        :param bool spectator: post to spectator room (else player room)
        :return: success
        :rtype: bool
        """
        payload = {'room': 'spectator' if spectator else 'player', 'text': text}
        return (await PostEndpoint(f'api/bot/game/{game_id}/chat')(self._r)(json=payload))['ok']

    async def abort_game(self, game_id):
        """Abort a bot game.

        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/bot/game/{game_id}/abort')(self._r)())['ok']

    async def resign_game(self, game_id):
        """Resign a bot game.

        :param str game_id: ID of a game
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/bot/game/{game_id}/resign')(self._r)())['ok']

    async def accept_challenge(self, challenge_id):
        """Accept an incoming challenge.

        :param str challenge_id: ID of a challenge
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/challenge/{challenge_id}/accept')(self._r)())['ok']

    async def decline_challenge(self, challenge_id):
        """Decline an incoming challenge.

        :param str challenge_id: ID of a challenge
        :return: success
        :rtype: bool
        """
        return (await PostEndpoint(f'api/challenge/{challenge_id}/decline')(self._r)())['ok']


class _Tournaments(_OptionalPgnClient):
    """Client for tournament-related endpoints."""

    async def get(self):
        """Get recently finished, ongoing, and upcoming tournaments.

        :return: current tournaments
        :rtype: list
        """
        return await Endpoint('api/tournament', converter=models.Tournament.convert_values)(
            self._r)()

    async def create(self, clock_time, clock_increment, minutes, name=None,
                     wait_minutes=None, variant=None, berserkable=None, rated=None,
                     start_date=None, position=None, password=None, conditions=None):
        """Create a new tournament.

        .. note::

            ``wait_minutes`` is always relative to now and is overriden by
            ``start_time``.

        .. note::

            If ``name`` is left blank then one is automatically created.

        :param int clock_time: intial clock time in minutes
        :param int clock_increment: clock increment in seconds
        :param int minutes: length of the tournament in minutes
        :param str name: tournament name
        :param int wait_minutes: future start time in minutes
        :param str start_date: when to start the tournament
        :param str variant: variant to use if other than standard
        :param bool rated: whether the game affects player ratings
        :param str berserkable: whether players can use berserk
        :param str position: custom initial position in FEN
        :param str password: password (makes the tournament private)
        :param dict conditions: conditions for participation
        :return: created tournament info
        :rtype: dict
        """
        payload = {
            'name': name,
            'clockTime': clock_time,
            'clockIncrement': clock_increment,
            'minutes': minutes,
            'waitMinutes': wait_minutes,
            'startDate': start_date,
            'variant': variant,
            'rated': rated,
            'position': position,
            'berserkable': berserkable,
            'password': password,
            **{f'conditions.{c}': v for c, v in (conditions or {}).items()},
        }
        return await PostEndpoint('api/tournament', converter=models.Tournament.convert)(self._r)(
            json=payload)

    async def export_games(self, id_, as_pgn=False, moves=None, tags=None,
                           clocks=None, evals=None, opening=None):
        """Export games from a tournament.

        :param str id_: tournament ID
        :param bool as_pgn: whether to return PGN instead of JSON
        :param bool moves: include moves
        :param bool tags: include tags
        :param bool clocks: include clock comments in the PGN moves, when
                            available
        :param bool evals: include analysis evalulation comments in the PGN
                           moves, when available
        :param bool opening: include the opening name
        :return: games
        :rtype: list
        """
        params = {
            'moves': moves,
            'tags': tags,
            'clocks': clocks,
            'evals': evals,
            'opening': opening,
        }
        fmt = PGN if self._use_pgn(as_pgn) else NDJSON
        return await Endpoint(f'api/tournament/{id_}/games', fmt=fmt,
                              converter=models.Game.convert)(
            self._r)(params=params)

    def stream_results(self, id_, limit=None):
        """Stream the results of a tournament.

        Results are the players of a tournament with their scores and
        performance in rank order. Note that results for ongoing
        tournaments can be inconsistent due to ranking changes.

        :param str id_: tournament ID
        :param int limit: maximum number of results to stream
        :return: iterator over the stream of results
        :rtype: iter
        """
        return StreamEndpoint(f'api/tournament/{id_}/results')(self._r)(params={'nb': limit})

    def stream_by_creator(self, username):
        """Stream the tournaments created by a player.

        :param str username: username of the player
        :return: tournaments
        :rtype: iter
        """
        return StreamEndpoint(f'api/user/{username}/tournament/created')(self._r)()


class _Broadcasts(_BaseClient):
    """Broadcast of one or more games."""

    async def create(self, name, description, sync_url=None, markdown=None,
                     credit=None, starts_at=None, official=None, throttle=None):
        """Create a new broadcast.

        .. note::

            ``sync_url`` must be publicly accessible. If not provided, you
            must periodically push new PGN to update the broadcast manually.

        :param str name: name of the broadcast
        :param str description: short description
        :param str markdown: long description
        :param str sync_url: URL by which Lichess can poll for updates
        :param str credit: short text to give credit to the source provider
        :param int starts_at: start time as millis
        :param bool official: DO NOT USE
        :param int throttle: DO NOT USE
        :return: created tournament info
        :rtype: dict
        """
        payload = {
            'name': name,
            'description': description,
            'syncUrl': sync_url,
            'markdown': markdown,
            'credit': credit,
            'startsAt': starts_at,
            'official': official,
            'throttle': throttle,
        }
        return await PostEndpoint('broadcast/new', converter=models.Broadcast.convert)(self._r)(
            json=payload)

    async def get(self, broadcast_id, slug='-'):
        """Get a broadcast by ID.

        :param str broadcast_id: ID of a broadcast
        :param str slug: slug for SEO
        :return: broadcast information
        :rtype: dict
        """
        return await Endpoint(f'broadcast/{slug}/{broadcast_id}',
                              converter=models.Broadcast.convert)(self._r)()

    async def update(self, broadcast_id, name, description, sync_url, markdown=None,
                     credit=None, starts_at=None, official=None, throttle=None,
                     slug='-'):
        """Update an existing broadcast by ID.

        .. note::

            Provide all fields. Values in missing fields will be erased.

        :param str broadcast_id: ID of a broadcast
        :param str name: name of the broadcast
        :param str description: short description
        :param str sync_url: URL by which Lichess can poll for updates
        :param str markdown: long description
        :param str credit: short text to give credit to the source provider
        :param int starts_at: start time as millis
        :param bool official: DO NOT USE
        :param int throttle: DO NOT USE
        :param str slug: slug for SEO
        :return: updated broadcast information
        :rtype: dict
        """
        payload = {
            'name': name,
            'description': description,
            'syncUrl': sync_url,
            'markdown': markdown,
            'credit': credit,
            'startsAt': starts_at,
            'official': official,

        }
        return PostEndpoint(f'broadcast/{slug}/{broadcast_id}',
                            converter=models.Broadcast.convert)(
            self._r)(json=payload)

    async def push_pgn_update(self, broadcast_id, pgn_games, slug='-'):
        """Manually update an existing broadcast by ID.

        :param str broadcast_id: ID of a broadcast
        :param list pgn_games: one or more games in PGN format
        :return: success
        :rtype: bool
        """
        games = '\n\n'.join(g.strip() for g in pgn_games)
        return (await PostEndpoint(f'broadcast/{slug}/{broadcast_id}/push')(self._r)(data=games))[
            'ok']


class _Simuls(_BaseClient):
    """Simultaneous exhibitions - one vs many."""

    async def get(self):
        """Get recently finished, ongoing, and upcoming simuls.

        :return: current simuls
        :rtype: list
        """
        return await Endpoint('api/simul')(self._r)()


class _Studies(_BaseClient):
    """Study chess the Lichess way."""

    async def export_chapter(self, study_id, chapter_id):
        """Export one chapter of a study.

        :return: chapter
        :rtype: PGN
        """
        return await Endpoint(f'/study/{study_id}/{chapter_id}.pgn', fmt=PGN)(self._r)()

    def export(self, study_id):
        """Export all chapters of a study.

        :return: all chapters as PGN
        :rtype: list
        """
        return StreamEndpoint(f'/study/{study_id}.pgn', fmt=PGN)(self._r)()
