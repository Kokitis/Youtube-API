from package.github import timetools
from pprint import pprint


# https://developers.google.com/youtube/v3/docs/playlists

class ListResource:
	def __init__(self, api_response):

		self.response = api_response
		if 'error' in api_response:
			pprint(api_response)
			self.kind = 'youtube#error'
			self.status_code = api_response['statusCode']
		else:
			self.status_code = 200
			self.kind = api_response.get('kind')  # should be 'youtube#videoListResponse'
		self.etag = api_response.get('etag')
		self.next_page_token = api_response.get('nextPageToken')
		self.previous_page_token = api_response.get('prevPageToken')
		self.page_info = api_response.get('pageInfo')
		self.items = [self.getResource(i) for i in api_response.get('items', [])]

	def __str__(self):
		if self.status_code == 200:
			string = "ListResource('{}', {})".format(self.etag, len(self.items))
		else:
			string = "ListResource('error', {})".format(self.status_code)
		return string

	def __getitem__(self, item):
		return self.items[item]

	def __len__(self):
		return len(self.items)

	@staticmethod
	def _handleError(error):
		pprint(error)

	def summary(self):
		print(self)
		print("itemCount: ", len(self.items))
		for i in self.items:
			print("\t", i)

	@staticmethod
	def getResource(item):
		item_kind = item['kind']
		if item_kind == 'youtube#video':
			item_resource = VideoResource(item)
		elif item_kind == 'youtube#channel':
			item_resource = ChannelResource(item)
		elif item_kind == 'youtube#playlist':
			item_resource = PlaylistResource(item)
		elif item_kind == 'youtube#playlistItem':
			item_resource = PlaylistItemResource(item)
		elif item_kind == 'youtube#searchResult':
			item_resource = SearchResource(item)
		else:
			message = "'{}' is not a supported resource!".format(item_kind)
			raise ValueError(message)
		return item_resource


class ChannelResource:
	def __init__(self, response):
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
	def __str__(self):
		channel_name = self.snippet['channelName']
		string = "ChannelResource('{}')".format(channel_name)
		return string
	def __getitem__(self, item):
		return self.data.get(item)
	@staticmethod
	def _parseSnippet(snippet):
		standard_snippet = {
			'channelName':        snippet.get('title'),
			'channelDescription': snippet.get('description'),
			'channelUrl':         snippet.get('customUrl'),
			'channelLanguage':    snippet.get('defaultLanguage'),
			'channelCountry':     snippet.get('country')
		}
		return standard_snippet

	@staticmethod
	def _parseContentDetails(content_details):
		related_playlists = content_details.get('relatedPlaylists', {})
		standard_content_details = {
			'channelUploadPlaylist': related_playlists.get('uploads')
		}
		return standard_content_details

	@staticmethod
	def _parseStatistics(statistics):
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
	def _parseTopicDetails(response):
		return response

	@staticmethod
	def _parseStatus(response):
		return response

	@staticmethod
	def _parseBrandingSettings(response):
		return response

	@staticmethod
	def _parseAuditDetails(response):
		return response

	@staticmethod
	def _parseContentOwnerDetails(response):
		return response

	@staticmethod
	def _parseLocalizations(response):
		return response


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
			'channelName':         snippet.get('channelTitle'),
			'playlistName':        snippet.get('title'),
			'playlistDescription': snippet.get('description'),
			'playlistTags':        snippet.get('tags'),
			'playlistLanguage':    snippet.get('defaultLanguage')
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

	def __str__(self):
		playlist_id = self.data['playlistId']
		channel_name = self.data['channelName']
		video_name = self.data['playlistItemName']
		string = "PlaylistItemResource('{}', '{}', '{}')".format(playlist_id, channel_name, video_name)
		return string

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
			'playlistItemDescription': response.get('description'),
			'channelName':             response.get('channelTitle'),
			'playlistId':              response.get('playlistId'),
			'position':                item_position,
			'itemId': resource_id,
			'itemType': resource_type
		}
		return standard_snippet

	@staticmethod
	def _parseContentDetails(response):
		return response

	@staticmethod
	def _parseStatus(response):
		return response
	def toDict(self):
		pass


class SearchResource:
	def __init__(self, response):
		self.kind = response.get('kind')
		self.etag = response.get('etag')
		self.resource_id = None
		self.item_id = self._parseId(response.get('id'))
		self.snippet = self._parseSnippet(response.get('snippet', {}))

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
			'resourceType': self.kind,
			'resourceId':   self.resource_id,
			'itemId': self.item_id,
			'itemType': 'video'
		}

		self.data = {**standard_id, **self.snippet, **self.content_details, **self.statistics}

	def __str__(self):
		video_name = self.data['videoName']
		video_id = self.item_id
		channel_name = self.data['channelName']
		string = "VideoResource('{}', '{}')".format(channel_name, video_name)
		return string

	def toStandard(self):
		return self.data

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
			'videoDescription':   response.get('description'),
			'videoCategoryId':    response.get('categoryId'),
			'videoLanguage':      response.get('defaultLanguage'),
			'videoAudioLanguage': response.get('defaultAudioLanguage'),
			'videoTags':          response.get('tags')
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

