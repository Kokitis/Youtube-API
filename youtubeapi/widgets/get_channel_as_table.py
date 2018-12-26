import pandas
from youtubeapi.api.data_api import request_channel_videos
def get_channel_videos_as_table(key:str)->pandas.DataFrame:
	channel, channel_uploads, channel_videos = request_channel_videos(key)
	channel_table = list()
	for video in channel_videos:
		row = {
			'videoName': video.name,
			'videoId': video.resourceId,
			'channelName': channel.name,
			'channelId': channel.resourceId,
			'description': video.description,
			'language': video.language,
			'views': video.views,
			'likes': video.likes,
			'dislikes': video.dislikes,
			'comments': video.comments,
			'dimension': video.dimension,
			'duration': video.duration.to_timedelta(),
			'publishDate': video.date.to_iso(),
		}
		channel_table.append(row)
	df = pandas.DataFrame(channel_table)
	return df

if __name__ == "__main__":
	channel_key = "UCjdQaSJCYS4o2eG93MvIwqg"
	result = get_channel_videos_as_table(channel_key)
	print(result.to_string())