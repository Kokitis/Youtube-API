from .._entities import importEntities
from ..github import DATA_FOLDER
from .validation import parseEntityArguments, validateEntity
import pony
from pprint import pprint
import json
import os 
import progressbar

class YouTubeDatabase:
	def __init__(self, api, filename = None):
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
		self.api = api 
		self._db = pony.orm.Database()
		self._db.bind(provider='sqlite', filename=filename, create_db = True)
		
		self.Channel, self.Playlist, self.Tag, self.Video = importEntities(self._db)
		self._db.generate_mapping(create_tables=True)

	def _addError(self, error):
		self._error_log.append(error)
		with open(self.error_filename, 'w') as file1:
			file1.write(json.dumps(self._error_log, sort_keys = True, indent = 4))
	
	def __call__(self, kind, key):
		if kind.endswith('s'):
			kind = kind[:-1]

		#Check if entity already exists
		response = self.get(kind, key)

		# If it doesn't exist, add it.
		if response is None:
			if kind == 'tag':
				response = key 
			else:
				response = self.api.get(kind, key)
			response = self.access('add', kind, response)

		return response
	def _getEntityClass(self, kind):
		if kind == 'channel':
			return self.Channel 
		elif kind == 'playlist':
			return self.Playlist 
		elif kind == 'tag':
			return self.Tag 
		elif kind == 'video':
			return self.Video
	def callApi(self, endpoint, **parameters):
		return self.api.request(endpoint, **parameters)
	@pony.orm.db_session
	def access(self, method, kind, key = None, **kwargs):

		if method in ['get', 'import']:
			result = self.get(kind, key, **kwargs)
		else:
			result = None

		if isinstance(key, str):
			parameters = self.api.get(kind, key)
		elif isinstance(key, dict):
			parameters = key
		else:
			parameters = kwargs

		if parameters is None:
			_error_message = {
				'itemType': kind,
				'itemId': key,
				'inFunction': 'YouTubeDatabase.access',
				'message': "api returned 'None'",
				'inputParameters':
					{
						'method': method,
						'kind': kind,
						'key': key,
						'kwargs': kwargs
					},
				'apiResponse': self.api.get(kind, key)
			}
			self._addError(_error_message)
			return None
		database_parameters = self._cleanArguments(kind, **parameters)
		database_parameters = self._addMissingArguments(kind, database_parameters, **parameters)
		#pprint(database_parameters)
		if method in ['import', 'insert'] and result is None:
			result = self._insertEntity(kind, **database_parameters)

		if method in ['update']:
			pass

		return result
	@pony.orm.db_session

	def _addMissingArguments(self, kind, parameters, **kwargs):

		if kind == 'video':
			if 'channelId' in parameters:
				channel_id = parameters['channelId']
			elif 'channelId' in kwargs:
				channel_id = kwargs['channelId']
			else:
				if True:
					pprint(parameters)
					print("\n")
					pprint(kwargs)
				raise KeyError("Could not find the channelId.")
			channel = self('channel', channel_id)
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
				if True:
					pprint(parameters)
					print("\n")
					pprint(kwargs)
				raise KeyError("Could not find the channelId.")
			
			channel = self('channel', channel_id)
			parameters['channel'] = channel
		else:
			pass

		return parameters
	def _insertEntity(self, kind, **kwargs):
		entity_class = self._getEntityClass(kind)
		parameters = self._cleanArguments(kind, **kwargs)
		
		if not validateEntity(kind, **parameters):
			return None
		try:
			
			result = entity_class(**parameters)
		except Exception as exception:
			if False:
				print("Entity Type: '{}'".format(kind))
				print("\nRaw Data\n")
				pprint(kwargs)
				print("\nClean Data\n")
				pprint(parameters)
			#raise exception 
			result = None
		return result
	def importVideos(self, elements):
		""" list of Video ids. """
		for video_id in elements:
			self.access('import', 'video', video_id)
	@pony.orm.db_session
	def importChannel(self, key):
		""" Imports the videos and playlists associated with a given channel.
		"""
		channel = self.access('import', 'channel', key)
		if channel is None:
			print("Could not find channel '{}'".format(key))
			return None
		print("Importing all items for '{}'...".format(channel.name))

		items = self.api.getChannelElements(key)
		metrics = {
			'found': 0,
			'failed': 0
		}
		progress_bar = progressbar.ProgressBar(max_value = len(items))
		for index, item in enumerate(items):
			progress_bar.update(index)
			item_id = item['itemId']
			item_kind = item['itemKind']
			if item_kind == 'youtube#playlist':
				self._importPlaylist(item_id)
			elif item_kind == 'youtube#video':
				channel_video = self.access('import', 'video', item_id)
				if channel_video is not None:
					metrics['found'] += 1
				else:
					metrics['failed'] += 1

		pprint(metrics)

	@pony.orm.db_session
	def _importPlaylist(self, key):

		playlist = self.get('playlist', key)
		if playlist is not None:
			return playlist

		playlist_response = self.api.get('playlist', key)
		
		playlist_response['channel'] = self.access('import', 'channel', playlist_response['channelId'])

		playlist = self.access('import', 'playlist', **playlist_response)

		for item in playlist_response['items']:
			kind = item['kind'].split('#')[1]
			if kind != 'video':
				continue
			else:
				video = self.access('import', 'video', item['videoId'])
			if video is None: continue
			video.playlists.add(playlist)

	@staticmethod
	def _cleanArguments(kind, **data):
		return parseEntityArguments(kind, **data)

	@pony.orm.db_session
	def get(self, kind, key = None, **kwargs):
		"""
			Parameters
			----------
				kind: {'channel', 'playlist', 'tag', 'video'}
				key: str; default None

				Keyword Arguments
				-----------------
				'id', 'string':  The primary key for an object in the database.
		"""	
		if isinstance(key, dict) and ('id' in key or 'string' in key):
			kwargs = key
		kwargs = self._cleanArguments('playlist',**kwargs)
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
			if True:
				print("Entity Type: '{}'\n".format(kind))
				#print("Key: '{}'".format(key))
				#print("\nRaw Arguments\n")
				#pprint(kwargs)
				print("\Clean Arguments\n")
				pprint(parameters)
			raise exception
		return result
	@pony.orm.db_session 
	def select(self, kind, expression):
		entity_class = self._getEntityClass(kind)
		result = entity_class.select(expression)
		return result
