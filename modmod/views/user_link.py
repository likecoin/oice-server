from cornice import Service
from pyramid.httpexceptions import HTTPForbidden


from ..models import (
    DBSession,
    UserFactory,
    UserQuery,
    UserLink,
    UserLinkFactory,
    UserLinkTypeQuery,
)


user_links_types = Service(name='user_links_types',
                           path='user/links/types',
                           renderer='json')

user_id_links = Service(name='user_id_links',
                        path='user/{user_id}/links',
                        renderer='json',
                        factory=UserFactory,
                        traverse='/{user_id}')

user_links = Service(name='user_links',
                     path='user/links',
                     renderer='json')

user_link_id = Service(name='user_link_id',
                       path='user/link/{user_link_id}',
                       renderer='json',
                       factory=UserLinkFactory,
                       traverse='/{user_link_id}')


@user_links_types.get()
def list_link_types(request):
    link_types = UserLinkTypeQuery(DBSession).fetch_all()

    return {
        "code": 200,
        "message": "ok",
        "linkTypes": [link_type.serialize() for link_type in link_types],
    }


@user_id_links.get()
def list_user_links(request):
    user = request.context

    return {
        "code": 200,
        "message": "ok",
        "links": [link.serialize() for link in user.links],
    }


@user_links.post()
def create_user_link(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden()

    # Rely on client to specify the UserLinkType
    link_type_alias = request.json_body.get('typeAlias')
    link_type = UserLinkTypeQuery(DBSession).fetch_by_alias(alias=link_type_alias)

    label = request.json_body['label']
    link = request.json_body['link']

    link = UserLink(user_id=user.id,
                    user_link_type_id=link_type.id if link_type else None,
                    label=label,
                    link=link,
                    order=len(user.links),
                    )

    user.links.append(link)

    DBSession.flush()

    return {
        "code": 200,
        "message": "ok",
        "link": link.serialize(),
    }


@user_link_id.post(permission='set')
def update_user_link(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    user_link = request.context

    # Rely on client to specify the UserLinkType
    if 'typeAlias' in request.json_body:
        user_link.type = UserLinkTypeQuery(DBSession).fetch_by_alias(alias=request.json_body['typeAlias'])

    if 'label' in request.json_body:
        user_link.label = request.json_body['label']

    if 'link' in request.json_body:
        user_link.link = request.json_body['link']

    # For reordering links
    if 'order' in request.json_body:
        new_link_order = request.json_body['order']
        old_link_order = user_link.order

        if old_link_order > new_link_order:
            DBSession.query(UserLink) \
                     .filter(
                         UserLink.user_id == user.id,
                         UserLink.order >= new_link_order,
                         UserLink.order < old_link_order
                     ) \
                     .update({ UserLink.order: UserLink.order + 1 })

            user_link.order = new_link_order

        elif old_link_order < new_link_order:
            DBSession.query(UserLink) \
                     .filter(
                         UserLink.user_id == user.id,
                         UserLink.order > old_link_order,
                         UserLink.order <= new_link_order
                     ) \
                     .update({ UserLink.order: UserLink.order - 1 })

            user_link.order = new_link_order

    return {
        "code": 200,
        "message": "ok",
        "link": user_link.serialize(),
    }


@user_link_id.delete(permission='set')
def delete_user_link(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    user_link = request.context

    DBSession.delete(user_link)

    DBSession.query(UserLink) \
        .filter(
            UserLink.user_id == user.id,
            UserLink.order > user_link.order
        ) \
        .update({ UserLink.order: UserLink.order - 1 })

    return {
        "code": 200,
        "message": "ok",
    }
