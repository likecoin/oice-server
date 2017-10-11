# pylama:ignore=E501

fg_show = {
    "left": """@fgLeft storage="%(fg)s" left="&ch['%(key)s'].xl" top="&ch['%(key)s'].yl\"""",
    "right": """@fgRight storage="%(fg)s" left="&ch['%(key)s'].xr" top="&ch['%(key)s'].yr\"""",
    "middle": """@fgMiddle storage="%(fg)s" left="&ch['%(key)s'].xm" top="&ch['%(key)s'].ym\""""
}

fg_to_bright = {
    "right": """@fgRightToBright left="&ch['%(key)s'].xDr" top="&ch['%(key)s'].yDr" storage="%(fg)s" path="&ch['%(key)s'].pathr\"""",
    "left": """@fgLeftToBright storage="%(fg)s" left="&ch['%(key)s'].xDl" top="&ch['%(key)s'].yDl" path="&ch['%(key)s'].pathl\""""
}

fg_to_dark = {
    "right": """@fgRightToDark left="&ch['%(key)s'].xr" top="&ch['%(key)s'].yr" storage="%(fg)s" path="&ch['%(key)s'].pathDr\"""",
    "left": """@fgLeftToDark left="&ch['%(key)s'].xl" top="&ch['%(key)s'].yl" storage="%(fg)s" path="&ch['%(key)s'].pathDl\""""
}

fg_exit = {
    "right": "@fgExitRight",
    "left": "@fgExitLeft",
    "middle": "@fgExitMiddle"
}
