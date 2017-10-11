from datetime import (
    datetime,
    timedelta,
)
from ..models import (
    DBSession,
    OiceQuery,
    UserQuery,
    UserSubscriptionPayout,
    UserSubscriptionPayoutQuery,
)
from modmod.exc import ValidationError
import json
import logging


log = logging.getLogger(__name__)


def start_trial(user):
    if (user.role == 'user' or not user.role) and not user.expire_date:
        user.role = 'paid'
        user.is_trial = True
        user.expire_date = datetime.utcnow() + timedelta(days=30)
        return True
    return False


def handle_membership_update(user, original_transaction_id, expire_timestamp, \
                                        developer_payload, platform, payout_amount):
    if developer_payload.split(':')[0] == 'subs':
        developer_payload = developer_payload.split(':')[2:]
        developer_payload = ':'.join(developer_payload)
    payload_dict = json.loads(developer_payload)
    oice_id = None

    if payload_dict['email'] != user.email:
        raise ValidationError('ERR_IAP_VALIDATOR_USER_NOT_MATCH')

    if 'oiceId' in payload_dict and user.is_new_subscribe \
        and (UserSubscriptionPayoutQuery(DBSession).fetch_by_transaction_id(original_transaction_id) is None):
        oice_id = payload_dict['oiceId']
        target_user = OiceQuery(DBSession).get_by_id(oice_id).story.users[0]
        user_subscription_payout = UserSubscriptionPayout(subscription_user_id = user.id, oice_id=oice_id, \
                                        author_id=target_user.id, platform=platform, \
                                        original_transaction_id=original_transaction_id, \
                                        payout_amount=payout_amount)
        DBSession.add(user_subscription_payout)
        # handle share $ to oice author

    new_expire_date = datetime.utcfromtimestamp(expire_timestamp/1000)
    if user.expire_date is None or new_expire_date > user.expire_date:
        if 'android' == platform:
            user_record = UserQuery(DBSession).fetch_user_by_android_transaction_id(original_transaction_id)
            if user_record is not None and user_record != user:
                raise ValidationError('ERR_IAP_RECEIPT_ALREADY_USED')
            else:
                user.android_original_transaction_id = original_transaction_id
        elif 'ios' == platform:
            user_record = UserQuery(DBSession).fetch_user_by_ios_transaction_id(original_transaction_id)
            if user_record is not None and user_record != user:
                raise ValidationError('ERR_IAP_RECEIPT_ALREADY_USED')
            else:
                user.ios_original_transaction_id = original_transaction_id
        else:
            raise ValidationError("ERR_IAP_PLATFORM_UNKNOWN")
        user.role = 'paid'
        user.is_trial = False
        user.is_cancelled = False
        user.platform = platform
        user.expire_date = new_expire_date
    return 'ok'

