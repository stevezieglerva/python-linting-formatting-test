import datetime, time
import pytz


class LocalTime:
	def __init__(self, local_timezone = "America/New_York"):
		self.local_timezone = local_timezone
		self.utc = pytz.utc.localize(datetime.datetime.utcnow())
		self.local = self.utc.astimezone(pytz.timezone(self.local_timezone))

	def __str__(self):
		formatted = str(self.local) + " " + self.local_timezone + " (" + str(self.utc) + " UTC)"
		return formatted
		
	def now(self):
		self.utc = pytz.utc.localize(datetime.datetime.utcnow())
		self.local = self.utc.astimezone(pytz.timezone(self.local_timezone))
		return str(self)

	def get_utc_epoch_date(self):
		epoch_date = datetime.datetime(1970, 1, 1, 0, 0, 0)
		utc_epoch_date = pytz.utc.localize(epoch_date)
		return utc_epoch_date

	def get_utc_epoch(self):
		utc_epoch_date = self.get_utc_epoch_date()
		self.now()
		return (self.utc - utc_epoch_date).total_seconds()


	def get_epoch_plus_seconds(self, seconds):
		local_time = LocalTime()
		expiration = local_time.utc + datetime.timedelta(seconds=seconds)
		utc_epoch_date = self.get_utc_epoch_date()
		expiration_epoch =  (expiration - utc_epoch_date).total_seconds()
		return  int(expiration_epoch) 	

	def get_utc_timestamp(self):
		return self.utc.strftime("%Y-%m-%dT%H:%M:%S.%f")


	def get_local_timestamp(self):
		return self.local.strftime("%Y-%m-%dT%H:%M:%S.%f")

	def get_local_timestamp_miliseconds(self):
		return int(round(time.time() * 1000) - 300000)
		#subtracting 5 minutes to get logs from just before alarm
