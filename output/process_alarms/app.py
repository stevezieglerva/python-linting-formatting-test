import os
import json
import boto3
import datetime
from Alert import *
from LocalTime import *
from EventInfo import *
from alarm_metric_statistics import *
from outliers import Outliers


ALARM_TYPE_NOT_FOUND = 0
ALARM_TYPE_CW_LOG_METRIC = 1
ALARM_TYPE_BASELINE_LAMBDA_FAILURE = 2
ALARM_TYPE_EC2_CPU = 3
ALARM_TYPE_EC2_NETWORKIN = 4


def lambda_handler(event, context):
    print("Starting ...")
    print(os.environ["PROJ_NAME"])
    print(json.dumps(event, indent=3, default=str))
    alarm_text = event["Records"][0]["Sns"]["Message"]
    alarm_json = json.loads(alarm_text)
    print(json.dumps(alarm_json, indent=3))
    alarm_name = alarm_json["AlarmName"]
    metric = ""
    metric_namespace = ""
    (metric_namespace, metric) = get_metric_name_from_alarm(alarm_json)
    timestamp = alarm_json["StateChangeTime"]

    local = LocalTime()
    processing_gmt = local.get_utc_timestamp()
    processing_local = local.get_local_timestamp()
    processing_local_miliseconds = local.get_local_timestamp_miliseconds()

    print(f"*** Need to pivot based on: {metric_namespace} for {alarm_name}")
    log_error_details = ""
    alarm_type = get_alarm_type(metric_namespace, metric, alarm_name)
    need_to_check_outliers = need_to_check_for_outliers(alarm_name)
    if need_to_check_outliers:
        print("checking for outliers")
        metric_stats = get_recent_outliers_for_current_alarm(alarm_name)
        print(json.dumps(metric_stats, indent=3, default=str))
        if metric_stats.get("currently_in_above_threshold_run", False) == False:
            print(f"Metric {metric} is not in a threshold run")
            return {
                "processing_action": f"skipped since not in threshold: {alarm_name}"
            }
        else:
            print(f"Metric {metric} is current in a threshold run")

    if alarm_type == ALARM_TYPE_NOT_FOUND:
        raise ValueError(
            f"Received alarm on {metric_namespace}/{metric} for {alarm_name} but that case is not handled. "
        )

    elif alarm_type == ALARM_TYPE_CW_LOG_METRIC:
        subject = f"Increase in error keywords - {metric}"
        log_group_name = get_log_group_name(metric, metric_namespace)
        log_error_details = log_error_samples(
            processing_local_miliseconds, log_group_name
        )
        message = f"Time:{processing_local}\n\nWe've detected an increase error keywords in the log for the {metric} metric."
        remeadiation = (
            f"Look at the {metric} log in the AWS console for clues to the root cause."
        )

    elif alarm_type == ALARM_TYPE_BASELINE_LAMBDA_FAILURE:
        subject = f"BASELINE Lambda failed - {alarm_name}"
        failing_resource = alarm_json["Trigger"]["Dimensions"][0]["value"]
        log_group_name = f"/aws/lambda/{failing_resource}"
        log_error_details = log_error_samples(
            processing_local_miliseconds, log_group_name
        )
        message = f"Time:{processing_local}\n\nThe BASELINE Lambda for {failing_resource} failed."
        remeadiation = f"Look at the {failing_resource} Cloudwatch log in the AWS console for clues to the root cause."

    elif alarm_type == ALARM_TYPE_EC2_CPU or alarm_type == ALARM_TYPE_EC2_NETWORKIN:
        subject = f"Generic EC2 alarm"
        log_error_details = []
        message = f"Time:{processing_local}\n\nGeneric EC2"
        remeadiation = f"Generic EC2"

    alert = AlertMessage(
        alarm_name,
        subject,
        message,
        remeadiation,
        "",
        "",
        alarm_json,
        os.environ["EVENTS_BUCKET"],
        log_error_details,
    )

    sns_output_topic = get_correct_sns_topic(
        alarm_name, log_error_details, os.environ["SNS_OUTPUT_TEXT"]
    )
    print(f"Using sns_output_topic = {sns_output_topic}")
    send_notification_to_sns_topic = True
    if sns_output_topic == "":
        send_notification_to_sns_topic = False

    if send_notification_to_sns_topic:
        send_notifications(alert, sns_output_topic)
    else:
        print("Skipping SNS notification since doing end-to-end testing")

    print("Finished.")
    result = {
        "processing_action": "alarm processed",
        "alert_message": alert.formatted_text,
        "sns_output_topic": sns_output_topic,
        "send_notification_to_sns_topic": send_notification_to_sns_topic,
    }
    print(json.dumps(result, indent=3))
    return result


def get_alarm_type(metric_namespace, metric, alarm_name):
    if metric_namespace == "ops-aws":
        return ALARM_TYPE_CW_LOG_METRIC
    if metric_namespace == "AWS/EC2" and metric == "CPUUtilization":
        return ALARM_TYPE_EC2_CPU
    if metric_namespace == "AWS/EC2" and metric == "NetworkIn":
        return ALARM_TYPE_EC2_NETWORKIN
    if (
        metric_namespace == "AWS/Lambda"
        and metric == "Errors"
        and "BASELINE" in alarm_name
    ):
        return ALARM_TYPE_BASELINE_LAMBDA_FAILURE
    return ALARM_TYPE_NOT_FOUND


def send_notifications(alert, sns_output_text):
    sns = boto3.client("sns")
    print(f"Sending to {sns_output_text}")
    sns.publish(
        TopicArn=sns_output_text, Subject=alert.subject, Message=alert.formatted_text
    )


def get_correct_sns_topic(alarm_name, log_error_details, regular_sns_alert_topic):
    if "BASELINE" in alarm_name:
        return os.environ["SNS_BASELINE_ERRORS"]
    log_error_lines = ""
    for line in log_error_details:
        log_error_lines = log_error_lines + "\n" + line
    if "end-to-end test suppress email" in log_error_lines:
        return ""
    return regular_sns_alert_topic


def get_log_group_name(metricName, metricNamespace):
    print(f"Getting log group name for {metricName} and {metricNamespace}")
    logs = boto3.client("logs")
    log_group_name = logs.describe_metric_filters(
        metricName=metricName, metricNamespace=metricNamespace
    )
    log_group_name = [
        logname["logGroupName"] for logname in log_group_name["metricFilters"]
    ]
    return log_group_name[0]


def log_error_samples(processing_local_miliseconds, logGroupName):
    sample_matches = []
    logs = boto3.client("logs")
    error_details = logs.filter_log_events(
        logGroupName=logGroupName,
        startTime=processing_local_miliseconds,
        filterPattern="?error ?Error ?ERROR ?exception ?Exception ?EXCEPTION",
        limit=3,
    )
    most_recent_events = [event["message"] for event in error_details["events"]]
    return most_recent_events


def need_to_check_for_outliers(alarm_name):
    if (
        alarm_name
        == "ops-aws-ErrorMetricFilterAlarm-aws-lambda-ops-aws-fake-cw-errors-new"
    ):
        return False
    if "EC2AlarmNetworkIn" in alarm_name:
        return True
    if "ErrorMetricFilterAlarm" in alarm_name:
        return True
    return False


def get_metric_name_from_alarm(alarm_json):
    if "MetricName" in alarm_json["Trigger"]:
        metric = alarm_json["Trigger"]["MetricName"]
        metric_namespace = alarm_json["Trigger"]["Namespace"]
        return (metric_namespace, metric)
    elif "Metrics" in alarm_json["Trigger"]:
        position_index_with_metricstat = 0
        metrics_stat = alarm_json["Trigger"]["Metrics"][
            position_index_with_metricstat
        ].get("MetricStat", "")
        if metrics_stat == "":
            position_index_with_metricstat = 1
        metric = alarm_json["Trigger"]["Metrics"][position_index_with_metricstat][
            "MetricStat"
        ]["Metric"]["MetricName"]
        metric_namespace = alarm_json["Trigger"]["Metrics"][
            position_index_with_metricstat
        ]["MetricStat"]["Metric"]["Namespace"]
        return (metric_namespace, metric)
    else:
        raise ValueError("Can't find metric name in alarm json")
