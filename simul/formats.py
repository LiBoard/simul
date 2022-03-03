"""Submodule for format conversions."""

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
import json
from berserk import utils


class FormatHandler:
    """Provide request headers and parse responses for a particular format.

    Instances of this class should override the :meth:`parse_stream` and
    :meth:`parse` methods to support handling both streaming and non-streaming
    responses.

    :param str mime_type: the MIME type for the format
    """

    def __init__(self, mime_type):
        """Initialize a new FormatHandler."""
        self.mime_type = mime_type
        self.headers = {'Accept': mime_type}

    def handle(self, content, converter=utils.noop):
        """Handle the response content by returning the data.

        :param content: response content
        :param func converter: function to handle field conversions
        :return: either all response data or an iterator of response data
        """
        return converter(self.parse(content))

    def parse(self, content):
        """Parse all data from a response.

        :param content: raw response
        :type content: :class:`requests.Response`
        :return: response data
        """
        return content


class JsonHandler(FormatHandler):
    """Handle JSON data.

    :param str mime_type: the MIME type for the format
    :param decoder: the decoder to use for the JSON format
    :type decoder: :class:`json.JSONDecoder`
    """

    def __init__(self, mime_type):
        """Initialize a new JsonHandler."""
        super().__init__(mime_type=mime_type)

    def parse(self, content):
        """Parse all JSON data from a response.

        :param content: raw response
        :type content: :class:`requests.Response`
        :return: response data
        :rtype: JSON
        """
        return json.loads(content)


class PgnHandler(FormatHandler):
    """Handle PGN data."""

    def __init__(self):
        """Initialize a new PgnHandler."""
        super().__init__(mime_type='application/x-chess-pgn')

    def handle(self, *args, **kwargs):
        """Handle the response content by returning the data.

        :param content: response content
        :param func converter: function to handle field conversions
        :return: either all response data or an iterator of response data
        """
        kwargs['converter'] = utils.noop  # disable conversions
        return super().handle(*args, **kwargs)


class TextHandler(FormatHandler):
    """Handle plain text."""

    def __init__(self):
        """Initialize a new TextHandler."""
        super().__init__(mime_type='text/plain')


TEXT = TextHandler()
JSON = JsonHandler(mime_type='application/json')
LIJSON = JsonHandler(mime_type='application/vnd.lichess.v3+json')
PGN = PgnHandler()
