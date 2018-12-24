from typing import Dict, List, Any
from dataclasses import dataclass
from pytools import timetools


@dataclass
class VideoResource:
	resourceId: str
	resourceType: str
	itemId: str
	itemType: str
	name: str
	channelName: str
	channelId: str
	date: timetools.Timestamp
	description: str
	#category: str
	language: str
	audioLanguage: str
	tags: List[str]
	views: int
	likes: int
	dislikes: int
	comments: int
	favorites: int
	duration: timetools.Duration
	dimension: str
	definition: str
	caption: str


def parse_video_response(resource: Dict, include_all: bool = False) -> VideoResource:
	kind = resource['kind']
	resource_id = resource['id']
	item_id = resource_id

	default_response = dict()

	snippet = _parse_snippet(resource.get('snippet', default_response))
	content_details = _parse_content_details(resource.get('contentDetails', default_response))
	statistics = _parse_statistics(resource.get('statistics', default_response))
	if include_all:
		status = _parse_status(resource.get('status', default_response))
		player = _parse_player(resource.get('player', default_response))
		topic_details = _parse_topic_details(resource.get('topicDetails', default_response))
		recording_details = _parse_recording_details(resource.get('recordingDetails', default_response))
		file_details = _parse_file_details(resource.get('fileDetails', default_response))
		processing_details = _parse_processing_details(resource.get('processingDetails', default_response))
		suggestions = _parse_suggestions(resource.get('suggestions', default_response))
		livestream_details = _parse_livestream_details(resource.get('liveStreamingDetails', default_response))
		localizations = _parse_localizations(resource.get('localizations', default_response))

	parsed_resource = VideoResource(
		resourceId = resource_id,
		resourceType = kind,
		itemId = item_id,
		itemType = kind,
		name = snippet['videoName'],
		date = snippet['videoDate'],
		channelName = snippet['channelName'],
		channelId = snippet['channelId'],
		description = snippet['videoDescription'],
		#category = snippet['categoryId'],
		language = snippet['videoLanguage'],
		audioLanguage = snippet['videoAudioLanguage'],
		tags = snippet['videoTags'],
		views = statistics['videoViewCount'],
		likes = statistics['videoLikeCount'],
		dislikes = statistics['videoDislikeCount'],
		comments = statistics['videoCommentCount'],
		favorites = statistics['videoFavoriteCount'],
		duration = content_details['videoDuration'],
		dimension = content_details['videoDimension'],
		definition = content_details['videoDefinition'],
		caption = content_details['videoCaption']
	)
	return parsed_resource


def _parse_content_details(response: Dict[str, str]) -> Dict[str, Any]:
	video_duration = response.get('duration')
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


def _parse_snippet(response: Dict[str, str]) -> Dict[str, Any]:
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


def _parse_statistics(response: Dict[str, str]) -> Dict[str, Any]:
	standard_statistics = {
		'videoViewCount':     int(response.get('viewCount', 0)),
		'videoCommentCount':  int(response.get('commentCount', 0)),
		'videoLikeCount':     int(response.get('likeCount', 0)),
		'videoDislikeCount':  int(response.get('dislikeCount', 0)),
		'videoFavoriteCount': int(response.get('favoriteCount', 0))
	}
	return standard_statistics


def _parse_status(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_player(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_topic_details(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_recording_details(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_file_details(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_processing_details(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_suggestions(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_livestream_details(response: Dict[str, str]) -> Dict[str, Any]:
	return response


def _parse_localizations(response: Dict[str, str]) -> Dict[str, Any]:
	return response


if __name__ == "__main__":
	import yaml
	from pathlib import Path

	data = yaml.load(Path("/home/proginoskes/Documents/GitHub/YoutubeAPI/tests/sample_video_response.yaml").read_text())
	result = parse_video_response(data['items'][0])
	print(result)
