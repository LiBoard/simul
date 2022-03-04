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

from . import utils


class model(type):
    @property
    def conversions(cls):
        return {k: v for k, v in vars(cls).items() if not k.startswith('_')}


class Model(metaclass=model):
    @classmethod
    def convert(cls, data):
        if isinstance(data, (list, tuple)):
            return [cls.convert_one(v) for v in data]
        return cls.convert_one(data)

    @classmethod
    def convert_one(cls, data):
        for k in set(data) & set(cls.conversions):
            data[k] = cls.conversions[k](data[k])
        return data

    @classmethod
    def convert_values(cls, data):
        for k in data:
            data[k] = cls.convert(data[k])
        return data


class Account(Model):
    createdAt = utils.datetime_from_millis
    seenAt = utils.datetime_from_millis


class User(Model):
    createdAt = utils.datetime_from_millis
    seenAt = utils.datetime_from_millis


class Activity(Model):
    interval = utils.inner(utils.datetime_from_millis,
                           'start', 'end')


class Game(Model):
    createdAt = utils.datetime_from_millis
    lastMoveAt = utils.datetime_from_millis


class GameState(Model):
    createdAt = utils.datetime_from_millis
    wtime = utils.datetime_from_millis
    btime = utils.datetime_from_millis
    winc = utils.datetime_from_millis
    binc = utils.datetime_from_millis


class Tournament(Model):
    startsAt = utils.datetime_from_str


class Tournaments(Model):
    startsAt = utils.datetime_from_millis
    finishesAt = utils.datetime_from_millis


class Broadcast(Model):
    broadcast = utils.inner(utils.datetime_from_millis,
                            'startedAt', 'startsAt')


class RatingHistory(Model):
    points = utils.listing(utils.rating_history)


class PuzzleActivity(Model):
    date = utils.datetime_from_millis
