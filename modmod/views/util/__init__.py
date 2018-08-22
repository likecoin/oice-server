from .mailchimp import (
    init_mailchimp,
    subscribe_mailchimp,
    update_mailchimp_field,
    update_user_mailchimp_stage,
)

from .elastic_search import (
    do_elastic_search_user,
    init_elastic_search,
    update_elastic_search_user,
)

from .localization import (
    normalize_language,
    normalize_ui_language,
    normalize_story_language,
    get_language_code_for_translate,
)

from .slack import (
    init_slack,
    send_message_into_slack,
    send_oice_publish_message_into_slack,
)

from .confluent_kafka_log import (
    init_producer,
    log_message as kafka_log_message,
)

from .gcloudPub import (
    init_gcloud_pub,
    log_message as gcloud_pub_log_message,
)

def includeme(config):
    isProduction = config.get_settings().get('isProduction', '') == 'true'

    init_mailchimp(config.get_settings())

    if config.get_settings().get('es.enable', None) == 'true':
        host = config.get_settings().get('es.host', '')
        port = config.get_settings().get('es.port', '')
        max_suggest = config.get_settings().get('es.max_suggest', '0')
        user = config.get_settings().get('es.user', '')
        password = config.get_settings().get('es.pass', '')
        init_elastic_search(host, port, max_suggest, user, password, isProduction)

    init_slack(config.get_settings())

    if config.get_settings().get('kafka.enable', None) == 'true':
        kafka_host = \
            config.get_settings().get('kafka.host', '')
        kafka_port = \
            config.get_settings().get('kafka.port', '')
        init_producer(','.join([kafka_host + ':' + p for p in kafka_port.split(',')]), isProduction)

    if config.get_settings().get('gcloud.pub.enable', None) == 'true':
        projectId = config.get_settings().get('gcloud.pub.projectId', '')
        init_gcloud_pub(projectId, isProduction)

def log_message(topic, dict_msg):
    gcloud_pub_log_message(topic, dict_msg)
    kafka_log_message(topic, dict_msg)
