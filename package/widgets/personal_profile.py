"""
	Widgets pertaining to common operations to perform on the personal channel.
"""
import os
import pandas

def importSubscriptions(youtube, subscriptions, whitelist = None, start_index = 0):
	"""
		Imports all subscriptions.
	Parameters
	----------
	youtube: YoutubeDatabase
	subscriptions: dict

	Returns
	-------

	"""
	if whitelist is None:
		whitelist = list(subscriptions.keys())
	all_metrics = list()
	database_name = os.path.basename(youtube.filename)
	metrics_filename = os.path.join(os.path.dirname(youtube.filename), database_name + '_import_metrics.xlsx')
	index = 0
	# pprint(subscriptions)

	for index, element in enumerate(sorted(subscriptions.items())):
		if index < start_index:
			continue
		channel_name, channel_id = element
		if channel_name not in whitelist:
			continue
		index += 1
		print("\n{} of {}".format(index, len(subscriptions)))
		metrics = youtube.importChannel(channel_id)
		if metrics is None:
			metrics = [{
				'itemKind':        'channel',
				'itemId':          channel_id,
				'itemName':        channel_name,
				'itemChannelName': channel_name,
				'itemChannelId':   channel_id
			}]
		all_metrics += metrics
		metrics_df = pandas.DataFrame(all_metrics)
		metrics_df.to_excel(metrics_filename)