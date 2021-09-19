import logging
import traceback
from datetime import datetime
import json
from decouple import AutoConfig
import requests
import os
import time
from confluent_kafka import Producer
import logging.handlers as handlers

dir_path = os.path.abspath(os.curdir)
extra_tags = {}
config = AutoConfig(search_path=dir_path)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def set_tags(key, value):
    extra_tags[key] = value


def get_tags(key):
    if key in extra_tags:
        return extra_tags[key]
    return None


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def acknowledge_err(err, msg):
    if err is not None:
        # print("Failed to deliver message: {0}: {1}"
        #       .format(msg.value(), err.str()))
        suffix = "failover"
        data = msg.value()
        file_logger(data.decode('utf-8'), suffix)


def _log(msg, application, level, execution_time, user_id, extra_data):

    environment = 'development' if config("ENVIRONMENT") is None or config("ENVIRONMENT") == "" else config("ENVIRONMENT")
    application = 'unknown' if config("APPLICATION") is None or config("APPLICATION") == "" else config("APPLICATION")
    team = config("TEAM")
    app_group = config("APPLICATION_GROUP")

    conf_kafka = {'bootstrap.servers': config("KAFKA_BROKERS"), 'acks': 'all', 'compression.codec': 'gzip', 'message.timeout.ms': 10}
    obj_producer = Producer(**conf_kafka)

    original_data = {
        "message": msg,
        "level": level,
        "application": application,
        "team": team,
        "app_group": app_group,
        "environment": environment,
        "user_id": user_id,
        "execution_time": execution_time,
        "extra_data": extra_data,
        "timestamp": int(time.time())
    }
    data = merge_two_dicts(original_data, extra_tags)

    if str(config("GENERATE_LOG_FILE")).lower() == "yes":
        if not os.path.exists(config('DIR')):
            os.makedirs(config('DIR'))
        file_logger(data)

    if str(config("AGENT")).lower() == "kafka":
        try:
            obj_producer.poll(0)
            obj_producer.produce(config("TOPIC"), json.dumps(data), callback=acknowledge_err)

        except Exception as e:
            print(e)
            file_logger(data)

    obj_producer.flush()
    return data


def _notify(msg):
    url = config("NOTIFY_URL")
    requests.post(url, data={"message": json.dumps(msg), "channel": msg['application']})


def file_logger(data, file_suffix=None):
    try:
        now = datetime.now().strftime("%y%m%d")

        file_name = config('DIR') + file_suffix + "_" + now + '.log' if file_suffix is not None else config('DIR') + now + '.log'

        handler = logging.handlers.TimedRotatingFileHandler(filename=file_name,
                                                            when='midnight', backupCount=5)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if isinstance(data, dict):
            logger.warning(json.dumps(data)+"\n")
        else:
            logger.warning(data+"\n")

        logger.removeHandler(handler)

    except Exception as e:
        print(f'error {e}, traceback {traceback.format_exc()}')


def warning(msg, application=None,  execution_time=None, user_id=None, extra_data=None):
    _log(msg, application, config('WARNING'), execution_time, user_id, extra_data)


def info(msg, application=None,  execution_time=None, user_id=None, extra_data=None):
    _log(msg, application, config('INFO'), execution_time, user_id, extra_data)


def error(msg, application=None,  execution_time=None, user_id=None, extra_data=None):
    _log(msg, application, config('ERROR'), execution_time, user_id, extra_data)


def critical(msg, application=None,  execution_time=None, user_id=None, extra_data=None):
    _notify(_log(msg, application, config('CRITICAL'), execution_time, user_id, extra_data))


def metrics(msg, application=None,  execution_time=None, user_id=None, extra_data=None):
    _log(msg, application, config('METRIC'), execution_time, user_id, extra_data)
