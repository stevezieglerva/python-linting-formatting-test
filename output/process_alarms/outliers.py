import statistics


class Outliers:
    def __init__(self):
        pass

    def get_statistics(self, data_list, num_of_stdevs, periods_of_anomaly):
        return self._get_stats_on_list(data_list, num_of_stdevs, periods_of_anomaly)

    def _get_stats_on_list(self, data, num_of_stdevs, periods_of_anomaly=2):
        stats = {}
        if len(data) < 2:
            stats["number_of_items"] = 0
            stats["num_of_stdevs"] = num_of_stdevs
            stats["periods_of_anomaly"] = periods_of_anomaly
            stats["average"] = 0
            stats["stdev"] = 0
            stats["upper_limit"] = 0
            stats["lower_limit"] = 0
            stats["above_threshold"] = []
            stats["above_threshold_runs"] = []
            stats["below_threshold"] = []
            stats["below_threshold_runs"] = []
            return stats

        mean = statistics.mean(data)
        stdev = statistics.stdev(data)
        stats["number_of_items"] = len(data)
        stats["num_of_stdevs"] = num_of_stdevs
        stats["periods_of_anomaly"] = periods_of_anomaly

        stats["average"] = round(mean, 2)
        stats["stdev"] = round(stdev, 2)
        upper_limit = mean + stdev * num_of_stdevs
        stats["upper_limit"] = round(upper_limit, 2)
        lower_limit = mean - stdev * num_of_stdevs
        stats["lower_limit"] = round(lower_limit, 2)

        above_threshold = []
        below_threshold = []

        position_index = -1
        for i in data:
            position_index = position_index + 1
            if i > upper_limit:
                above_item = {}
                above_item["list_position"] = position_index
                above_item["value"] = i
                above_threshold.append(above_item)

            if i < lower_limit:
                below_item = {}
                below_item["list_position"] = position_index
                below_item["value"] = i
                below_threshold.append(below_item)

        stats["above_threshold"] = above_threshold
        stats["above_threshold_runs"] = self._get_threshold_runs(
            above_threshold, periods_of_anomaly
        )
        stats[
            "currently_in_above_threshold_run"
        ] = self._is_metric_in_threshold_run_now(
            len(data), stats["above_threshold_runs"]
        )

        stats["below_threshold"] = below_threshold
        stats["below_threshold_runs"] = self._get_threshold_runs(
            below_threshold, periods_of_anomaly
        )
        stats[
            "currently_in_below_threshold_run"
        ] = self._is_metric_in_threshold_run_now(
            len(data), stats["below_threshold_runs"]
        )

        return stats

    def _get_threshold_runs(self, threshold, periods_of_anomaly):
        anomaly_runs = []
        on_run = False
        previous_list_position = 0
        current_run = []
        items_processed = 0
        for threshold_value in threshold:
            items_processed = items_processed + 1
            if len(current_run) == 0:
                current_run.append(threshold_value)

            position = threshold_value["list_position"]
            if position - 1 == previous_list_position or items_processed == 1:
                on_run = True
            else:
                if on_run and len(current_run) >= periods_of_anomaly:
                    anomaly_runs.append(current_run)
                on_run = False
                current_run = []
                current_run.append(threshold_value)
            if on_run and items_processed > 1:
                current_run.append(threshold_value)
            previous_list_position = position
        if len(current_run) >= periods_of_anomaly:
            anomaly_runs.append(current_run)
        return anomaly_runs

    def _is_metric_in_threshold_run_now(self, number_of_items, threshold_runs):
        if len(threshold_runs) == 0:
            return False
        last_threshold_run = threshold_runs[-1][-1]
        list_position = last_threshold_run.get("list_position", "")
        if list_position == "":
            return False
        if list_position + 1 == number_of_items:
            return True
        return False
