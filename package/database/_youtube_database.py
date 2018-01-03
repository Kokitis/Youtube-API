import json
import os
from pprint import pprint

from pony.orm import Database, db_session 
import progressbar

from .._entities import importEntities
from ..github import DATA_FOLDER
from .validation import parseEntityArguments
from .. import YouTube

class YouTubeDatabase:
	def __init__(self, api_key = None, filename = None):
		if filename is None:
			filename = os.path.join(DATA_FOLDER, 'youtube_database.sqlite')
		elif os.path.isdir(filename):
			filename = os.path.join(filename, 'youtube_database.sqlite')
		elif '\\' not in filename and '/' not in filename:
			filename = os.path.join(DATA_FOLDER, filename + '.sqlite')

		self.filename = filename 


		self.error_filename = os.path.join(DATA_FOLDER, 'error_log.json')

		if not os.path.exists(self.error_filename):
			self._error_log = list()
		else:
			with open(self.error_filename, 'r') as file1:
				self._error_log = json.loads(file1.read())
		
		self.api = YouTube(api_key)

		self._db = Database()
		self._db.bind(provider='sqlite', filename=filename, create_db = True)
		
		self.Channel, self.Playlist, self.Tag, self.Video = importEntities(self._db)
		self._db.generate_mapping(create_tables=True)

	def _addError(self, error):
		self._error_log.append(error)
		with open(self.error_filename, 'w') as file1:
			file1.write(json.dumps(self._error_log, sort_keys = True, indent = 4))
	
	def __call__(self, kind, key):
		return self.getEntity(kind, key)

	def getEntity(self, kind, key):
		if kind.endswith('s'):
			kind = kind[:-1]

		#Check if entity already exists
		response = self.getEntity(kind, key)

		# If it doesn't exist, add it.
		if response is None:
			if kind == 'tag':
				response = key
			else:
				response = self.callApi(kind, key)
			response = self.access('add', kind, response)

		return response
	def callApi(self, kind, key):
		return self.api.get(kind, key)
	
	def _getEntityClass(self, kind):
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

	@db_session
	def access(self, method, entity_type, key = None, api_response = None, **kwargs):
		"""
			Parameters
			----------
			method: str
				'get'
				'import'
				'update'
			
			Keyword Arguments
			-----------------

		"""
		if key is None:
			if api_response is None:
				key = kwargs['id']

			else:
				key = api_response.toSqlEntity()['id']
		
		if method in ['get', 'import']:
			result = self.getEntity(entity_type, key)
		else:
			result = None
		
		if result is not None:
			return result

		if api_response is None:
			api_response = self.callApi(entity_type, key)

		entity_attributes = api_response.toSqlEntity(**kwargs)
		entity_tags = entity_attributes['tags']
		tags = list()
		for tag in entity_tags:
			t = self.getEntity('tag', tag)
			if t is None:
				t = self.Tag(string = tag)
			tags.append(t)
		entity_attributes['tags'] = tags

		if method in ['import', 'insert']:

			result = self._insertEntity(entity_type, api_response = api_response, **entity_attributes)

		if method in ['update']:
			raise NotImplementedError

		return result


	@db_session
	def _addMissingArguments(self, kind, parameters, **kwargs):

		if kind == 'video':
			if 'channelId' in parameters:
				channel_id = parameters['channelId']
			elif 'channelId' in kwargs:
				channel_id = kwargs.get('channelId')
			else:
				if False:
					pprint(parameters)
					print("\n")
					pprint(kwargs)
				raise KeyError("Could not find the channelId.")

			channel = self.getEntity('channel', channel_id)
			tags = [self.access('import', 'tag', tag) for tag in parameters['tags']]
			parameters['channel'] = channel
			parameters['tags'] = tags
		elif kind == 'channel':
			pass
		elif kind == 'playlist':
			if 'channelId' in parameters:
				channel_id = parameters.get('channelId')
			elif 'channelId' in kwargs:
				channel_id = kwargs.get('channelId')
			else:
				if False:
					pprint(parameters)
					print("\n")
					pprint(kwargs)
				raise KeyError("Could not find the channelId.")
			
			channel = self.getEntity('channel', channel_id)
			parameters['channel'] = channel
		else:
			pass

		return parameters



	def _insertEntity(self, kind, api_response = None, **parameters):
		entity_class = self._getEntityClass(kind)
		#parameters = self._cleanArguments(kind, **kwargs
		try:
			result = entity_class(**parameters)
		except Exception as exception:
			if False:
				print("Exception: ", str(exception))
				if api_response is not None:
					pprint(api_response.raw_response)
				print("Entity Type: '{}'".format(kind))
				print("\nRaw Data\n")
				pprint(parameters)
				print("\nClean Data\n")
				pprint(parameters)
			raise exception
		return result
	


	@db_session
	def importChannel(self, key):
		""" Imports the videos and playlists associated with a given channel.
		"""
		api_response = self.api.get('channels', key)
		if not api_response.status:
			print("Could not find Channel: ", key)
			return None
		channel = self.access('import', 'channel', key, api_response = api_response)

		if channel is None:
			print("Could not find channel '{}'".format(key))
			return None

		print("Importing all items for '{}'...".format(channel.name))

		items = self.api.getChannelItems(key)

		metrics = list()
		progress_bar = progressbar.ProgressBar(max_value = len(items))
		for index, item in enumerate(items):
			progress_bar.update(index)
			item_kind = item['itemKind']
			item_id = item['itemId']

			if item_kind == 'video':
				entity = self.access('import', item_kind, item_id, channel = channel)
			else:
				entity = self._importPlaylist(item_id, channel = channel)
			item['status'] = entity is not None
			metrics.append(item)

		return metrics

	@db_session
	def _importPlaylist(self, key, **kwargs):

		playlist = self.getEntity('playlist', key)
		if playlist is not None:
			return playlist
		
		playlist_response = self.callApi('playlist', key)

		if not playlist_response.status: 
			return None
		else:
			playlist_standard = playlist_response.toStandard()

			if 'channel' in kwargs:
				channel = kwargs['channel']
			else:
				channel_id = playlist_standard['channelId']
				channel = self.access('import', 'channel', channel_id)

			playlist_entity = playlist_response.toSqlEntity(channel = channel)

			playlist_entity['channel'] = channel
			playlist_tags = playlist_entity.pop('tags')
			playlist = self.access('import', 'playlist', **playlist_entity)

			for item in playlist_standard['playlistItems']:
				kind = item['itemKind']
				if kind != 'video':
					continue
				else:
					video = self.access('import', 'video', item['videoId'])
				if video is None: 
					continue
				video.playlists.add(playlist)

	@staticmethod
	def _cleanArguments(kind, **data):
		return parseEntityArguments(kind, **data)

	
	@db_session
	def getEntity(self, kind, key = None, **kwargs):
		"""
			Parameters
			----------
				kind: {'channel', 'playlist', 'tag', 'video'}
				key: str; default None

				Keyword Arguments
				-----------------
				'id', 'string':  The primary key for an object in the database.
		"""	
		if isinstance(key, dict) and ('itemId' in key or 'string' in key):
			kwargs = key
		
		kwargs = self._cleanArguments(kind, **kwargs)

		if isinstance(key, str):
			if kind.startswith('tag'): arg_key = 'string'
			else: arg_key = 'id'
			parameters = {arg_key: key}
		elif 'id' in kwargs or 'string' in kwargs:
			k = 'id' if kind != 'tag' else 'string'
			parameters = {k: kwargs[k]}
		else:
			message = "Could not find the primary Key"
			print("key: ", key)
			pprint(kwargs)
			raise ValueError(message)

		entity_class = self._getEntityClass(kind)

		try:
			result = entity_class.get(**parameters)
		except Exception as exception:
			if False:
				print("Entity Type: '{}'\n".format(kind))
				#print("Key: '{}'".format(key))
				#print("\nRaw Arguments\n")
				#pprint(kwargs)
				print("\Clean Arguments\n")
				pprint(parameters)
			raise exception
		return result
	@db_session 
	def select(self, kind, expression):
		entity_class = self._getEntityClass(kind)
		result = entity_class.select(expression)
		return result
