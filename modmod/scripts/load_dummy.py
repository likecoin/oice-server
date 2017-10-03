import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from ..models import (
    DBSession,
    Project,
    Ks,
    Macro,
    Block,
    )


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    with transaction.manager:
        '''Load dummy project and ks files'''
        project = Project(
            name='Dummy Project',
            base_zip=None
        )
        DBSession.add(project)
        DBSession.flush()
        ks_model1 = Ks(
            project_id=project.id,
            filename='first.ks'
        )
        DBSession.add(ks_model1)

        ks_model2 = Ks(
            project=project,
            filename='second.ks'
        )
        DBSession.add(ks_model2)
        DBSession.flush()

        '''Load 20 dummy blocks of KS file with id: 1'''
        macro = DBSession.query(Macro) \
                         .filter(Macro.tagname == 'text') \
                         .first()
        for i in range(0, 19):
            block_model = Block(
                ks=ks_model1,
                macro=macro,
                position=i
            )
            DBSession.add(block_model)
        DBSession.flush()
