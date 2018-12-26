""" Pony implementations of the API resources."""
from pony.orm import Optional, PrimaryKey, Required, Set, Database
import datetime

unlinked_database = Database()


class ChannelEntity(unlinked_database.Entity):
	id = PrimaryKey(str)
	name = Required(str)
	description = Required(str, nullable = True)
	url = Required(str)
	language = Optional(str)
	country = Optional(str)
	uploadPlaylist = Required(str)
	videoCount = Required(int, size = 64)
	viewCount = Required(int, size = 64)
	commentCount = Required(int, size = 64)
	subscriberCount = Required(int, size = 64)
	videos = Set('VideoEntity')
	playlists = Set('PlaylistEntity')


class PlaylistEntity(unlinked_database.Entity):
	id = PrimaryKey(str)
	description = Optional(str)
	date = Required(datetime.datetime)
	language = Optional(str)

	channel = Required(ChannelEntity)
	videos = Set('VideoEntity')
	tags = Set('TagEntity')


class TagEntity(unlinked_database.Entity):
	value = PrimaryKey(str)

	playlists = Set(PlaylistEntity)
	videos = Set('VideoEntity')


class VideoEntity(unlinked_database.Entity):
	id = PrimaryKey(str)
	name = Required(str)
	date = Required(datetime.datetime)
	description = Optional(str)
	language = Optional(str)
	audioLanguage = Optional(str)
	viewCount = Required(int, size = 64)
	likeCount = Required(int, size = 64)
	dislikeCount = Required(int, size = 64)
	commentCount = Required(int, size = 64)
	favoriteCount = Required(int, size = 64)
	duration = Required(datetime.timedelta)
	dimension = Optional(str)
	definition = Optional(str)
	caption = Optional(str)

	channel = Required(ChannelEntity)
	playlists = Set(PlaylistEntity)
	tags = Set(TagEntity)
