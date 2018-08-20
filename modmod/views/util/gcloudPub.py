from google.cloud import pubsub

import json
import datetime
import logging
log = logging.getLogger(__name__)

GCLOUD_PUB_CONFIG = {'enable': False}

def init_gcloud_pub(projectId, isProduction):
    global GCLOUD_PUB_CONFIG
    GCLOUD_PUB_CONFIG['publisher'] = pubsub.PublisherClient()
    GCLOUD_PUB_CONFIG['projectId'] = projectId
    GCLOUD_PUB_CONFIG['enable'] = True
    GCLOUD_PUB_CONFIG['server'] = 'production' if isProduction else 'test'

def log_message(topic, dict_msg):
    global GCLOUD_PUB_CONFIG

    if GCLOUD_PUB_CONFIG['enable']:
        publisher = GCLOUD_PUB_CONFIG['publisher']
        server = GCLOUD_PUB_CONFIG['server']
        projectId = GCLOUD_PUB_CONFIG['projectId']
        topic_path = publisher.topic_path(projectId, topic)

        try:
            dict_msg['timestamp'] = datetime.datetime.now().isoformat()
            dict_msg['server'] = server
            out_message = json.dumps(dict_msg)

            publisher.publish(topic_path, out_message.encode())
        except Exception as e:
            log.error('gcloud pub error: ' + str(e))
