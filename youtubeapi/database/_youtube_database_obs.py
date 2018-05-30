
import os
from pprint import pprint
from functools import partial
pprint = partial(pprint, width = 200)
from pony.orm import Database, db_session 
import progressbar

from .._entities import importEntities
from ..github import DATA_FOLDER
from .validation import parseEntityArguments
from .. import YouTube
from typing import Union, List

def formatErrorMessage(message, exception, *args, **kwargs):
	error_message = {
		'exception': str(exception),
		'exceptionType': type(exception),
		'message': message,
		'args': args,
		'kwargs': kwargs
	}
	return error_message

class YouTubeDatabaseOBS:
	def __init__(self, api_key:Union[str,YouTube] = None, filename:str = None):
		if isinstance(api_key, str):
			self.api = YouTube(api_key)
		else:
			self.api = api_key
		self._initializeDatabase(filename)


	def callApi(self, kind:str, key:Union[str,List[str]]):
		return self.api.get(kind, key)

	def _initializeDatabase(self, filename:str):

		if filename is None:
			filename = os.path.join(DATA_FOLDER, 'youtube_database.sqlite')
		elif os.path.isdir(filename):
			filename = os.path.join(filename, 'youtube_database.sqlite')
		elif '\\' not in filename and '/' not in filename:
			filename = os.path.join(DATA_FOLDER, filename + '.sqlite')

		self.filename = filename

		self._db = Database()
		self._db.bind(provider = 'sqlite', filename = self.filename, create_db = True)

		self.Channel, self.Playlist, self.Tag, self.Video = importEntities(self._db)
		self._db.generate_mapping(create_tables = True)

	def _getEntityClass(self, kind:str):
		if kind.endswith('s'):
			kind = kind[:-1]
		if kind == 'channel':
			return self.Channel 
		elif kind == 'playlist':
			return self.Playlist 
		elif kind == 'tag':
			return self.Tag 
		elif kind == 'video':
			return self.Video
		else:
			message = "'{}' is not a valid entity type!".format(kind)
			raise ValueError(message)

	def retrieveEntityFromDatabase(self, kind, key, api_response = None, **kwargs):
		"""

		Parameters
		----------
		kind
		key
		api_response: ApiResponse
		kwargs

		Returns
		-------

		"""
		entity_class = self._getEntityClass(kind)
		# Check if an enity id was given.
		if not key:
			if api_response:
				key = api_response.id
			else:
				key = kwargs.get('id', kwargs.get('itemId'))

		if key:
			result = entity_class.get(id = key)
		else:
			# Use entity.get()
			arguments = self._cleanArguments(kind, **kwargs)
			result = entity_class.get(**arguments)

		return result


	def addEntityToDatabase(self, kind, api_response, **kwargs):
		try:
			sql_entity_attributes = api_response.toSqlEntity(**kwargs)

			entity_tags = sql_entity_attributes.pop('tags')
			result = self._insertEntity(kind, **sql_entity_attributes)
			self.addTagsToEntity(result, entity_tags)
		except ValueError:
			result = None
		return result


	def addTagsToEntity(self, entity, tags):
		"""
			Adds tags to an entity in the database.
		Parameters
		----------
		entity
		tags

		Returns
		-------

		"""
		if not hasattr(entity, 'tags'): return None
		for tag in tags:
			t = self.Tag.get(string = tag)
			if t is None:
				t = self.Tag(string = tag)
			entity.tags.add(t)

	@db_session
	def access(self, method, entity_type, key = None, api_response = None, **kwargs):
		"""

		Parameters
		----------
			method: {'get', 'import', 'update'}
			entity_type: {'channel', 'video', 'playlist'}
			key: str; default None
			api_response: ApiResponse
			kwargs

		Returns
		-------

		"""

		if method in ['get', 'import']:
			result = self.retrieveEntityFromDatabase(entity_type, key, api_response, **kwargs)
		else:
			result = None

		if result is None and method in {'import', 'insert', 'update'}:
			if api_response is None:
				api_response = self.callApi(entity_type, key)

			if method in ['import', 'insert']:

				result = self.addEntityToDatabase(entity_type, api_response, **kwargs)

			if method in ['update']:
				raise NotImplementedError

		return result


	def _insertEntity(self, kind, **parameters):
		entity_class = self._getEntityClass(kind)
		try:
			result = entity_class(**parameters)
		except Exception as exception:
			error_message = formatErrorMessage("in ._insertEntity", exception, kind = kind, **parameters)
			if True:
				print()
				pprint(error_message)
			raise exception
		return result

	@db_session
	def importChannel(self, key, include_channels = False):
		"""
			Imports all videos and playlists associated with a channel
		Parameters
		----------
		key
		include_channels: bool; default False

		Returns
		-------

		"""
		api_response = self.callApi('channels', key)

		channel = self.access('import', 'channel', key, api_response = api_response)

		if not api_response or channel is None:
			print("Could not find channel '{}'".format(key))
			return None

		print("\nImporting all items for '{}' ('{}')...\n".format(channel.name, channel.id))

		channel_items = self.api.getChannelItems(key)

		metrics = list()
		progress_bar = progressbar.ProgressBar(max_value = len(channel_items))
		for index, element in enumerate(channel_items):
			progress_bar.update(index)
			item = element.toStandard()
			item_kind = item['itemKind']
			item_id = item['itemId']

			if item_kind == 'video':
				entity = self.access('import', item_kind, item_id, channel = channel)
			elif item_kind == 'playlist':
				entity = self.importPlaylist(item_id, channel = channel)
			elif item_kind == 'channel':
				if include_channels:
					entity = self.importChannel(item_id)
				else:
					continue
			else:
				message = "'{}' is not a supported entity!".format(item_kind)
				raise ValueError(message)

			item['status'] = entity is not None
			metrics.append(item)

		return metrics

	@db_session
	def importPlaylist(self, key, **kwargs):

		playlist_entity = self.retrieveEntityFromDatabase('playlist', key)
		if playlist_entity is not None:
			return playlist_entity

		playlist_response = self.callApi('playlist', key)
		playlist_standard = playlist_response.toStandard()

		if 'channel' in kwargs:
			channel = kwargs['channel']
		else:
			channel_id = playlist_standard['channelId']
			channel = self.access('import', 'channel', channel_id)

		playlist_entity = self.access('import', 'playlist', api_response = playlist_response, channel = channel)

		playlist_items = self.api.getPlaylistItems(playlist_entity.id)

		for item in playlist_items:
			playlist_item = self.importPlaylistItem(item, channel = channel)
			playlist_entity.videos.add(playlist_item)
		return playlist_entity

	def importPlaylistItem(self, item, channel):

		item_standard = item.toStandard()
		item_kind = item_standard['itemKind']
		item_id = item_standard['itemId']

		result = self.access('import', item_kind, item_id, channel = channel)
		return result

	@staticmethod
	def _cleanArguments(kind, **data):
		return parseEntityArguments(kind, **data)

	def get(self, kind:str, keys:Union[str,List[str]]):
		# Check if the keys already exist in the database

		#If not, use the api to request the data
		pass

	@db_session 
	def select(self, kind, expression):
		entity_class = self._getEntityClass(kind)
		result = entity_class.select(expression)
		return result
