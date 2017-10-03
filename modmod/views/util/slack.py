import json
import requests

SLACK_ENABLE = False
SLACK_WEBHOOK_URL = None
SLACK_ICON_EMOJI = ':oicelogo:'
SLACK_MESSAGE_PAYLOAD = {}

def init_slack(setting):
    global SLACK_ENABLE
    global SLACK_WEBHOOK_URL
    global SLACK_MESSAGE_PAYLOAD
    if not SLACK_ENABLE and setting.get('slack.enable', None) == 'true':
        webhook_url = setting.get('slack.webhook_url', None)
        if webhook_url:
            username = setting.get('slack.username', 'oice')
            icon_url = setting.get('slack.icon_url', None)
            SLACK_ENABLE = True
            SLACK_WEBHOOK_URL = webhook_url
            SLACK_MESSAGE_PAYLOAD['username'] = username
            if icon_url:
                SLACK_MESSAGE_PAYLOAD['icon_url'] = icon_url
            else:
                SLACK_MESSAGE_PAYLOAD['icon_emoji'] = SLACK_ICON_EMOJI
    return SLACK_ENABLE

def send_message_into_slack(payload = {}):
    payload.update(SLACK_MESSAGE_PAYLOAD)
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

def send_oice_publish_message_into_slack(author, oice, link='', image_url=''):
    if not author and not oice: return
    author_name = "%s (%s)" % (author.display_name, author.email)
    title = "%s - %s" % (oice.filename, oice.story.name)
    payload = {
        "attachments": [
            {
                "fallback": "%s just published %s :tada:" % (author_name, title),
                "color": "#16A222",
                "pretext": "A new oice is published! :tada:",
                "author_name": author_name,
                "author_link": "mailto:" + author.email,
                "title": title,
                "title_link": link,
                "fields": [],
                "image_url": image_url
            }
        ]
    }
    send_message_into_slack(payload)
