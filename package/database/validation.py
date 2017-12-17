import math
from datetime import datetime, timedelta
from ..github import timetools
def debugEntity(label, entity):
	""" Convientience method to display the arguments
		used in a failed attempt to create a new entity 
	"""
	print("Entity: {}".format(label))
	print("\tType: ", type(entity))
	if isinstance(entity, dict):
		for k, v in sorted(entity.items()):
			print("\t{}:\t{}".format(k, v))
	else:
		print("\t", entity)

def isNull(value):
	""" Checks if a value should be considered null.
		Returns True if the value is None or has a value of nan 
	"""
	is_null = value is None
	if not is_null and isinstance(value, float):
		is_null = math.isnan(value)
	return is_null

def isNumber(value):
	""" Checks if a value is a numeric type or if all characters in the string are digits.
		Parameters
		----------
			value: int, float, str
	"""
	is_numeric_type = isinstance(value, (int, float))
	is_all_digit = is_numeric_type or (isinstance(value, str) and value.isdigit())
	return is_all_digit

def parseKeywords(columns, keys, cls = None, return_type = 'values', default_value = None):
	"""
		Parameters
		----------
		columns: list<str>
			A list of the columns in the table.
		keys: list<str>
			A list of the possible column names that hold the
			desired information.
			Ex. 'country', 'regionName', 'countryName' to
			extract the column with the region's name
		return_type: {'columns', 'values'}; default 'values'
			* 'columns': returns the column in the table that was found.
			* 'values': returns the value contained in the column that was found.
		cls: class(obj); default None
			A function or class to convert the resulting values to.
		default_value: scalar; default None
			The default value to return.
	"""

	if hasattr(columns, 'keys'):
		data = columns
		columns = data.keys()
	elif hasattr(columns, 'columns'):
		data = columns
		columns = data.columns
	else:
		# Assume a list of str
		data = dict()
		return_type = 'columns'

	candidates = [col for col in columns if col in keys]
	if len(candidates) == 0:
		value = None
	elif return_type == 'columns':
		value = candidates[0]
	elif return_type == 'values':
		value = candidates[0]
		value = data[value]
	else:
		message = "Invalid return type: '{}'".format(return_type)
		raise ValueError(message)
	if cls:
		try:
			value = cls(value)
		except TypeError:
			value = default_value
		except ValueError:
			value = default_value

	return value


def _removeMissingVars(values):
	return {k:v for k,v in values.items() if v is not None and str(v) != 'nan'}


def parseEntityArguments(entity_type, entity_args = None, **kwargs):
	"""
		Parameters
		----------
			entity_type: {'channel', 'playlist', 'tag', 'video'}
			entity_args: dict<str:scalar>

	"""

	if entity_args is None:
		result = kwargs
	else:
		result = entity_args

	if not isinstance(entity_type, str):
		entity_type = entity_type.entity_type
	entity_type = entity_type.lower()
	

	if entity_type == 'tag':
		args = {
			'string': parseKeywords(result, ['string', 'tag', 'seriesTags', 'tags'])
		}
	elif entity_type == 'video':
		args = {
			'id': parseKeywords(result, ['videoId', 'id']),
			'title': parseKeywords(result, ['videoName', 'name', 'title']),
			'views': parseKeywords(result, ['views', 'viewCount', 'videoViewCount'], int),
			'likes': parseKeywords(result, ['likes', 'likeCount', 'videoLikeCount'], int),
			'dislikes': parseKeywords(result, ['dislikes', 'dislikeCount', 'videoDislikeCount'], int),
			'publishDate': parseKeywords(result, ['publishDate', 'publishedAt', 'videoPublishDate'], timetools.Timestamp),
			'duration': parseKeywords(result, ['duration', 'length', 'videoDuration']),
			#'updatedAt': "",
			'channel': parseKeywords(result, ['channel']),
			'description': parseKeywords(result, ['description', 'videoDescription']),
			'tags': parseKeywords(result, ['tags', 'videoTags'])
		}
		if args['duration'] is not None:
			args['duration'] = timetools.Duration(args['duration'])
		#args['duration'] = args['duration'].toTimeDelta()
	elif entity_type == 'playlist':
		args = {
			'id': parseKeywords(result, ['id', 'playlistId']),
			'name': parseKeywords(result, ['name', 'playlistName']),
			'channel': parseKeywords(result, ['channel', 'playlistChannel'])
		}
	elif entity_type == 'tag':
		args = {
			'string': parseKeywords(result, ['string', 'tag'])
		}
	elif entity_type == 'channel':
		args = {
			'id': parseKeywords(result, ['channelId', 'id']),
			'name': parseKeywords(result, ['channelName', 'name', 'title']),
			'country': parseKeywords(result, ['country']),
			'creationDate': parseKeywords(result, ['creationDate', 'publishedAt'], timetools.Timestamp),
			'description': parseKeywords(result, ['description']),
			'subscriberCount': parseKeywords(result, ['subscriberCount', 'subscribers'], int),
			'videoCount': parseKeywords(result, ['videoCount'], int),
			'viewCount': parseKeywords(result, ['views', 'viewCount'], int)
		}
	else:
		message = "ParseEntityArguments: The requested entity type ('{}') does not exist!".format(entity_type)
		raise ValueError(message)

	args = _removeMissingVars(args)
	if len(args) == 0: args = None
	return args

from pprint import pprint
def validateEntity(entity_type, **data):
	""" Validates that an entity is properly defined.
		Used to ensure the data can be used to create a new instance
		of an entity.
		Parameters
		----------
			entity_type: str
			data: dict
	"""

	pprint(data)

	validation = dict()
	if entity_type == 'channel':
		for key in ['id', 'name', 'description']:
			value = data.get(key)
			validation[key] = (value, isinstance(value, str))
		for key in ['subscriberCount', 'videoCount', 'viewCount']:
			value = data.get(key)
			validation[key] = (value, isinstance(value, int))
		value = data.get('creationDate')
		validation['creationDate'] = (value, isinstance(value, datetime))

	elif entity_type == 'playlist':
		for key in ['id', 'name']:
			value = data.get(key)
			validation[key] = (value, isinstance(value, str))
		value = data.get('channel')
		validation['channel'] = (value, hasattr(value, 'entity_type') and value.entity_type == 'channel')

	elif entity_type == 'tag':
		value = data.get('string')
		validation['string'] = (value, isinstance(value, str))
	elif entity_type == 'video':
		for key in ['id', 'name', 'description', 'videoName']:
			value = data.get(key)
			validation[key] = (value, isinstance(value, str))
		for key in ['views', 'likes', 'dislikes']:
			value = data.get(key)
			validation[key] = (value, isinstance(value, int))
		value = data.get('publishDate')
		validation['publishDate'] = (value, isinstance(value, datetime))
		value = data.get('duration')
		validation['duration'] = (value, isinstance(value, timedelta))

	else:
		message = "'{}' is not a supported entity type.".format(entity_type)
		raise ValueError(message)

	valid = all(i[1] for i in validation.values())


	if not valid:
		print("[validateEntity] The entity had one or more errors:")
		print("Entity Type: ", entity_type)
		print()
		for key, value in sorted(validation.items()):
			a = value[0] if not value[1] else ""
			print(key, '\t', a, '\t', value[1])
	
	return valid


