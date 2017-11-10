import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import PasswordType
from sqlalchemy.sql.expression import true, false
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import text
from pyramid_safile import FileHandleStore
import logging

from modmod.models.base import (
    Base,
    BaseMixin,
)

from .user_story import user_story
from .user_selected_library import user_selected_library
from .user_link import UserLink
from .user_like_story import user_like_story

from ..config import get_upload_base_url
from . import DBSession
log = logging.getLogger(__name__)


class User(Base, BaseMixin):
    __tablename__ = 'user'

    email = sa.Column(sa.Unicode(1024), nullable=False, unique=True)
    display_name = sa.Column(sa.Unicode(256), nullable=False)
    username = sa.Column(sa.Unicode(256), nullable=True, unique=True)
    role = sa.Column(sa.Unicode(1024), nullable=False, server_default='user')
    platform = sa.Column(sa.Unicode(16), nullable=True)
    last_login_at = sa.Column(sa.DateTime, nullable=True)
    description = sa.Column(sa.Unicode(1024), nullable=False, server_default='')
    seeking_subscription_message = sa.Column(sa.Unicode(1024), nullable=False, server_default='')
    language = sa.Column(sa.Unicode(7), nullable=True)
    ui_language = sa.Column(sa.Unicode(7), nullable=False, server_default='en')
    avatar_storage = sa.Column(FileHandleStore, nullable=True)
    is_trial = sa.Column(sa.Boolean, nullable=False, server_default=false())
    mailchimp_stage = sa.Column(sa.Integer, nullable=False, server_default="1")
    customer_id = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    stripe_access_token = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    stripe_refresh_token = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    stripe_account_id = sa.Column(sa.Unicode(128), nullable=True, unique=False)
    android_original_transaction_id = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    ios_original_transaction_id = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    expire_date = sa.Column(sa.DateTime, nullable=True)
    is_cancelled = sa.Column(sa.Boolean, nullable=False, server_default=true())
    is_anonymous = sa.Column(sa.Boolean, nullable=False, server_default=false())
    tutorial_state = sa.Column(mysql.BIT(32), nullable=False, server_default=text("b'0'"))
    stories = relationship(
        "Story",
        secondary=user_story,
        secondaryjoin='and_( \
                        user_story.c.story_id==Story.id, \
                        Story.is_deleted==false() \
                        )',
        lazy='select',
        cascade='',
        backref=backref("users", lazy="joined", viewonly=True)
    )
    liked_stories = relationship(
        "Story",
        secondary=user_like_story,
        lazy='select',
        cascade='',
        backref=backref('liked_users', lazy="select")
    )
    libraries_selected = relationship(
        "Library",
        secondary=user_selected_library,
        secondaryjoin='''and_(
            user_selected_library.c.library_id==Library.id,
            Library.is_deleted==false()
        )''',
        lazy='select',
        cascade='',
        backref=backref("selected_users", lazy="select")
    )
    links = relationship(
        UserLink,
        order_by=UserLink.order,
        cascade='all, delete',
        backref=backref("user", lazy="joined")
    )
    subscription_payouts = relationship(
        "UserSubscriptionPayout",
        primaryjoin="User.id == UserSubscriptionPayout.author_id",
        lazy='select',
        viewonly=True
    )

    def __init__(self, email, is_anonymous=False):
        self.email = email
        self.is_anonymous = is_anonymous
        self.mailchimp_stage = 1
        self.tutorial_state = 0

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "displayName" : self.display_name,
            "username": self.username,
            "role": self.role,
            "description" : self.description,
            'seekingSubscriptionMessage': self.seeking_subscription_message,
            "language" : self.language,
            "uiLanguage": self.ui_language,
            'avatar': self.avatar_url(),
            "isTrial": self.is_trial,
            'expireDate': self.expire_date.isoformat() if self.expire_date else None,
            'isCancelled' : self.is_cancelled,
            'tutorialState': self.serialize_tutorial_state(),
            'isStripeConnected' : bool(self.stripe_account_id),
            'hasPaymentInfo' : bool(self.customer_id),
            'isAnonymous': self.is_anonymous,
        }

    def serialize_min(self):
        return {
            'id': self.id,
            "email": self.email,
            "displayName" : self.display_name,
            'avatar': self.avatar_url(),
        }

    def serialize_credit(self):
        return {
            'id': self.id,
            'displayName' : self.display_name,
            'description': self.description,
            'seekingSubscriptionMessage': self.seeking_subscription_message,
            'avatar': self.avatar_url(),
        }

    def avatar_url(self):
        return get_upload_base_url() + self.avatar_storage.url if self.avatar_storage else ''

    def serialize_tutorial_state(self):
        string_bits = str(bin(self.tutorial_state))[2:].zfill(32)
        bool_list = []
        for char in string_bits:
            bool_list.append(char == '1')
        return bool_list

    def import_handle(self, handle):
        self.avatar_storage = handle

    def is_free(self):
        return self.role == "user"

    def is_paid(self):
        return self.role == "paid"

    def is_admin(self):
        return self.role == "admin"

    @property
    def is_new_subscribe(self):
        return  (not self.customer_id) and \
                (not self.android_original_transaction_id) and \
                (not self.ios_original_transaction_id)

class UserFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            key = int(key)
            return UserQuery(DBSession) \
                .get_user_by_id(key)
        except:
            return UserQuery(DBSession) \
                .fetch_user_by_username(key) \
                .one()

class UserQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(User)

    def fetch_user_by_email(self, email):
        return self.query \
                   .filter(User.email == email)

    def fetch_user_by_emails(self, emails):
        return self.query \
                   .filter(User.email.in_(emails)) \
                   .all()

    def get_user_by_id(self, id):
        return self.query \
                   .filter(User.id == id) \
                   .one()

    def fetch_user_by_customer_id(self, customer_id):
        return self.query \
                   .filter(User.customer_id == customer_id)\
                   .one()

    def fetch_user_by_stripe_account_id(self, stripe_account_id):
        return self.query \
                   .filter(User.stripe_account_id == stripe_account_id)\
                   .one()

    def fetch_user_by_ids(self, user_ids):
        return self.query \
                   .filter(User.id.in_(user_ids)) \
                   .all()

    def fetch_user_by_android_transaction_id(self, android_original_transaction_id):
        return self.query \
                   .filter(User.android_original_transaction_id == android_original_transaction_id)\
                   .one_or_none()

    def fetch_user_by_ios_transaction_id(self, ios_original_transaction_id):
        return self.query \
                   .filter(User.ios_original_transaction_id == ios_original_transaction_id)\
                   .one_or_none()

    def fetch_user_by_username(self, username):
        return self.query \
                   .filter(User.username == username)

    # def fetch_user_by_id(self, user_id):
    #     return self.query \
    #                .filter(User.id == user_id)
