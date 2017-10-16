import os

ks_view_url = None

def includeme(config):
    global ks_view_url
    global oice_url
    global oice_communication_url
    global o2_output_dir
    global default_lang
    global upload_base_url
    global gcloud_bucket_id
    global gcloud_project_id
    global gcloud_json_path
    global itunesconnect_account
    global itunesconnect_pass
    global itunesconnect_provider_id
    global itunesconnect_app_id
    global testflight_testers_group_id
    ks_view_url = \
        config.get_settings().get('o2.view_url', None)
    oice_url = \
        config.get_settings().get('o2.oice_url', None)
    oice_communication_url = \
        config.get_settings().get('o2.oice_communication_url', None)
    o2_output_dir = \
        config.get_settings().get('o2.output_dir', None)
    default_lang = \
        config.get_settings().get('locale.default_lang', 'en')
    upload_base_url = \
        config.get_settings().get('oice.upload_base_url', None)
    gcloud_bucket_id = \
        config.get_settings().get('gcloud.bucket_id', None)
    gcloud_project_id = \
        config.get_settings().get('gcloud.project_id', None)
    gcloud_json_path = \
        config.get_settings().get('gcloud.json_path', None)
    if gcloud_json_path is not None:
        gcloud_json_path = os.path.abspath(gcloud_json_path)
    itunesconnect_account = \
        config.get_settings().get('itunesconnect.account', '')
    itunesconnect_pass = \
        config.get_settings().get('itunesconnect.pass', '')
    itunesconnect_provider_id = \
        config.get_settings().get('itunesconnect.provider_id', '')
    itunesconnect_app_id = \
        config.get_settings().get('itunesconnect.app_id', '')
    testflight_testers_group_id = \
        config.get_settings().get('testflight.testers_group_id', '')

def get_oice_view_url(oice_uuid):
    global ks_view_url
    if ks_view_url is not None:
        return ks_view_url % {
            'ks_uuid': oice_uuid
        }
    else:
        return None

def get_oice_url(oice_uuid):
    global oice_url
    if oice_url is not None:
        return oice_url % {
            'ks_uuid': oice_uuid
        }
    else:
        return None

def get_oice_preview_url(oice_uuid):
    oice_view_url = get_oice_view_url(oice_uuid)
    if oice_view_url is not None:
        oice_view_url += '/preview'
    return oice_view_url

def get_oice_communication_url():
    global oice_communication_url
    return oice_communication_url

def get_o2_output_dir(oice_uuid):
    global o2_output_dir
    if o2_output_dir is not None:
        return o2_output_dir % {
            'ks_uuid': oice_uuid
        }
    else:
        return None


def get_default_lang():
    global default_lang
    return default_lang


def get_upload_base_url():
    global upload_base_url
    return upload_base_url

def get_gcloud_bucket_id():
    global gcloud_bucket_id
    return gcloud_bucket_id

def get_gcloud_project_id():
    global gcloud_project_id
    return gcloud_project_id

def get_gcloud_json_path():
    global gcloud_json_path
    return gcloud_json_path

def get_itunesconnect_account():
    global itunesconnect_account
    return itunesconnect_account

def get_itunesconnect_pass():
    global itunesconnect_pass
    return itunesconnect_pass

def get_itunesconnect_provider_id():
    global itunesconnect_provider_id
    return itunesconnect_provider_id

def get_itunesconnect_app_id():
    global itunesconnect_app_id
    return itunesconnect_app_id

def get_testflight_testers_group_id():
    global testflight_testers_group_id
    return testflight_testers_group_id
