from confluent_kafka import Producer
from confluent_kafka import KafkaException

import json
import datetime
import logging
log = logging.getLogger(__name__)

global CONFLUENT_KAFKA_OBJ
CONFLUENT_KAFKA_OBJ = {'enable': False}

def init_producer(broker_list, isProduction):
    global CONFLUENT_KAFKA_OBJ
    CONFLUENT_KAFKA_OBJ['producer'] = Producer({
                                        'bootstrap.servers': broker_list,
                                        'api.version.request': True,
                                      })
    CONFLUENT_KAFKA_OBJ['enable'] = True
    CONFLUENT_KAFKA_OBJ['server'] = 'production' if isProduction else 'test'


def log_message(topic, dict_msg):
    global CONFLUENT_KAFKA_OBJ

    if CONFLUENT_KAFKA_OBJ['enable']:
        producer = CONFLUENT_KAFKA_OBJ['producer']
        server = CONFLUENT_KAFKA_OBJ['server']

        # Add general fields and set output message
        dict_msg['timestamp'] = datetime.datetime.now().isoformat()
        dict_msg['server'] = server
        out_message = json.dumps(dict_msg)
    
        try:
            producer.produce(topic, out_message.encode('utf-8'))
    
            producer.flush()
        except KafkaException as e: 
            log.error('Confluent kafka error: ' + str(e))

