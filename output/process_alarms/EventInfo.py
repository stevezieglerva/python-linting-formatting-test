import boto3
import os
import json
from datetime import datetime


def create_event(event_source, event_name, event_json, s3_bucket):
    event_source = event_source
    event_name = event_name
    event_json = event_json
    s3_bucket = s3_bucket

    timestamp = datetime.now().isoformat()
    event_json["eventProcessingTimestamp"] = timestamp
    event_desc = f"{event_source}__{event_name}.json"
    if "simple_description" in event_json:
        event_desc = event_json["simple_description"].replace(" ", "__") + ".json"

    last_occurrence_key = f"events/last-occurrence/{event_desc}"
    escaped_time = timestamp[11:23].replace(":", "-")
    history_key = f"events/history/{timestamp[0:4]}/{timestamp[5:7]}/{timestamp[8:10]}/{escaped_time}_{event_desc}"

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=s3_bucket, Key=last_occurrence_key, Body=json.dumps(event_json, indent=3)
    )
    s3.put_object(
        Bucket=s3_bucket, Key=history_key, Body=json.dumps(event_json, indent=3)
    )

    results = {"last_occurrence_key": last_occurrence_key, "history_key": history_key}
    return results
