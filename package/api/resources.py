from package.github import timetools
from pprint import pprint
from typing import Dict, List,Iterable
import json
import yaml


# https://developers.google.com/youtube/v3/docs/playlists
def checkKeys(expected_keys:List[str], provided_keys:Iterable)->None:
	expected_keys = set(expected_keys)
	provided_keys = set(provided_keys)
	missing_keys = sorted(expected_keys - provided_keys)
	extra_keys = sorted(provided_keys - expected_keys)

	if len(missing_keys) > 0:
		print("Missing keys:")
		for i in missing_keys:
			print("\t", i)
		print("Provided Keys: ")
		for i in sorted(provided_keys):
			print("\t", i)
		print("Extra Keys: ")
		for i in extra_keys:
			print("\t", i)
		raise ValueError

class ListResource:
	def __init__(self, api_response: Dict):

		self.response = api_response
		if 'error' in api_response:
			pprint(api_response)
			self.kind = 'youtube#error'
			self.status_code = api_response['statusCode']
		else:
			self.status_code = 200
			self.kind = api_response.get('kind')  # should be 'youtube#videoListResponse'
		self.etag: str = api_response.get('etag')
		self.next_page_token: str = api_response.get('nextPageToken')
		self.previous_page_token: str = api_response.get('prevPageToken')
		self.page_info: Dict = api_response.get('pageInfo')
		self.items: List = [self.getResource(i) for i in api_response.get('items', [])]

	def __str__(self):
		if self.status_code == 200:
			string = "ListResource('{}', {})".format(self.etag, len(self.items))
		else:
			string = "ListResource('error', {})".format(self.status_code)
		return string

	def __getitem__(self, item: int):
		return self.items[item]

	def __len__(self):
		return len(self.items)

	@staticmethod
	def _handleError(error: Dict) -> None:
		pprint(error)

	def summary(self) -> None:
		print(self)
		print("itemCount: ", len(self.items))
		for i in self.items:
			print("\t", i)

	@staticmethod
	def getResource(item: Dict):

		item_kind = item.get('kind', item.get('itemType'))

		if item_kind == 'youtube#video':
			item_class = VideoResource
		elif item_kind == 'youtube#channel':
			item_class = ChannelResource
		elif item_kind == 'youtube#playlist':
			item_class = PlaylistResource
		elif item_kind == 'youtube#playlistItem':
			item_class = PlaylistItemResource
		elif item_kind == 'youtube#searchResult':
			item_class = SearchResource
		else:
			message = "'{}' is not a supported resource!".format(item_kind)
			raise ValueError(message)
		if 'resourceId' in item: #Comes from the database.
			item_resource = item_class.fromSql(item)
		else:
			item_resource = item_class(item)
		return item_resource

	def toFile(self, filename):

		filetype = filename.split('.')[-1]

		data = {
			'etag':              self.etag,
			'items':             self.items,
			'pageInfo':          self.page_info,
			'previousPageToken': self.previous_page_token,
			'nextPageToken':     self.next_page_token
		}

		if filetype == 'json':
			data_string = json.dumps(data, indent = 4, sort_keys = True)
		elif filetype == 'yaml':
			data_string = yaml.dump(data, default_flow_style = False, indent = 4)
		else:
			raise NotImplementedError

		with open(filename, 'w') as file1:
			file1.write(data_string)

	@classmethod
	def fromSql(cls, items: List[Dict]) -> 'ListResource':
		sql_response = {
			'kind':          'youtube#ListResource',
			'etag':          'fromSql',
			'nextPageToken': "",
			'prevPageToken': "",
			'pageInfo':      {},
			'items':         items
		}

		return cls(sql_response)


class ChannelResource:
	def __init__(self, response: Dict):
		self.response = response
		self.kind = response.get('kind')
		self.etag = response.get('etag')
		self.resource_id = response.get('id')
		self.item_id = self.resource_id

		default_response = dict()

		self.snippet = self._parseSnippet(response.get('snippet', default_response))
		self.content_details = self._parseContentDetails(response.get('contentDetails', default_response))
		self.statistics = self._parseStatistics(response.get('statistics', default_response))
		self.topic_details = self._parseTopicDetails(response.get('topicDetails', default_response))
		self.status = self._parseStatus(response.get('status', default_response))
		self.branding_settings = self._parseBrandingSettings(response.get('brandingSettings', default_response))
		self.audit_details = self._parseAuditDetails(response.get('auditDetails', default_response))
		self.content_owner_details = self._parseContentOwnerDetails(response.get('contentOwnerDetails'))
		self.localizations = self._parseLocalizations(response.get('localizations', default_response))

		self.data = {**self.snippet, **self.content_details, **self.statistics}
		self.data['resourceId'] = self.resource_id
		self.data['itemId'] = self.item_id
		self.data['itemType'] = self.kind
		self.data['resourceType'] = self.kind

	def __str__(self):
		channel_name = self.snippet['channelName']
		string = "ChannelResource('{}')".format(channel_name)
		return string

	def __getitem__(self, item: str):
		return self.data.get(item)

	@staticmethod
	def _parseSnippet(snippet: Dict):
		standard_snippet = {
			'channelName':        snippet.get('title', ''),
			'channelDescription': snippet.get('description', ''),
			'channelUrl':         snippet.get('customUrl', ''),
			'channelLanguage':    snippet.get('defaultLanguage', ''),
			'channelCountry':     snippet.get('country', '')
		}
		return standard_snippet

	@staticmethod
	def _parseContentDetails(content_details: Dict) -> Dict:
		related_playlists = content_details.get('relatedPlaylists', {})
		standard_content_details = {
			'channelUploadPlaylist': related_playlists.get('uploads')
		}
		return standard_content_details

	@staticmethod
	def _parseStatistics(statistics: Dict) -> Dict:
		view_count = int(statistics.get('viewCount', 0))
		comment_count = int(statistics.get('commentCount', 0))
		subscriber_count = int(statistics.get('subscriberCount', 0))
		video_count = int(statistics.get('videoCount', 0))
		standard_statistics = {
			'channelViewCount':       view_count,
			'channelCommentCount':    comment_count,
			'channelSubscriberCount': subscriber_count,
			'channelVideoCount':      video_count
		}
		return standard_statistics

	@staticmethod
	def _parseTopicDetails(response: Dict) -> Dict:
		return response

	@staticmethod
	def _parseStatus(response: Dict) -> Dict:
		return response

	@staticmethod
	def _parseBrandingSettings(response: Dict) -> Dict:
		return response

	@staticmethod
	def _parseAuditDetails(response: Dict) -> Dict:
		return response

	@staticmethod
	def _parseContentOwnerDetails(response: Dict) -> Dict:
		return response

	@staticmethod
	def _parseLocalizations(response: Dict) -> Dict:
		return response

	def toDict(self, to_sql:bool = False)->Dict:

		data = self.data
		if to_sql:
			allowed_keys = ['resourceId','resourceType', 'itemId', 'itemType', 'channelId', 'channelName', 'channelDescription',
							'channelUrl', 'channelLanguage', 'channelUploadPlaylist', 'channelViewCount', 'channelCommentCount',
							'channelSubscriberCount', 'channelVideoCount']
			data = {k:v for k,v in data.items() if k in allowed_keys}
		return data

	@classmethod
	def fromSql(cls, response:Dict)->'ChannelResource':
		expected_keys = ['channelName', 'channelDescription', 'channelUrl', 'channelLanguage', 'channelCountry',
						 'channelUploadPlaylist', 'channelViewCount', 'channelCommentCount', 'channelSubscriberCount',
						 'channelVideoCount', 'resourceId']
		checkKeys(expected_keys,response.keys())
		snippet = {
			'title':           response['channelName'],
			'description':     response['channelDescription'],
			'customUrl':       response['channelUrl'],
			'defaultLanguage': response['channelLanguage'],
			'country':         response['channelCountry']
		}

		content_details = {
			'relatedPlaylists': {
				'uploads': response['channelUploadPlaylist']
			}
		}

		statistics = {
			'viewCount':       response['channelViewCount'],
			'commentCount':    response['channelCommentCount'],
			'subscriberCount': response['channelSubscriberCount'],
			'videoCount':      response['channelVideoCount']
		}

		api_response = {
			'kind':           'youtube#channel',
			'etag':           'fromSql',
			'id':             response['resourceId'],
			'snippet':        snippet,
			'contentDetails': content_details,
			'statistics':     statistics
		}
		return cls(api_response)


class PlaylistResource:
	def __init__(self, response):
		self.kind = response.get('kind')
		self.etag = response.get('etag')
		self.resource_id = response.get('id')
		self.item_id = self.resource_id

		self.snippet = self._parseSnippet(response.get('snippet', {}))
		self.status = self._parseStatus(response.get('status', {}))
		self.content_details = self._parseContentDetails(response.get('contentDetails', {}))
		self.player = self._parsePlayer(response.get('player', {}))
		self.localizations = self._parseLocalizations(response.get('localizations', {}))

		self.data = {**self.snippet, **self.content_details}
		self.data['itemId'] = self.item_id
		self.data['itemType'] = self.kind
		self.data['resourceType'] = self.kind
		self.data['resourceId'] = self.resource_id

	def __getitem__(self, item):
		return self.data.get(item)
	@staticmethod
	def _parseContentDetails(content_details):
		item_count = int(content_details.get('itemCount', 0))

		standard_content_details = {
			'playlistItemCount': item_count
		}
		return standard_content_details

	@staticmethod
	def _parseSnippet(snippet):
		playlist_date = snippet.get('publishedAt')
		if playlist_date:
			playlist_date = timetools.Timestamp(playlist_date)
		else:
			playlist_date = None
		standard_snippet = {
			'playlistDate':        playlist_date,
			'channelId':           snippet.get('channelId'),
			'channelName':         snippet.get('channelTitle', ''),
			'playlistName':        snippet.get('title', ''),
			'playlistDescription': snippet.get('description', ''),
			'playlistTags':        snippet.get('tags', []),
			'playlistLanguage':    snippet.get('defaultLanguage', '')
		}

		return standard_snippet

	@staticmethod
	def _parseStatus(response):
		return response

	@staticmethod
	def _parsePlayer(response):
		return response

	@staticmethod
	def _parseLocalizations(response):
		return response

	def toDict(self, to_sql:bool = False)->Dict:

		data = self.data
		allowed_keys = ['resourceId','resourceType', 'itemId', 'itemType', 'playlistDate', 'playlistName', 'playlistTags', 'playlistDescription', 'playlistLanguage', 'channelId']
		if to_sql:
			data = {k:v for k,v in data.items() if k in allowed_keys}
		return data

	@classmethod
	def fromSql(cls, response:Dict)->'PlaylistResource':
		expected_keys = ['channelId', 'channelName', 'playlistName', 'playlistDescription', 'playlistTags',
						 'playlistLanguage', 'playlistDate', 'resourceId', 'playlistItemCount']
		checkKeys(expected_keys, response.keys())
		snippet = {
			'channelId':       response['channelId'],
			'channelTitle':    response['channelName'],
			'title':           response['playlistName'],
			'description':     response['playlistDescription'],
			'tags':            response['playlistTags'],
			'defaultLanguage': response['playlistLanguage'],
			'publishedAt':     response['playlistDate']
		}

		content_details = {
			'itemCount': response['playlistItemCount']
		}

		api_response = {
			'id':             response['resourceId'],
			'etag':           'fromSql',
			'kind':           "youtube#playlist",
			'snippet':        snippet,
			'contentDetails': content_details
		}
		return cls(api_response)


class PlaylistItemResource:
	def __init__(self, response):
		self.response = response
		self.kind = response.get('kind')
		self.etag = response.get('etag')
		self.resource_id = response.get('id')

		self.snippet = self._parseSnippet(response.get('snippet', {}))
		self.content_details = self._parseContentDetails(response.get('contentDetails', {}))
		self.status = self._parseStatus(response.get('status', {}))

		self.item_id = self.snippet['itemId']
		self.data = {**self.snippet, **self.content_details}
		self.data['itemId'] = self.item_id
		self.data['itemType'] = 'youtube#video'
		self.data['resourceType'] = self.kind
		self.data['resourceId'] = self.resource_id

	def __str__(self):
		playlist_id = self.data['playlistId']
		channel_name = self.data['channelName']
		video_name = self.data['playlistItemName']
		string = "PlaylistItemResource('{}', '{}', '{}')".format(playlist_id, channel_name, video_name)
		return string

	def __getitem__(self, item):
		return self.data.get(item)
	@staticmethod
	def _parseSnippet(response):
		item_position = int(response.get('position', 0))
		item_date = response.get('publishedAt')
		item_resource_info = response.get('resourceId', {})
		resource_type = item_resource_info.get('kind')
		resource_id = item_resource_info.get('videoId')
		if item_date:
			item_date = timetools.Timestamp(item_date)

		standard_snippet = {
			'playlistItemDate':        item_date,
			'channelId':               response.get('channelId'),
			'playlistItemName':        response.get('title'),
			'playlistItemDescription': response.get('description', ''),
			'channelName':             response.get('channelTitle', ''),
			'playlistId':              response.get('playlistId', ''),
			'playlistItemPosition':    item_position,
			'itemId':                  resource_id,
			'itemType':                resource_type
		}
		return standard_snippet

	@staticmethod
	def _parseContentDetails(response):
		return response

	@staticmethod
	def _parseStatus(response):
		return response

	def toDict(self, to_sql:bool = False):
		data = self.data

		allowed_keys = ['playlistId', 'resourceId', 'resourceType', 'itemId', 'itemType', 'playlistItemDate', 'playlistItemName', 'playlistItemDescription', 'playlistItemPosition']
		if to_sql:
			data = {k:v for k,v in data.items() if k in allowed_keys}
		return data

	@classmethod
	def fromSql(cls, response:Dict)->'PlaylistItemResource':
		expected_keys = ['channelId', 'playlistItemName', 'playlistItemDescription', 'channelName', 'playlistId',
						 'playlistItemPosition', 'playlistItemDate', 'resourceId', 'itemId', 'itemType']
		checkKeys(expected_keys,response.keys())
		snippet = {
			'channelId':    response['channelId'],
			'title':        response['playlistItemName'],
			'description':  response['playlistItemDescription'],
			'channelTitle': response['channelName'],
			'playlistId':   response['playlistId'],
			'position':     response['playlistItemPosition'],
			'publishedAt':  response['playlistItemDate'],
			'resourceId':   {
				'videoId': response['itemId'],
				'kind':    response['itemType']
			}
		}

		api_response = {
			'etag':    'fromSql',
			'id':      response['resourceId'],
			'kind':    'youtube#playlistItem',
			'snippet': snippet
		}
		return cls(api_response)


class SearchResource:
	def __init__(self, response):
		self.kind = response.get('kind')
		self.etag = response.get('etag')
		self.resource_id = None
		self.item_id = self._parseId(response.get('id'))
		self.snippet = self._parseSnippet(response.get('snippet', {}))
		self.data = {}

	@staticmethod
	def _parseId(response):
		return response

	@staticmethod
	def _parseSnippet(response):
		item_date = response.get('publishedAt')
		if item_date:
			item_date = timetools.Timestamp(item_date)

		standard_snippet = {
			'itemDate':        item_date,
			'channelId':       response.get('title'),
			'itemName':        response.get('title'),
			'itemDescription': response.get('description'),
			'channelName':     response.get('channelTitle')
		}

		return standard_snippet


class VideoResource:
	def __init__(self, resource):
		self.response = resource
		self.kind = resource['kind']
		self.etag = resource['etag']
		self.resource_id = resource['id']
		self.item_id = self.resource_id

		default_response = dict()

		self.snippet = self._parseSnippet(resource.get('snippet', default_response))
		self.content_details = self._parseContentDetails(resource.get('contentDetails', default_response))
		self.status = self._parseStatus(resource.get('status', default_response))
		self.statistics = self._parseStatistics(resource.get('statistics', default_response))

		self.player = self._parsePlayer(resource.get('player', default_response))
		self.topic_details = self._parseTopicDetails(resource.get('topicDetails', default_response))
		self.recording_details = self._parseRecordingDetails(resource.get('recordingDetails', default_response))
		self.file_details = self._parseFileDetails(resource.get('fileDetails', default_response))
		self.processing_details = self._parseProcessingDetails(resource.get('processingDetails', default_response))
		self.suggestions = self._parseSuggestions(resource.get('suggestions', default_response))
		self.livestream_details = self._parseLivestreamDetails(resource.get('liveStreamingDetails', default_response))
		self.localizations = self._parseLocalizations(resource.get('localizations', default_response))

		standard_id = {
			'resourceId':   self.resource_id,
			'itemId':       self.item_id,
			'itemType':     self.kind,
			'resourceType': self.kind
		}

		self.data = {**standard_id, **self.snippet, **self.content_details, **self.statistics}

	def __str__(self):
		video_name = self.data['videoName']
		channel_name = self.data['channelName']
		string = "VideoResource('{}', '{}')".format(channel_name, video_name)
		return string

	def __getitem__(self, item):
		return self.data.get(item)
	@staticmethod
	def _parseContentDetails(response):

		video_duration = response['duration']
		if video_duration:
			video_duration = timetools.Duration(video_duration)
		else:
			video_duration = None

		standard_content_details = {
			'videoDuration':   video_duration,
			'videoDimension':  response.get('dimension'),
			'videoDefinition': response.get('definition'),
			'videoCaption':    response.get('caption')
		}
		return standard_content_details

	@staticmethod
	def _parseSnippet(response):
		"""
		Parameters
		----------
		response: dict<>
			* "publishedAt": datetime,
    		* "channelId": string,
    		* "title": string,
    		* "description": string,
    		* "thumbnails": dict<>
    		* "channelTitle": string,
    		* "tag s": list<str>
			* "categoryId": string,
   			* "liveBroadcastContent": string,
    		* "defaultLanguage": string,
    		* "localized": dict<>
    		*"defaultAudioLanguage": string
		Returns
		-------
			dict<>
		"""
		publish_date = response.get('publishedAt')
		if publish_date:
			publish_date = timetools.Timestamp(publish_date)
		else:
			publish_date = None

		standard_snippet = {
			'videoName':          response.get('title'),
			'videoDate':          publish_date,
			'channelName':        response.get('channelTitle'),
			'channelId':          response.get('channelId'),
			'videoDescription':   response.get('description', ''),
			'videoCategoryId':    response.get('categoryId', ''),
			'videoLanguage':      response.get('defaultLanguage', ''),
			'videoAudioLanguage': response.get('defaultAudioLanguage', ''),
			'videoTags':          response.get('tags', [])
		}
		return standard_snippet

	@staticmethod
	def _parseStatistics(response):

		standard_statistics = {
			'videoViewCount':     int(response.get('viewCount', 0)),
			'videoCommentCount':  int(response.get('commentCount', 0)),
			'videoLikeCount':     int(response.get('likeCount', 0)),
			'videoDislikeCount':  int(response.get('dislikeCount', 0)),
			'videoFavoriteCount': int(response.get('favoriteCount', 0))
		}
		return standard_statistics

	@staticmethod
	def _parseStatus(response):
		return response

	@staticmethod
	def _parsePlayer(response):
		return response

	@staticmethod
	def _parseTopicDetails(response):
		return response

	@staticmethod
	def _parseRecordingDetails(response):
		return response

	@staticmethod
	def _parseFileDetails(response):
		return response

	@staticmethod
	def _parseProcessingDetails(response):
		return response

	@staticmethod
	def _parseSuggestions(response):
		return response

	@staticmethod
	def _parseLivestreamDetails(response):
		return response

	@staticmethod
	def _parseLocalizations(response):
		return response

	def toDict(self, to_sql:bool = False)->Dict:
		data = self.data
		if to_sql:

			allowed_keys = ['resourceId','resourceType', 'itemId','itemType', 'videoName', 'videoViewCount', 'videoLikeCount', 'videoDislikeCount',
							'videoCommentCount', 'videoFavoriteCount', 'videoDescription', 'videoCaption', 'videoLanguage',
							'videoAudioLanguage', 'videoCategoryId', 'videoDate', 'videoDuration', 'videoDefinition', 'videoDimension',
							'channelId', 'videoTags']
			data = {k:v for k,v in data.items() if k in allowed_keys}
		return data

	@classmethod
	def fromSql(cls, response: Dict) -> 'VideoResource':
		expected_keys = ['videoName', 'videoDate', 'channelName', 'channelId', 'videoDescription', 'videoCategoryId',
						 'videoLanguage', 'videoAudioLanguage', 'videoTags', 'videoDuration', 'videoDimension',
						 'videoDefinition', 'videoCaption', 'videoViewCount', 'videoCommentCount', 'videoDislikeCount',
						 'videoFavoriteCount', 'resourceId']
		checkKeys(expected_keys,response.keys())
		snippet = {
			'title':                response['videoName'],
			'publishedAt':          response['videoDate'],
			'channelTitle':         response['channelName'],
			'channelId':            response['channelId'],
			'description':          response['videoDescription'],
			'categoryId':           response['videoCategoryId'],
			'defaultLanguage':      response['videoLanguage'],
			'defaultAudioLanguage': response['videoAudioLanguage'],
			'tags':                 response['videoTags']
		}
		content_details = {
			'duration':   response['videoDuration'],
			'dimension':  response['videoDimension'],
			'definition': response['videoDefinition'],
			'caption':    response['videoCaption']
		}

		statistics = {
			'viewCount':     response['videoViewCount'],
			'commentCount':  response['videoCommentCount'],
			'likeCount':     response['videoLikeCount'],
			'dislikeCount':  response['videoDislikeCount'],
			'favoriteCount': response['videoFavoriteCount']
		}

		api_response = {
			'etag':           'fromSql',
			'kind':           'youtube#video',
			'id':             response['resourceId'],
			'snippet':        snippet,
			'contentDetails': content_details,
			'statistics':     statistics
		}
		return cls(api_response)
