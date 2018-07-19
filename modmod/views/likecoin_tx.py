from cornice import Service
import json
import math
import requests

from modmod.exc import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from ..models import (
    DBSession,
    LibraryQuery,
    LikecoinTx,
    LikecoinTxFactory,
    LikecoinTxQuery,
    UserQuery,
)
from . import (
    get_likecoin_firebase_api_url,
    get_likecoin_tx_subscription_key,
    get_likecoin_max_reward_ratio,
    get_oice_likecoin_wallet,
)

import logging
log = logging.getLogger(__name__)

likecoin_tx_product_type = Service(name='likecoin_tx_product_type',
                                   path='likecoin/tx/product/{product_type}',
                                   renderer='json')

likecoin_tx_id_validate = Service(name='likecoin_tx_id_validate',
                                    path='likecoin/tx/{id}/validate',
                                    renderer='json',
                                    factory=LikecoinTxFactory,
                                    traverse='/{id}',)

likecoin_tx_subscription = Service(name='likecoin_tx_subscription',
                                    path='likecoin/tx/subscription',
                                    renderer='json')


@likecoin_tx_product_type.post(permission='set')
def add_product_tx(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    try:
        product_type = request.matchdict['product_type']
        product_id = request.json_body['productId']
        amount = request.json_body['amount']
    except KeyError:
        raise ValidationError('ERR_LIKECOIN_TX_PRODUCT_INFO_MISSING')

    tx = DBSession.query(LikecoinTx) \
                  .filter(LikecoinTx.user_id == user.id) \
                  .filter(LikecoinTx.product_type == product_type) \
                  .filter(LikecoinTx.product_id == product_id) \
                  .one_or_none()

    if tx is None:
        tx = LikecoinTx(user_id=user.id,
                        product_type=product_type,
                        product_id=product_id,
                        amount=amount,
                        max_reward=amount*get_likecoin_max_reward_ratio())
        DBSession.add(tx)
        DBSession.flush()
    elif tx.status == 'failed':
        raise ValidationError('ERR_LIKECOIN_TX_PRODUCT_STATUS_FAILED')
    elif tx.tx_hash is not None:
        raise ValidationError('ERR_LIKECOIN_TX_PRODUCT_PURCHASED')

    return {
        'id': tx.id,
        'userId': user.id,
        'productType': product_type,
        'productId': product_id,
        'from': tx.from_,
        'to': tx.to,
        'amount': amount,
        'txHash': tx.tx_hash,
        'status': tx.status,
        'createdAt': tx.created_at.isoformat(),
        'updatedAt': tx.updated_at.isoformat(),
    }


def get_likecoin_tx_detail(tx_hash):
    url = get_likecoin_firebase_api_url() + '/tx/hash/' + tx_hash
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        return r.json()
        # { completeTs, from, status, to, ts, txHash, type, value }
    return None


def is_tx_amount_valid(tx_amount, likecoin_value):
    amount = float(likecoin_value) / math.pow(10, 18)
    return math.isclose(tx_amount, amount)

@likecoin_tx_id_validate.put(permission='get')
def validate_likecoin_tx(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    try:
        tx_hash = request.json_body['txhash']
    except KeyError:
        raise ValidationError('ERR_LIKECOIN_TX_PRODUCT_INFO_MISSING')

    tx = request.context

    if tx.tx_hash != tx_hash:
        raise ValidationError('ERR_LIKECOIN_TX_VALIDATE_TX_HASH_NOT_MATCH')

    likecoin_tx = get_likecoin_tx_detail(tx.tx_hash)
    if likecoin_tx is None:
        raise ValidationError('ERR_LIKECOIN_TX_HASH_NOT_EXIST')
    if tx.status == 'success':
        raise ValidationError('ERR_LIKECOIN_TX_VALIDATE_EXISTED')
    if is_tx_amount_valid(tx.amount, likecoin_tx['value']) is not True:
        raise ValidationError('ERR_LIKECOIN_TX_VALIDATE_AMOUNT_NOT_MATCH')
    if tx.from_ != likecoin_tx['from']:
        raise ValidationError('ERR_LIKECOIN_TX_VALIDATE_FROM_ADDRESS_NOT_MATCH')
    if not (tx.to == likecoin_tx['to'] == get_oice_likecoin_wallet()):
        raise ValidationError('ERR_LIKECOIN_TX_VALIDATE_TO_ADDRESS_NOT_MATCH')

    product = None

    if tx.product_type == 'library':
        library = LibraryQuery(DBSession).get_library_by_id(tx.product_id)
        return {
            'product': library.serialize_min(),
        }

    return {}


def is_subscribe_payload_valid(tx, likecoin_tx):
    oice_wallet = get_oice_likecoin_wallet()
    return (tx.to is not None and tx.to == oice_wallet) and \
           likecoin_tx['to'] == oice_wallet and \
           is_tx_amount_valid(tx.amount, likecoin_tx['value'])


@likecoin_tx_subscription.post()
def subscribe_likecoin_tx(request):
    ok = {
        'code': 200,
        'message': 'ok'
    }

    if request.params.get('key') != get_likecoin_tx_subscription_key():
        # invalid subscription key
        return ok

    likecoin_tx = get_likecoin_tx_detail(request.json_body['txHash'])
    if likecoin_tx is None:
        # tx record not found in likeco
        return ok

    tx = None
    if 'userPayload' in request.json_body:
        # will receive userPayload for first message for each tx
        user_payload = json.loads(request.json_body['userPayload'])
        tx = LikecoinTxQuery(DBSession).get_by_id(user_payload['txId'])
    else:
        tx = LikecoinTxQuery(DBSession).get_by_tx_hash(request.json_body['txHash'])

    if tx is None:
        # tx record not found in db
        return ok
    elif not is_subscribe_payload_valid(tx, likecoin_tx):
        # invalid subscribe payload
        return ok

    if tx.tx_hash is not None:
        tx.tx_hash = request.json_body['txHash']
        tx.from_ = request.json_body['from']
        tx.to = request.json_body['to']

        user = UserQuery(DBSession).get_user_by_id(tx.user_id)
        if tx.product_type == 'library':
            # add library to user purchased and selected library list
            library = LibraryQuery(DBSession).get_library_by_id(tx.product_id)

            if library not in user.libraries_purchased:
                user.libraries_purchased.append(library)
            if library not in user.libraries_selected:
                user.libraries_selected.append(library)

    if 'status' in request.json_body:
        status = request.json_body['status']
        tx.status = status

        # TODO notify user when status changes
        if status == 'failed':
            # remove library from user
            user = UserQuery(DBSession).get_user_by_id(tx.user_id)

            if tx.product_type == 'library':
                library = LibraryQuery(DBSession).get_library_by_id(tx.product_id)

                if library in user.libraries_selected:
                    user.libraries_selected.remove(library)
                if library.has_user_purchased:
                    user.libraries_purchased.remove(library)

    return ok
