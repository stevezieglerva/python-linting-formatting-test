import boto3
import json
from datetime import datetime, timedelta
from outliers import Outliers


def get_recent_outliers_for_current_alarm(alarm_name):
	metric_details = get_metric_dimensions_from_alarm(alarm_name)
	statistic = metric_details["Statistic"]
	metrics = get_metric_statistics(metric_details)
	raw_data = [i[statistic] for i in metrics]
	outliers = Outliers()
	stats_info = outliers.get_statistics(raw_data, 2, 4)
	stats_info["AlarmName"] = alarm_name
	stats_info["Metric"] = metric_details

	run_timestamps = []
	for run in stats_info["above_threshold_runs"]:
		first_run_item = run[0]
		list_position = first_run_item["list_position"]
		raw_item = metrics[list_position]
		start_timestamp = raw_item["Timestamp"]

		last_run_item = run[len(run) - 1]
		list_position = last_run_item["list_position"]
		raw_item = metrics[list_position]
		end_timestamp = raw_item["Timestamp"]

		run_timestamp = {"start" : start_timestamp, "end" : end_timestamp, "occurences_during_run" : len(run)}
		run_timestamps.append(run_timestamp)
	stats_info["run_timestamps"] = run_timestamps

	return stats_info


def get_outliers_for_all_alarms():
	cloudwatch = boto3.client("cloudwatch")
	alarms = cloudwatch.describe_alarms()
	alarm_names = [i["AlarmName"] for i in alarms["MetricAlarms"]]
	results = []
	count = 0
	for alarm in alarm_names:
		count = count + 1
		print(f"\n\nAlarm: {count}. {alarm}")
		outliers = get_recent_outliers_for_alarm(alarm)
		avg = outliers["average"]
		perc_diff = ""
		if avg != 0:
			perc_diff = round((outliers["upper_limit"] / avg) * 100, 0)
		alarm_info = {}
		alarm_info["alarm"] = alarm
		alarm_info["metric_value:"] = f"\taverage: {avg} +- {perc_diff}%"
		alarm_info["run_timestamps:"] = outliers["run_timestamps"]
		results.append(alarm_info)
	return results


def get_metric_dimensions_from_alarm(alarm_name):
	cloudwatch = boto3.client("cloudwatch")
	alarms = cloudwatch.describe_alarms(AlarmNames=[alarm_name])

	if len(alarms["MetricAlarms"]) == 1:
		alarm_info = alarms["MetricAlarms"][0]
		metric_name = ""
		metric_namespace = ""
		dimensions = []
		statistic = ""
		if "MetricName" in alarm_info:
			metric_name = alarm_info["MetricName"]
			metric_namespace = alarm_info["Namespace"]
			dimensions = alarm_info["Dimensions"]
			statistic = alarm_info["Statistic"]
		else:
			metric_position_index = 0
			if "MetricStat" in alarm_info["Metrics"][1]:
				metric_position_index = 1
			metric_name = alarm_info["Metrics"][metric_position_index]["MetricStat"]["Metric"]["MetricName"]
			metric_namespace = alarm_info["Metrics"][metric_position_index]["MetricStat"]["Metric"]["Namespace"]
			dimensions = alarm_info["Metrics"][metric_position_index]["MetricStat"]["Metric"]["Dimensions"]
			statistic = alarm_info["Metrics"][metric_position_index]["MetricStat"]["Stat"]

		metric_details = {"MetricName" : metric_name,
						"MetricNamespace" : metric_namespace,
						"Dimensions" : dimensions,
						"Statistic" : statistic
						}
		return metric_details
	else:
		assert ValueError("cloudwatch.describe_alarms did not return a single alarm")


def get_metric_statistics(metric_details):
	namespace = metric_details["MetricNamespace"]
	metric = metric_details["MetricName"]
	statistic = metric_details["Statistic"]
	dimensions = metric_details["Dimensions"]
	period = 60

	datapoints = []
	cloudwatch = boto3.client("cloudwatch")
	for i in range(0, 5):
		today_offset = i
		yesterday_offest = i + 1
		end_day = datetime.now()- timedelta(days=today_offset)
		end_time = end_day.isoformat()
		start_day = datetime.now() - timedelta(days=yesterday_offest)
		start_time = start_day.isoformat()
		api_results = cloudwatch.get_metric_statistics(Namespace=namespace, MetricName=metric, StartTime=start_time, EndTime=end_time, Period=period, Statistics=[statistic], Dimensions=dimensions)
		datapoints.extend(api_results["Datapoints"])
	datapoints_sorted = sorted(datapoints, key=lambda i: i['Timestamp'])
	return datapoints_sorted

