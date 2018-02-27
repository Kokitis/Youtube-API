from datetime import timedelta, datetime
from pony.orm import *
from typing import Dict, Union


def importEntities(db: Database) -> Dict:
	class Video(db.Entity):
		entity_type = 'youtube#video'
		resourceId = PrimaryKey(str)
		itemId = Required(str)
		itemType = Required(str)
		videoName = Required(str)
		videoViewCount = Optional(int, size = 64)
		videoLikeCount = Optional(int, size = 64, sql_default = 0)
		videoDislikeCount = Optional(int, size = 64, sql_default = 0)
		videoCommentCount = Optional(int, size = 64, sql_default = 0)
		videoFavoriteCount = Optional(int, size = 64, sql_default = 0)

		videoDescription = Optional(str)
		videoCaption = Optional(bool)
		videoLanguage = Optional(str)
		videoAudioLanguage = Optional(str)
		videoCategoryId = Optional(int)
		videoDate = Required(datetime)
		videoDuration = Required(timedelta)
		videoDefinition = Optional(str)
		videoDimension = Optional(str)

		channel = Required('Channel')
		tags = Set('Tag')
		playlistItems = Set('PlaylistItem')

		def toDict(self):
			data = self.to_dict()
			data['channelId'] = self.channel.resourceId
			data['channelName'] = self.channel.channelName
			data['itemType'] = 'youtube#video'
			data['videoTags'] = [i.string for i in self.tags]

			return data

	class Channel(db.Entity):
		entity_type = 'youtube#channel'
		resourceId = PrimaryKey(str)
		itemType = Required(str)
		itemId = Required(str)
		channelName = Required(str)
		channelDescription = Optional(str)
		channelUrl = Optional(str)
		channelLanguage = Optional(str)
		channelCountry = Optional(str)

		channelUploadPlaylist = Required(str)

		channelViewCount = Required(int, size = 64, sql_default = 0)
		channelCommentCount = Required(int, size = 64, sql_default = 0)
		channelSubscriberCount = Required(int, size = 64, sql_default = 0)
		channelVideoCount = Required(int, size = 64, sql_default = 0)

		tags = Set('Tag')
		video = Set(Video)
		playlists = Set('Playlist')

		def toDict(self):
			data = self.to_dict()
			data['itemType'] = 'youtube#channel'

			return data

	class Playlist(db.Entity):
		entity_type = 'youtube#playlist'
		resourceId = PrimaryKey(str)
		itemType = Required(str)
		itemId = Required(str)
		playlistDate = Required(datetime)
		playlistName = Required(str)
		playlistDescription = Optional(str)
		playlistLanguage = Optional(str)

		playlistItems = Set('PlaylistItem')
		channel = Set(Channel)
		tags = Set('Tag')

		def toDict(self):
			data = self.to_dict()
			data['itemType'] = 'youtube#playlist'
			return data

	class PlaylistItem(db.Entity):
		entity_type = '#youtube#playlistItem'
		resourceId = PrimaryKey(str)
		itemId = Required(str)
		itemType = Required(str)

		playlistItemDate = Required(datetime)
		playlistItemName = Required(str)
		playlistItemDescription = Optional(str)
		playlistItemPosition = Optional(int)

		playlist = Required(Playlist)
		video = Required(Video)
		def toDict(self):
			data = self.to_dict()
			data['itemType'] = 'youtube#playlistItem'
			return data

	class Tag(db.Entity):
		entity_type = 'youtube#tag'
		string = PrimaryKey(str)
		videos = Set(Video)
		channels = Set(Channel)
		playlists = Set(Playlist)

		def toDict(self):
			data = self.to_dict()
			data['itemType'] = 'youtube#Tag'
			return data

	Entities = Union[Channel, Playlist, PlaylistItem, Video, Tag]

	# db.generate_mapping(create_tables = True)
	entities: Dict[str, Entities] = {
		'channel':      Channel,
		'playlist':     Playlist,
		'playlistItem': PlaylistItem,
		'video':        Video,
		'tag':          Tag
	}
	return entities
