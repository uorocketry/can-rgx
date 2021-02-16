import logging


class SensorFilter(logging.Filter):
    """
    Filters out records starting with the level "sensorlog"
    """

    def filter(self, record):
        return not record.name.startswith("sensorlog")
