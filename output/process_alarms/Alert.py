"""Alert module for the Alert class that formats and saves alert info"""

import datetime
import boto3
import json
from ProjectInfo import *
from EventInfo import *
from EventContext import *


class AlertMessage:
    """Alert message details"""

    def __init__(
        self,
        alert_name,
        subject,
        simple_message,
        remediation,
        project_info,
        context,
        event_details_json,
        s3_bucket,
        log_error_details,
    ):
        self.alert_name = alert_name
        self.subject = subject
        self.simple_message = simple_message
        self.remediation = remediation
        self.context = context
        self.event_details_json = event_details_json
        self.project_info = ProjectInfo()
        self.event_context = EventContext(s3_bucket)

        log_error_text = ""
        for error in log_error_details:
            stripped_error = error.strip()
            log_error_text = log_error_text + f"- {stripped_error}\n"
        self.log_error_details = log_error_text

        self.formatted_text = self._format_text()
        self.formatted_html = self._format_text()

        alert_json = {
            "alert": self.formatted_text,
            "simple_description": f"alert {subject}",
        }

        event_results = self._create_event(alert_name, alert_json, s3_bucket)
        print(json.dumps(event_results, indent=3, default=str))

        self._save(s3_bucket)

    def _create_event(self, alert_name, alert_json, s3_bucket):
        return create_event("alert", alert_name, alert_json, s3_bucket)

    def __str__(self):
        return self.formatted_text()

    def _format_text(self):
        event_context_text = self.event_context.last_occurrences_text
        text = f""" 
Subject: 
{self.subject}

Message: 
{self.simple_message}

Log Info: 
{self.log_error_details}

Remediation:
{self.remediation}


Project Info:
{str(self.project_info)}

Recent Changes:
{event_context_text}
	"""
        return text

    def _save(self, bucket):
        s3 = boto3.client("s3")
        timestamp = datetime.datetime.now().isoformat()
        timestamp = timestamp.replace(":", "_")
        alert_filename = self.alert_name.replace(" ", "__")
        key = f"alerts/{alert_filename}/{timestamp}.json"
        print(f"Writing {key}")
        s3.put_object(Bucket=bucket, Key=key, Body=self.formatted_text)
        return key
