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
	youtube = YouTubeDatabase(API_KEY)
	
	#youtube.importChannel(test_channel)
	
	if True:

		all_metrics = dict()
		f_name = os.path.join(os.path.dirname(__file__), 'import_metrics.json')
		index = 0
		#pprint(subscriptions)
		for key, value in sorted(subscriptions.items()):
			index += 1
			print("\n{} of {}".format(index, len(subscriptions)))
			metrics = youtube.importChannel(value)
			all_metrics[key] = metrics
		
		with open(f_name, 'w') as file1:
			file1.write(json.dumps(all_metrics, sort_keys = True, indent = 4))

