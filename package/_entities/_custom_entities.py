import datetime
class CustomVideo:

	@property 
	def age(self):
		today = datetime.datetime.now()
		return today - self.publishDate

	@property 
	def publishDate(self):
		raise NotImplementedError
