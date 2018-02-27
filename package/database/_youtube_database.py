import os
from pprint import pprint
from functools import partial

pprint = partial(pprint, width = 200)
from pony.orm import Database, db_session


from ._database_entities import importEntities
from ..github import DATA_FOLDER

from ..api import *
from typing import Union, List, Any
from progressbar import ProgressBar


def formatErrorMessage(message, exception, *args, **kwargs):
	error_message = {
		'exception':     str(exception),
		'exceptionType': type(exception),
		'message':       message,
		'args':          args,
		'kwargs':        kwargs
	}
	return error_message


class YoutubeDatabase:
	def __init__(self, api_key: Union[str, YouTube] = None, filename: str = None):
		if isinstance(api_key, str):
			self.api = YouTube(api_key)
		else:
			self.api = api_key

		self.Channel = None
		self.Playlist = None
		self.PlaylistItem = None
		self.Video = None
		self.Tag = None

		self._initializeDatabase(filename)


	def _initializeDatabase(self, filename: str):

		if filename is None:
			filename = os.path.join(DATA_FOLDER, 'youtube_database.sqlite')
		elif os.path.isdir(filename):
			filename = os.path.join(filename, 'youtube_database.sqlite')
		elif '\\' not in filename and '/' not in filename:
			filename = os.path.join(DATA_FOLDER, filename + '.sqlite')

		self.filename = filename

		self._db = Database()
		self._db.bind(provider = 'sqlite', filename = self.filename, create_db = True)

		entities = importEntities(self._db)
		self.Channel = entities['channel']
		self.Playlist = entities['playlist']
		self.PlaylistItem = entities['playlistItem']
		self.Video = entities['video']
		self.Tag = entities['tag']

		self._db.generate_mapping(create_tables = True)

	def _getEntityClass(self, kind: Any):
		if not isinstance(kind, str):
			kind = kind['resourceType']
		if '#' not in kind: kind = 'youtube#' + kind

		kind = kind.split('#')[-1]
		if kind.endswith('s'):
			kind = kind[:-1]

		if kind == 'channel' or kind == 'youtube#channel':
			return self.Channel
		elif kind == 'playlist' or kind == 'youtube#playlist':
			return self.Playlist
		elif kind == 'tag' or kind == 'youtube#tag':
			return self.Tag
		elif kind == 'video' or kind == 'youtube#Video':
			return self.Video
		elif kind == 'playlistItem' or kind == 'youtube#playlistItem':
			return self.PlaylistItem
		else:
			message = "'{}' is not a valid entity type!".format(kind)
			raise ValueError(message)

	@db_session
	def insertItemIntoDatabase(self, items: ListResource, show:bool=False)->List:
		new_entities = list()
		if show:
			pbar = ProgressBar(max_value = len(items))
		else:
			pbar = None
		for index, item in enumerate(items):
			if show:
				pbar.update(index)


			sql_arguments: Dict = item.toDict(to_sql = True)
			item_type = sql_arguments.pop('resourceType')
			item_already_exists = self.exists(item_type, sql_arguments['resourceId'])
			if item_already_exists:
				continue
			#sql_arguments.pop('itemType')

			if item_type == 'youtube#video' or item_type == 'youtube#playlist':
				if 'channelId' not in sql_arguments:
					pprint(sql_arguments)
				channel_id = sql_arguments.pop('channelId')
				channel_entity = self.get('youtube#channel', channel_id, item_type = 'entity')
				sql_arguments['channel'] = channel_entity


			elif item_type == 'youtube#playlistItem':
				playlist_id = sql_arguments.pop('playlistId')
				video_id = sql_arguments['itemId']
				video_entity = self.get('youtube#video', video_id, item_type = 'entity')
				playlist_entity = self.get('youtube#playlist', playlist_id, item_type = 'entity')
				sql_arguments['playlist'] = playlist_entity
				sql_arguments['video'] = video_entity
			if item_type == 'youtube#video':
				tag_list = sql_arguments.pop('videoTags')
			elif item_type == 'youtube#playlist':
				tag_list = sql_arguments.pop('playlistTags')
			else:
				tag_list = []

			entity_class = self._getEntityClass(item)

			try:
				item_entity = entity_class(**sql_arguments)
				self.addTags(item_entity, tag_list)
				new_entities.append(item_entity)
			except Exception as exception:
				error_message = formatErrorMessage("Invalid Keys", exception, items, sql_arguments)
				pprint(error_message)
				raise ValueError
		return new_entities

	@db_session
	def addTags(self, entity, tags:List[str]):
		for tag in tags:
			t = self.Tag.get(string = tag)
			if t is None:
				t = self.Tag(string = tag)
			entity.tags.add(t)

	@db_session
	def exists(self, endpoint:str, key:str) -> bool:
		entity_class = self._getEntityClass(endpoint)
		entity_exists = entity_class.exists(resourceId = key)
		return entity_exists



	@db_session
	def retrieveItemFromDatabase(self, endpoint:str, key:str):
		entity_class = self._getEntityClass(endpoint)
		if ',' in key:
			keys = key.split(',')
			item = [entity_class.get(resourceId = k) for k in keys]
		else:
			item = entity_class.get(resourceId = key)
		return item

	@db_session
	def get(self, endpoint: str, key: str, item_type:str='resource') -> ListResource:
		"""
			Retrieves an item from the database, or inserts it if it's missing.
		Parameters
		----------
		endpoint: str
		key: str
		item_type: {'listResource', 'resource', 'entity', 'dict'}; default 'resource'

		Returns
		-------

		"""
		if 'youtube' not in endpoint:
			endpoint = 'youtube#' + endpoint

		# Check if item exists in database.
		item_in_database: bool = self.exists(endpoint, key)

		if item_in_database:
			item = self.retrieveItemFromDatabase(endpoint, key)

		else:
			# If not, insert it into the database.
			api_response = self.api.get(endpoint, key)
			item = self.insertItemIntoDatabase(api_response)

		if item_type == 'resource' or item_type == 'listResource':
			if not isinstance(item, list):
				item = [item]

			item = [i.toDict() for i in item]
			item = ListResource.fromSql(item)
			if item_type == 'resource' and len(item) == 1:
				item = item.items[0]
		elif item_type == 'entity':
			if isinstance(item, list) and len(item) == 1:
				item = item[0]

		return item

	def importChannel(self, channel_id:str):
		channel_response = self.api.getChannelItems(channel_id)
		if channel_response:

			self.insertItemIntoDatabase(channel_response, show = True)

	def importChannels(self, channel_ids:List[str]):
		for channel_id in channel_ids:
			channel_resource = self.get('youtube#channel', channel_id, item_type = 'listResource')
			if len(channel_resource)==0:
				print("Cannot import the channel.")
			else:
				for channel in channel_resource:
					channel_name = channel['channelName']
					video_count = channel['channelVideoCount']
					print("Importing '{}' with {} videos into the database.".format(channel_name, video_count))
					self.importChannel(channel['channelName'])



			self.importChannel(channel_id)
