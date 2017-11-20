# pylama:ignore=E501

fg_show = {
    "left": '''@fgLeft key="%(key)s" storage="%(fg)s" left="&ch['%(key)s'].xl" top="&ch['%(key)s'].yl" move="%(move)s" dim="%(dim)s"''',
    "right": '''@fgRight key="%(key)s" storage="%(fg)s" left="&ch['%(key)s'].xr" top="&ch['%(key)s'].yr" move="%(move)s" dim="%(dim)s"''',
    "middle": '''@fgMiddle key="%(key)s" storage="%(fg)s" left="&ch['%(key)s'].xm" top="&ch['%(key)s'].ym"'''
}

fg_to_bright = {
    "right": '''@fgRightToBright key="%(key)s" left="&ch['%(key)s'].xDr" top="&ch['%(key)s'].yDr" storage="%(fg)s" path="&ch['%(key)s'].pathr" move="%(move)s" dim="%(dim)s"''',
    "left": '''@fgLeftToBright key="%(key)s" storage="%(fg)s" left="&ch['%(key)s'].xDl" top="&ch['%(key)s'].yDl" path="&ch['%(key)s'].pathl" move="%(move)s" dim="%(dim)s"'''
}

fg_to_dark = {
    "right": """@fgRightToDark key="%(key)s" left="&ch['%(key)s'].xr" top="&ch['%(key)s'].yr" storage="%(fg)s" path="&ch['%(key)s'].pathDr\"""",
    "left": """@fgLeftToDark key="%(key)s" left="&ch['%(key)s'].xl" top="&ch['%(key)s'].yl" storage="%(fg)s" path="&ch['%(key)s'].pathDl\""""
}

fg_exit = {
    "right": "@fgExitRight",
    "left": "@fgExitLeft",
    "middle": "@fgExitMiddle"
}
