
from datetime import timedelta, datetime
from ._custom_entities import CustomVideo
from pony.orm import *
def importEntities(db):

	#db = Database()


	class Video(db.Entity, CustomVideo):
		entity_type = 'video'
		id = PrimaryKey(str)
		name = Required(str)
		views = Required(int, size = 64)
		likes = Required(int, size = 64)
		dislikes = Required(int, size = 64)
		publishDate = Required(datetime)
		duration = Required(timedelta)
		description = Required(str)
		#retrievedDate = Optional(timedelta)
		channel = Required('Channel')
		tags = Set('Tag')
		playlists = Set('Playlist')


	class Channel(db.Entity):
		entity_type = 'channel'
		id = PrimaryKey(str)
		name = Required(str)
		videos = Set(Video)
		playlists = Set('Playlist')
		country = Optional(str)
		creationDate = Optional(datetime)
		description = Optional(str)
		subscriberCount = Optional(int, size = 64)
		videoCount = Optional(int)
		viewCount = Optional(int, size = 64)


	class Playlist(db.Entity):
		entity_type = 'playlist'
		id = PrimaryKey(str)
		name = Required(str)
		videos = Set(Video)
		channel = Required(Channel)


	class Tag(db.Entity):
		entity_type = 'tag'
		string = PrimaryKey(str)
		videos = Set(Video)



	#db.generate_mapping(create_tables = True)

	return Channel, Playlist, Tag, Video