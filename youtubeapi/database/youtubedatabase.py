from pony.orm import db_session, ObjectNotFound

from pathlib import Path
from typing import Union, List, Optional

try:
	from youtubeapi import api
	from youtubeapi.database.entities import unlinked_database, ChannelEntity, PlaylistEntity, TagEntity, VideoEntity
except ModuleNotFoundError:
	from .. import api
	from .entities import unlinked_database, ChannelEntity, PlaylistEntity, TagEntity, VideoEntity

DEFAULT_DATABASE_PATH = Path(__file__).with_name("data") / "youtube_database.sqlite"
if not DEFAULT_DATABASE_PATH.parent.exists():
	DEFAULT_DATABASE_PATH.parent.mkdir()

def get_entity_class(resource_type: str)->unlinked_database.Entity:
	if resource_type == api.resource_types.channel:
		return ChannelEntity
	elif resource_type == api.resource_types.playlist:
		return PlaylistEntity
	elif resource_type == api.resource_types.video:
		return VideoEntity
	elif resource_type == 'youtube#tag':
		return TagEntity
	else:
		raise ValueError(f"Not a valid resource: '{resource_type}'")
class YoutubeDatabase:
	def __init__(self, filename: Union[str, Path] = DEFAULT_DATABASE_PATH):
		self.filename = Path(filename)  # Ensure that it is a Path object.
		self.database = unlinked_database
		self.database.bind('sqlite', filename = str(self.filename), create_db = (not self.filename.exists()))
		self.database.generate_mapping(create_tables = True)



	@db_session
	def request(self, key: str, resource_type: Optional[str] = None) -> unlinked_database.Entity:
		"""
			Attempts to retrieve an item from the database. If the item does not exist and is a 'youtube#playlist' item,
			it will be added to the database.
		Parameters
		----------
		key: str
		resource_type: Optional[str]
			If the resource type is not given or not on of the valid resource types as defined by the api,
			it will be infered using `api.infer_resource_type`.

		Returns
		-------
		Entity
		"""
		if resource_type not in api.resource_types:
			resource_type = api.infer_resource_type(key)
		resource_class = get_entity_class(resource_type)
		try:
			result = resource_class[key]
		except ObjectNotFound:
			print(f"Cannot find id '{key}' for resource type '{resource_type}'")
			result = None
		if result is None and resource_type == api.resource_types.channel:
			channel_resource = api.get(api.resource_types.channel, key)
			if channel_resource:
				result = self._add_channel_to_database(channel_resource)
		elif result is None and resource_type == api.resource_types.video:
			video_resource = api.get(api.resource_types.video, key)
			if video_resource:
				channel_entity = self.request(video_resource.channelId)
				result = self._add_video_to_database(channel_entity, video_resource)

		return result

	def import_channel(self, channel_id: str):
		""" Uses the youtube api to import a channel into the database."""
		channel_resource, upload_playlist_resource, channel_videos = api.request_channel_videos(channel_id)
		channel_playlists = api.request_channel_playlists(channel_id)
		with db_session:
			channel_entity = self._add_channel_to_database(channel_resource)
			for video_resource in channel_videos:
				self._add_video_to_database(channel_entity, video_resource)
			for channel_resource in channel_playlists:
				self._add_playlist_to_database(channel_entity, channel_resource)

	@db_session
	def _add_channel_to_database(self, channel_resource: api.ChannelResource) -> ChannelEntity:
		""" Adds a channel resource to the database as an entity. Does not add videos."""
		try:
			channel_entity = ChannelEntity[channel_resource.resourceId]
		except ObjectNotFound:
			channel_entity = ChannelEntity(
				id = channel_resource.resourceId,
				name = channel_resource.name,
				description = channel_resource.description,
				url = channel_resource.url,
				language = channel_resource.language,
				country = channel_resource.country,
				uploadPlaylist = channel_resource.uploads,
				videoCount = channel_resource.videos,
				viewCount = channel_resource.views,
				commentCount = channel_resource.comments,
				subscriberCount = channel_resource.subscribers
			)
		return channel_entity

	@db_session
	def _add_tags_to_database(self, parent_entity: Union[PlaylistEntity, VideoEntity], strings: List[str]) -> None:
		for string in strings:
			self._add_tag_to_database(parent_entity, string)

	@db_session
	def _add_tag_to_database(self, parent_entity: Union[PlaylistEntity, VideoEntity], string: str) -> TagEntity:
		try:
			tag_entity = TagEntity[string]
		except ObjectNotFound:
			tag_entity = TagEntity(value = string)
		if isinstance(parent_entity, PlaylistEntity):
			tag_entity.playlists.add(parent_entity)
		elif isinstance(parent_entity, VideoEntity):
			tag_entity.videos.add(parent_entity)
		else:
			raise ValueError(f"Not a valid parent entity: {type(parent_entity)}")
		return tag_entity

	@db_session
	def _add_video_to_database(self, channel_entity: ChannelEntity, video_resource: api.VideoResource) -> VideoEntity:
		""" Adds a video resource to the database."""
		try:
			video_entity = VideoEntity[video_resource.resourceId]
		except ObjectNotFound:
			video_entity = VideoEntity(
				id = video_resource.resourceId,
				name = video_resource.name,
				date = video_resource.date,
				description = video_resource.description,
				language = video_resource.language,
				audioLanguage = video_resource.audioLanguage,
				viewCount = video_resource.views,
				likeCount = video_resource.likes,
				dislikeCount = video_resource.dislikes,
				commentCount = video_resource.comments,
				favoriteCount = video_resource.favorites,
				duration = video_resource.duration,
				dimension = video_resource.dimension,
				definition = video_resource.definition,
				caption = video_resource.caption,
				channel = channel_entity
			)
		if video_entity:
			self._add_tags_to_database(video_entity, video_resource.tags)
		return video_entity

	@db_session
	def _add_playlist_to_database(self, channel_entity: ChannelEntity, playlist_resource: api.PlaylistResource,
								  playlist_items: List[str] = None) -> PlaylistEntity:
		if not playlist_items:
			playlist_items = api.request_playlist_item_ids(playlist_resource.resourceId)
		try:
			result = PlaylistEntity[playlist_resource.resourceId]
		except ObjectNotFound:
			result = PlaylistEntity(
				id = playlist_resource.resourceId,
				description = playlist_resource.description,
				date = playlist_resource.date,
				language = playlist_resource.language,
				channel = channel_entity,
			)
		if result:
			self._add_tags_to_database(result, playlist_resource.tags)
			for element in playlist_items:
				video_entity = self.request(element)
				if video_entity:
					result.videos.add(video_entity)
		return result


if __name__ == "__main__":
	channel_key = "UCjdQaSJCYS4o2eG93MvIwqg"
	video_key = "eqSNm6dKIYo"

	youtube_database = YoutubeDatabase()

	youtube_database.import_channel('UCboMX_UNgaPBsUOIgasn3-Q')
