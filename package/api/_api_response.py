
from pprint import pprint
from ..github import timetools
class ApiResponse:
	"""
		Parsed the response from the Youtube Api. Provedes a convienient method of converting the
		requested data into an easily-parsable format(via .toStandard()) as well as a format compatible with the
		YoutubeDatabase SQL schema.

		Parameters
		----------
			api_response: requests.models.Response
				The output of the api_request. Each request will be saved in the 'items' field of a json object,
				and may contain more than on item.
			kwargs:
	"""

	def __init__(self, api_response, **kwargs):

		self.api_response = api_response
		if isinstance(api_response, dict):
			json_response = api_response
		else:
			json_response = self.api_response.json()

		response_items = json_response.get('items', [])

		if len(response_items) == 1:
			json_response = response_items.pop()
			self.endpoint = self._getEndpoint(json_response)

			self.data = self._parseApiResponse(json_response)
			self.items = list()

		else:
			self.data = dict()
			self.endpoint = ""
			self.items = [ApiResponse(i) for i in response_items]
			raise NotImplementedError


	def __str__(self):
		string = "ApiResponse('{}', '{}')".format(self.endpoint, self.data['id'])
		return string

	@staticmethod
	def _getEndpoint(response):
		"""
			Attempts to determine the endpoint from the api response.
		Parameters
		----------
		response: dict
			The output or the .json() method of the requests.Response object.

		Returns
		-------

		"""

		response_type = response['kind']

		"""
		if response_type == 'youtube#channelListResponse':
			endpoint = 'channel
		elif response_type == 'youtube#playlistListResponse':
			endpoint = 'playlist
		elif response_type == 'youtube#videoListResponse':
			endpoint = 'video
		else:
			pprint(response)
			raise NotImplementedError
		"""
		endpoint = response_type.split('#')[1]


		return endpoint

	def _parseApiResponse(self, api_response):
		"""
			Validates the response from the api and ensures each argument is of the correct datatype.
		Returns
		-------
			dict, list<dict>
		"""
		if self.endpoint == 'playlistItems':
			raise NotImplementedError
		else:
			validated_json_response = self._validateResponseAttributes(api_response)
		return validated_json_response

	def _defineRequestedAttributes(self):
		"""
			Returns the keys that will be the most commonly used.
		Returns
		-------

		"""

		if self.endpoint == 'video':
			snippet_keys = [
				'title', 'id', 'channelId', 'channelTitle',
				'description', 'defaultAudioLanguage', 'liveBroadcastContent', 'publishedAt',
			]
			required_snippet_keys = ['title', 'id', 'channelId', 'channelTitle', 'description', 'publishedAt']

			statistics_keys = ['likeCount', 'dislikeCount', 'commentCount', 'favoriteCount', 'viewCount']
			required_statistics_keys = ['likeCount', 'dislikeCount', 'viewCount']

			content_details_keys = ['duration']
			required_content_details_keys = ['duration']


		elif self.endpoint == 'channel':
			snippet_keys = ['title', 'country', 'description', 'publishedAt']

			required_snippet_keys = ['title', 'publishedAt']

			statistics_keys = ['viewCount', 'videoCount', 'subscriberCount']
			required_statistics_keys = statistics_keys

			content_details_keys = None
			required_content_details_keys = None
		elif self.endpoint == 'playlist':
			snippet_keys = [
				'id', 'channelId', 'channelTitle',
				'description', 'publishedAt', 'title'
			]
			required_snippet_keys = ['id', 'title', 'channelId']

			statistics_keys = []
			required_statistics_keys = []

			content_details_keys = ['itemCount']
			required_content_details_keys = ['itemCount']

		elif self.endpoint == 'playlistItem':
			snippet_keys = ['channelId', 'channelTitle', 'description', 'playlistId', 'publishedAt', 'title',
				'resourceId']
			required_snippet_keys = ['resourceId', 'playlistId']

			statistics_keys = []
			required_statistics_keys = []

			content_details_keys = []
			required_content_details_keys = []
		else:
			message = "'{}' is not a supported endpoint.".format(self.endpoint)
			raise ValueError(message)

		attributes = {
			'snippetKeys':                snippet_keys,
			'snippetRequiredKeys':        required_snippet_keys,

			'statisticsKeys':             statistics_keys,
			'statisticsRequiredKeys':     required_statistics_keys,

			'contentDetailsKeys':         content_details_keys,
			'contentDetailsRequiredKeys': required_content_details_keys
		}

		return attributes


	def extractOne(self, converter = None):
		# items = self.getItems(function)
		items = self.getItems(converter)

		if len(items) == 0:
			result = None
		elif len(items) == 1:
			result = items[0]
		else:
			result = items[0]

		return result

	def toSqlEntity(self, **kwargs):
		"""
			Converts the data contained in the api response to a dict
			compatible with the YoutubeDatabase schema. The output can be directly used
			to update the database objects.
		Parameters
		----------
		kwargs

		Returns
		-------
			dict

		"""
		standard_response = self.toStandard()

		if self.endpoint == 'video':
			entity = {
				'id':          'videoId',
				'name':        "videoName",
				'views':       "videoViewCount",
				'likes':       'videoLikeCount',
				'dislikes':    "videoDislikeCount",
				'publishDate': 'videoPublishDate',
				'duration':    'videoDuration',
				'description': 'videoDescription',
				'tags':        'videoTags'
			}
		elif self.endpoint == 'channel':
			entity = {
				'id':              'channelId',
				'name':            'channelName',
				'country':         'channelCountry',
				'creationDate':    'channelCreationDate',
				'description':     'channelDescription',
				'subscriberCount': 'channelSubscriberCount',
				'videoCount':      'channelVideoCount',
				'viewCount':       'channelViewCount'
			}
		elif self.endpoint == 'playlist':
			entity = {
				'id':          'playlistId',
				'name':        'playlistName',
				'itemCount':   'playlistItemCount',
				'description': 'playlistDescription'
			}
		else:
			raise NotImplementedError

		try:
			sql_entity_args = {k: standard_response[v] for k, v in entity.items()}
		except Exception as exception:
			error_information = {
				'input':        {
					'kwargs': kwargs
				},
				'inFunction':   "ApiResponse.toEntity",
				'errorMessage': str(exception),
				'apiResponse':  self.api_response,
				'entity':       entity,
				'response':     standard_response
			}
			pprint(error_information)
			raise exception

		if self.endpoint == 'video' or self.endpoint == 'playlist':
			if 'channel' in kwargs:
				channel = kwargs['channel']
			else:
				raise NotImplementedError

			sql_entity_args['channel'] = channel

		if 'tags' not in sql_entity_args:
			sql_entity_args['tags'] = list()

		return sql_entity_args

	def toStandard(self, **kwargs):
		""" Converts the api response into a standardized format. All relevent data
			for the requested entities is represented as a standard dictionary where each
			key is mapped to either a scalar variable or a list, as needed.
		Returns
		-------

		"""
		#api_response = self.extractOne()
		api_response = self.data

		_toNum = lambda s: int(s) if s else -1

		if self.endpoint == 'channel':
			channel_id = api_response['id']
			channel_name = api_response['snippet']['title']
			channel_date = api_response['snippet']['publishedAt']
			channel_country = api_response['snippet']['country']
			channel_description = api_response['snippet']['description']
			channel_subscribers = api_response['statistics']['subscriberCount']
			channel_views = api_response['statistics']['viewCount']
			channel_videos = api_response['statistics']['videoCount']

			channel_date = timetools.Timestamp(channel_date)

			standard = {
				'itemKind':               'channel',
				'itemId':                 channel_id,
				'channelId':              channel_id,
				'channelName':            channel_name,
				'channelCreationDate':    channel_date,
				'channelCountry':         channel_country,
				'channelDescription':     channel_description,
				'channelSubscriberCount': channel_subscribers,
				'channelViewCount':       channel_views,
				'channelVideoCount':      channel_videos
			}
		elif self.endpoint == 'video':
			video_id = api_response['id']
			video_name = api_response['snippet']['title']
			view_count = api_response['statistics']['viewCount']
			like_count = api_response['statistics']['likeCount']
			dislike_count = api_response['statistics']['dislikeCount']
			video_date = api_response['snippet']['publishedAt']
			video_duration = api_response['contentDetails']['duration']
			video_channel = api_response['snippet']['channelId']
			video_description = api_response['snippet']['description']
			tags = api_response['tags']

			video_duration = timetools.Duration(video_duration)
			video_date = timetools.Timestamp(video_date)

			standard = {
				'itemKind':          'video',
				'itemId':            video_id,
				'videoId':           video_id,
				'videoName':         video_name,
				'videoViewCount':    _toNum(view_count),
				'videoLikeCount':    _toNum(like_count),
				'videoDislikeCount': _toNum(dislike_count),
				'videoPublishDate':  video_date,
				'videoDuration':     video_duration,
				'channelId':         video_channel,
				'videoDescription':  video_description,
				'videoTags':         tags
			}
		elif self.endpoint == 'playlist':

			playlist_id = api_response['id']
			playlist_name = api_response['snippet']['title']
			playlist_channel = api_response['snippet']['channelId']
			playlist_videos = api_response['contentDetails']['itemCount']
			playlist_description = api_response['snippet']['description']
			standard = {
				'itemKind':            'playlist',
				'itemId':              playlist_id,
				'playlistId':          playlist_id,
				'playlistName':        playlist_name,
				'channelId':           playlist_channel,
				'playlistDescription': playlist_description,
				'playlistItemCount':   playlist_videos,
				'playlistItems':       None
			}

			playlist_items = kwargs.get('playlistItems', [])
			standard['playlistItems'] = playlist_items
		else:
			raise NotImplementedError

		return standard



	def _verifyResponseStatusCode(self, response):
		error_response = response.get('errors')

		if error_response:
			error_code = error_response['code']
			status = False

			if error_code == 503:  # Common backend error
				error_message = "Common Backend Error."
			else:
				error_message = "Uncommon Error."

		elif len(response['items']) == 0:

			status = False
			error_code = -1
			error_message = "No items found."
		else:
			error_message = "No Errors."
			error_code = 0
			status = True

		error_info = {
			'inputs':       {
				'response':   response
			},
			'inFunction':   "ApiResponse._verifyResponse",
			'status':       status,
			'errorCode':    error_code,
			'errorMessage': error_message,

		}

		self.error = error_info

		return error_info


	def _validateResponseAttributes(self, response):

		_extractKeys = lambda data, keys: {k:data.get(k) for k in keys}

		response_id = response['id']

		snippet = response.get('snippet')
		statistics = response.get('statistics')
		content_details = response.get('contentDetails')
		topic_details = response.get('topicDetails', dict())

		attribute_definitions = self._defineRequestedAttributes()
		snippet_keys = attribute_definitions['snippetKeys']
		snippet_required_keys = attribute_definitions['snippetRequiredKeys']
		statistics_keys = attribute_definitions['statisticsKeys']
		statistics_required_keys = attribute_definitions['statisticsRequiredKeys']

		content_details_keys = attribute_definitions['contentDetailsKeys']
		content_details_required_keys = attribute_definitions['contentDetailsRequiredKeys']

		# Validate response attributes

		_isValid = lambda data, keys: data is not None and all(data[k] is not None for k in keys) # check if any are None

		validated_snippet = None
		validated_statistics = None
		validated_content_details = None

		# Validate Snippet

		if snippet and snippet_keys:
			validated_snippet = _extractKeys(snippet, snippet_keys)
		snippet_is_valid = _isValid(validated_snippet, snippet_required_keys)


		# Validate Statistics

		if statistics and statistics_keys:
			validated_statistics = _extractKeys(statistics, statistics_keys)
		statistics_is_valid = _isValid(validated_statistics, statistics_required_keys)

		# Validate ContentDetails

		if content_details and content_details_keys:
			validated_content_details = _extractKeys(content_details, content_details_keys)
		content_details_is_valid = _isValid(validated_content_details, content_details_required_keys)

		# Add tags and check if all parts are valid

		if self.endpoint == 'video':
			tags = snippet.get('tags', [])
			tags += topic_details.get('topicCategories', [])
			tags += topic_details.get('relevantTopicIds', [])
			is_valid = snippet_is_valid and statistics_is_valid and content_details_is_valid

		elif self.endpoint == 'channel':
			tags = []
			is_valid = snippet_is_valid and statistics_is_valid

		elif self.endpoint == 'playlist':
			tags = []
			is_valid = snippet_is_valid and content_details_is_valid

		elif self.endpoint == 'playlistItem':
			resource = snippet['resourceId']
			item_kind = resource['kind'].split('#')[1]
			item_id = resource[item_kind + 'Id']
			response_id = item_id
			validated_snippet['itemId'] = item_id
			tags = []
			is_valid = snippet_is_valid
		else:
			tags = []
			is_valid = False

		tags = [str(i).lower() for i in tags]

		error_info = {
			'input':        {
				'response': response
			},
			'inFunction':   "ApiResponse._validateResponseitems'",
			'errorMessage': "Error when validating the api response.",
			'status':       is_valid
		}

		result = {
			'id':               response_id,
			'itemKind':         self.endpoint,
			'tags':             tags,
			'isValid':          is_valid,
			'snippet':          validated_snippet,
			'statistics':       validated_statistics,
			'contentDetails':   validated_content_details,
			'topicDetails':     topic_details,
			'errorInformation': error_info
		}
		return result

	@property
	def status(self):
		return self.api_response.status_code == 200