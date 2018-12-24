from typing import Dict, List, Iterable
from dataclasses import dataclass


@dataclass
class ChannelResource:
	resourceId: str
	resourceType: str
	itemId: str
	itemType: str
	name: str
	description: str
	url: str
	language: str
	country: str
	uploads: str
	videos: int
	views: int
	comments: int
	subscribers: int


def checkKeys(expected_keys: List[str], provided_keys: Iterable) -> None:
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


def _parse_content_details(content_details: Dict) -> Dict:
	related_playlists = content_details.get('relatedPlaylists', {})
	standard_content_details = {
		'channelUploadPlaylist': related_playlists.get('uploads')
	}
	return standard_content_details


def _parse_statistics(statistics: Dict) -> Dict:
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


def _parseTopicDetails(response: Dict) -> Dict:
	return response


def _parseStatus(response: Dict) -> Dict:
	return response


def _parseBrandingSettings(response: Dict) -> Dict:
	return response


def _parseAuditDetails(response: Dict) -> Dict:
	return response


def _parseContentOwnerDetails(response: Dict) -> Dict:
	return response


def _parseLocalizations(response: Dict) -> Dict:
	return response


def _parse_snippet(snippet: Dict) -> Dict:
	standard_snippet = {
		'channelName':        snippet.get('title', ''),
		'channelDescription': snippet.get('description', ''),
		'channelUrl':         snippet.get('customUrl', ''),
		'channelLanguage':    snippet.get('defaultLanguage', ''),
		'channelCountry':     snippet.get('country', '')
	}
	return standard_snippet


def parse_channel_resource(response: Dict, include_all: bool = False) -> ChannelResource:
	""" Parses a channel response from the API and returns a standardized ChannelResponse object."""
	kind = response.get('kind')
	resource_id = response.get('id')
	item_id = resource_id

	default_response = dict()

	snippet = _parse_snippet(response.get('snippet', default_response))

	content_details = _parse_content_details(response.get('contentDetails', default_response))
	statistics = _parse_statistics(response.get('statistics', default_response))
	if include_all:
		# All these parsers currently return the original object.
		topic_details = _parseTopicDetails(response.get('topicDetails', default_response))
		status = _parseStatus(response.get('status', default_response))
		branding_settings = _parseBrandingSettings(response.get('brandingSettings', default_response))
		audit_details = _parseAuditDetails(response.get('auditDetails', default_response))
		content_owner_details = _parseContentOwnerDetails(response.get('contentOwnerDetails'))
		localizations = _parseLocalizations(response.get('localizations', default_response))

	parsed_response = ChannelResource(
		resourceId = resource_id,
		resourceType = kind,
		itemId = item_id,
		itemType = kind,
		name = snippet['channelName'],
		description = snippet['channelDescription'],
		url = snippet['channelUrl'],
		language = snippet['channelLanguage'],
		country = snippet['channelCountry'],
		uploads = content_details['channelUploadPlaylist'],
		videos = statistics['channelVideoCount'],
		views = statistics['channelViewCount'],
		comments = statistics['channelCommentCount'],
		subscribers = statistics['channelSubscriberCount']
	)

	return parsed_response


if __name__ == "__main__":
	from pathlib import Path
	import json

	contents = json.loads(Path("sample_channel_resource.json").read_text())
	result = parse_channel_resource(contents['items'][0])
	print(result)
