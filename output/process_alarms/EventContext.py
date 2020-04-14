import boto3
import datetime
import timeago
import json


class EventContext:
	def __init__(self, bucket):
		self.bucket = bucket
		self.last_occurrences_list = self._get_last_occurrences()
		self.last_occurrences_text = self._format_last_occurrences_text()

		

	def _get_last_occurrences(self):
		s3 = boto3.client("s3")
		results = s3.list_objects_v2(Bucket=self.bucket, Prefix="events/last-occurrence")
		file_list = []
		file_list_sorted = []
		for file in results["Contents"]:
			key = file["Key"]
			last_modified = file["LastModified"]
			now = datetime.datetime.now(datetime.timezone.utc)
			new_item = {}
			new_item["key"] = key
			new_item["duration"] = timeago.format(last_modified, now)
			new_item["last_modified"] = last_modified.isoformat()

			event_age = now - last_modified
			if event_age.days >= 30:
				continue

			s3res = boto3.resource('s3')
			obj = s3res.Object(self.bucket, key)
			file = obj.get()['Body'].read().decode("utf-8").replace("'", '"')
			try:
				file_json = json.loads(file)
				if "enrichment_summary" in file_json:
					new_item["enrichment_summary"] = file_json["enrichment_summary"]
					print(f"Found enrichment_summary field in {key}")
			except:
				print(f"Error: Unable to parse json from {key}. Skipping looking for the enrichment_summary field")
			file_list.append(new_item)
			file_list_sorted = sorted(file_list, key = lambda i: i['last_modified'], reverse=True)
		return file_list_sorted
		

	def _format_last_occurrences_text(self):
		text = ""
		last_text = ""
		for event in self.last_occurrences_list:
			duration = event["duration"]
			desc = event["key"].replace("events/last-occurrence/", "").replace("__", " ")
			new_text = f"{duration:<15} {desc}\n"
			text = self._add_spacer(text, last_text, "seconds", new_text, "minutes")
			text = self._add_spacer(text, last_text, "minutes", new_text, "hours")
			text = self._add_spacer(text, last_text, "minutes", new_text, "hour ")
			text = self._add_spacer(text, last_text, "hour ", new_text, "hours")
			text = self._add_spacer(text, last_text, "hours", new_text, "days")
			text = self._add_spacer(text, last_text, "hours", new_text, "day ")
			text = self._add_spacer(text, last_text, "hours", new_text, "days")
			text = text + new_text
			if "enrichment_summary" in event:
				padding = " " * 15
				enrichment_summary = event["enrichment_summary"]
				text = text + f"{padding}    {enrichment_summary}\n"
			last_text = new_text
		return text


	def _add_spacer(self, text, last_text, last_uom, new_text, new_uom):
		if last_uom in last_text and new_uom in new_text:
			text = text + "-" * 40 + "\n"
		return text