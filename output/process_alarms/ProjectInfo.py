import boto3
import os


class ProjectInfo:
    def __init__(self):
        self.set_project_info()

    def set_project_info(self):
        self.project_abbr = os.environ["PROJ_ABBR"]
        self.project_name = os.environ["PROJ_NAME"]
        self.pm_email = os.environ["PM_EMAIL"]
        self.tech_lead_email = os.environ["TECH_LEAD_EMAIL"]
        self.prod_url = os.environ["PROD_URL"]

    def __str__(self):
        text = f"""Project Name: {self.project_name}
PM Email: {self.pm_email}
Tech Lead Email: {self.tech_lead_email}
Prod URL: {self.prod_url}
"""
        return text
