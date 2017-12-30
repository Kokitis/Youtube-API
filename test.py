from package import YouTube, YouTubeDatabase, github, ApiResponse
from pprint import pprint
import pandas
import os
import json

API_KEY = github.youtube_api_key
subscriptions = github.youtube_subscriptions

filename = os.path.join(os.path.dirname(__file__), "RT_video_database.sqlite")

if __name__ == '__main__':
	print("Running Tests...")
	test_video = "FrLgREKD4kk"
	test_channel = "UCjdQaSJCYS4o2eG93MvIwqg"
	test_playlist = "PL1cXh4tWqmsEQPeLEJ5V3k5knt-X9k043"
	youtube = YouTubeDatabase(API_KEY, filename = 'videos - 2017-12-28')
	
	#youtube.importChannel(test_channel)
	
	if True:
		all_metrics = list()
		f_name = os.path.join(os.path.dirname(__file__), 'import_metrics.json')
		index = 0
		#pprint(subscriptions)
		for key, value in sorted(subscriptions.items()):
			index += 1
			if value != 'UCsB0LwkHPWyjfZ-JwvtwEXw': 
				pass
			print("\n{} of {}".format(index, len(subscriptions)))
			metrics = youtube.importChannel(value)
			if metrics is None:
				metrics = [{
					'itemKind': 'channel',
					'itemId': value,
					'itemName': key,
					'itemChannelName': key,
					'itemChannelId': value
				}]
			all_metrics += metrics
			metrics_df = pandas.DataFrame(all_metrics)
			metrics_df.to_excel('import_metrics.xlsx')

