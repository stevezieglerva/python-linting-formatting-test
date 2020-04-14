# process_alarms

## Description
Processes CloudWatch alarms for message enrichment and event history and sends alerts to the appropriate SNS topic. Depending on the alarm, different enrichment is added to the alert. Alarms with BASELINE infrastructure send alerts to the ops-aws-alert-baseline SNS topic to inform the BASELINE developers. 

The general event workflow is:

```
alarms are created through BASELINE lambdas ->
    an alarm is triggered in CloudWatch -> 
        message put on ops-aws-alarms SNS -> 
            ops-aws-process-alarms receives the SNS message ->
                alert sent to ops-aws-alerts for the project team ->
                   or
                alert sent to ops-aws-alerts-baseline for the BASELINE development team ->
                    SNS sends emails or texts to any of the SNS topic subscribers
```

## Triggering Event
ops-aws CloudWatch alarms that put notifications on the ops-aws-alarms SNS topic. The typical event processing is:



## Environment Variables
All of the pre-defined environment variables are set in the template and should not be changed.



