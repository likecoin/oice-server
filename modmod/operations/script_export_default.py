SCREEN_SIZE = 1080

NOVELSPHERE_CONFIG = {
    'title': 'oice',
    'scWidth': SCREEN_SIZE,
    'scHeight': SCREEN_SIZE,
    'gameID': None,
    'chSpeeds': 30,
    'numImageLayers': 5,
    'numMessageLayers': 4,
    'numSEBuffers': 3,
    'numMovies': 1,
    'scPositionX_left': 50,
    'scPositionX_left_center': 145,
    'scPositionX_center': 240,
    'scPositionX_right_center': 335,
    'scPositionX_right': 430,
    'initialMessageLayerVisible': False,
    'messageLayerColor': '0x000000',
    'messageLayerOpacity': int(255 * 0.7),
    'messageLayerMarginT': 44,
    'messageLayerMarginL': 60,
    'messageLayerMarginR': 60,
    'messageLayerMarginB': 40,
    'messageLayerCurrentPositionX': 0,
    'messageLayerCurrentPositionY': 0,
    'messageLayerCurrentWidth': SCREEN_SIZE,
    'messageLayerCurrentHeight': SCREEN_SIZE,
    'messageLayerDefaultAutoReturn': True,
    'messageLayerDefaultFontSize': 48,
    'messageLayerDefaultFontFace': 'Noto Sans TC',
    'messageLayerDefaultFontColor': '0xFFFFFF',
    'messageLayerDefaultFontBold': False,
    'messageLayerDefaultFontItalic': False,
    'messageLayerDefaultRubyOffset': 0,
    'messageLayerDefaultRubySize': 10,
    'messageLayerDefaultShadow': False,
    'messageLayerDefaultShadowBlur': 3,
    'messageLayerDefaultShadowOffsetX': 1,
    'messageLayerDefaultShadowOffsetY': 1,
    'messageLayerDefaultShadowColor': '0x000000',
    'messageLayerDefaultEdge': False,
    'messageLayerDefaultEdgeColor': '0x000000',
    'messageLayerDefaultStyleLineSpacing': 22,
    'messageLayerDefaultStylePitch': 0,
    'messageLayerDefaultGlyphLine': 'wait_click',
    'messageLayerDefaultGlyphPage': 'wait_click',
    'messageLayerDefaultGlyphFixed': True,
    'messageLayerDefaultGlyphX': 0,
    'messageLayerDefaultGlyphY': 0,
    'messageLayerDefaultLinkColor': '0x0080ff',
    'messageLayerDefaultLinkOpacity': 64,
    'messageLayerVertical': False,
    'historyLayerFontFace': 'Noto Sans TC',
    'historyLayerFontColor': '0xffffff',
    'historyLayerFontBold': False,
    'historyLayerFontHeight': 20,
    'historyLayerLineHeight': 26,
    'historyLayerEverypage': False,
    'historyLayerMaxLines': 2000,
    'historyLayerMaxPages': 100,
    'historyLayerStoreState': False,
    'historyLayerColor': '0x000000',
    'historyLayerOpacity': 255,
    'historyLayerFrame': '',
    'historyLayerFrameFixed': False,
    'historyLayerMarginT': 30,
    'historyLayerMarginL': 30,
    'historyLayerMarginR': 30,
    'historyLayerMarginB': 30,
    'historyLayerCurrentPositionX': 10,
    'historyLayerCurrentPositionY': 10,
    'historyLayerCurrentWidth': 620,
    'historyLayerCurrentHeight': 460,
    'historyLayerShadow': False,
    'historyLayerShadowBlur': 3,
    'historyLayerShadowOffsetX': 1,
    'historyLayerShadowOffsetY': 1,
    'historyLayerShadowColor': '0x000000',
    'historyLayerEdge': False,
    'historyLayerEdgeColor': '0x000000',
    'historyLayerVertical': 'auto',
    'cursorDefault': 'auto',
    'cursorDraggable': 'auto',
    'cursorWaitingClick': 'auto',
    'cursorPointed': 'pointer',
    'backgroundColor': '0x000000',
    'saveMode': 'o2kag',
    'priorityAudioChannel': 'bgm',
    # 'numImageCache': 2,
    # 'numScriptCache': 1,
    'saveThumbnail': True,
    'thumbnailWidth': 540,
    'autoModePageWait': 30,
    'autoModeLineWait': 30,
    # Custom configs
    'preloadRes': True,
    'preload': True,
    'forcePreloadSoundAndVideoInIOS': True
}

SCALABLE_CONFIG_ITEMS = [
    'scWidth',
    'scHeight',
    'scPositionX_left',
    'scPositionX_left_center',
    'scPositionX_center',
    'scPositionX_right_center',
    'scPositionX_right',
    'messageLayerMarginT',
    'messageLayerMarginL',
    'messageLayerMarginR',
    'messageLayerMarginB',
    'messageLayerCurrentPositionX',
    'messageLayerCurrentPositionY',
    'messageLayerCurrentWidth',
    'messageLayerCurrentHeight',
    'messageLayerDefaultFontSize',
    'messageLayerDefaultRubyOffset',
    'messageLayerDefaultRubySize',
    'messageLayerDefaultShadowBlur',
    'messageLayerDefaultShadowOffsetX',
    'messageLayerDefaultShadowOffsetY',
    'messageLayerDefaultStyleLineSpacing',
    'messageLayerDefaultStylePitch',
    'messageLayerDefaultGlyphX',
    'messageLayerDefaultGlyphY',
    'historyLayerFontHeight',
    'historyLayerLineHeight',
    'historyLayerMarginT',
    'historyLayerMarginL',
    'historyLayerMarginR',
    'historyLayerMarginB',
    'historyLayerCurrentPositionX',
    'historyLayerCurrentPositionY',
    'historyLayerCurrentWidth',
    'historyLayerCurrentHeight',
    'historyLayerShadowBlur',
    'historyLayerShadowOffsetX',
    'historyLayerShadowOffsetY',
    'thumbnailWidth',
]


SCALABLE_ATTRIBUTES = [
    'dx', 'dy',
    'height', 'width',
    'left', 'top',
    'linesize', 'linespacing',
    'marginb', 'marginl', 'marginr', 'margint',
    'shadowx', 'shadowy',
    'size',
    'sw', 'sx', 'sy',
    'x', 'y',
]


FADING_AUDIO_MACROS = set([
    'fadebgm',
    'fadeinbgm',
    'fadeinse',
    'fadeoutse',
    'fadeoutbgm',
    'fadeoutse',
    'fadepausebgm',
    'fadese',
])


OVERRIDABLE_CHARACTER_CONFIG_ITEMS = [
    "edgecolor",
    "xl",  "xm",  "xr",
    "yl",  "ym",  "yr",
    "xDl", "xDr", "xDm",
    "yDl", "yDr", "yDm",
]


CHARACTER_CONFIG = {
    'offset': 50,
    'edgecolor': '0xACACAB',
    'nameframe': 'nameframe'
}

OICE_HTML_META = """
<title>%s</title>
<meta property='og:locale' content='%s' />
<meta property='og:title' content='%s' />
<meta property='og:description' content='%s' />
<meta property='og:url' content='%s' />
<meta property='og:image' content='%s' />
<meta property='oice:thumbnail' content='%s' />
"""


FIRST_KS_HEADER = """;Include other .ks files
@call storage="_definition.ks"
@call storage="_default_macro.ks"
@call storage="_interaction.ks"
@call storage="_macro.ks"
@call storage="_npcdata.ks"

"""


KS_SCRIPT_RETURN = "\n@return"


OICE_DEFAULTS_SCRIPT = """;Global constants
; All global used ks variables should declare here
@eval o2_exp="tf.oiceDefaults = %s"
""" + KS_SCRIPT_RETURN


OICE_INTERACTION_SCRIPT = '''
function startSkip() {
    if (o2.autoMode) {
        o2.clickSkipEnabled = true;
    }
    o2.skipTimeout = setTimeout(function() {
        o2.skipWithMode(o2.SKIP_MODE_FAST_FORWARD);
    }, 500);
}

function endSkip() {
    clearTimeout(o2.skipTimeout);
    if (o2.autoMode) {
        o2.clickSkipEnabled = false;
    }
    o2.skipWithMode(o2.SKIP_MODE_NONE);
}

/**
 * Change the text delay speed
 * @param  {Number} speed - The delay speed, the smaller speed, the shorter delay
 */
function changeTextDelay(speed) {
    new Tag("delay", { "speed": speed }).run();
}

/**
 * Enter skip mode when user press the oice
 */
$("#main-wrapper").on('mousedown mouseup touchstart touchend', function(e) {
    switch (e.type) {
        case "mousedown":
        case "touchstart":
            startSkip();
            break;
        default:
            endSkip();
            break;
    }
});

function oiceActionHandler(event) {
    var action = JSON.parse(event.data);
    if (!(typeof action === 'object' && typeof action.type === 'string')) return;
    switch (action.type) {
        case 'oice.screenCapture':{
            /**
             * Capture oice screen for thumbnail
             * Use by web
             */
            new Tag("save", { "place": 0 }).run();
            var serializedAction = JSON.stringify({
                'type': 'oice.screenCapture',
                'payload': ev.save.snapshot[0]
            });
            window.parent.postMessage(serializedAction, "*");
            break;
        }
        case 'oice.click':
            /**
             * Fast forward until click wait (Draft)
             * Use by app
             */
            if (currentConductor) {
              currentConductor.trigger('click');
            }
            break;
        case 'oice.startSkip':
            /**
             * Start skipping oice
             * Use by web and app
             */
            startSkip();
            break;
        case 'oice.endSkip':
            /**
             * End skipping oice
             * Use by web and app
             */
            endSkip();
            break;
        case 'oice.setTextDelay':
            /**
             * Set time duration between occurrences of scripture text's characters
             * Use by app
             *
             * Payload data:
             * speed: (number) time delay in milliseconds
             */
            if (!(typeof action.payload === 'object')) return;

            if (typeof action.payload.speed === 'number') {
              changeTextDelay(action.payload.speed);
            }
            break;
        case 'oice.clickOptionButton':
            var buttonIndex = action.payload && action.payload.index;
            var button = o2.currentMessageLayer.buttons[buttonIndex];
            if (button) {
                button.click(0, 0, o2.currentMessageLayer, true);
            }
            break;
        case 'oice.toggleBGM':
            /**
             * To play or pause the background music.
             * Use by app
             *
             * Payload data:
             * enabled: (boolean) 
             */
            if (!(typeof action.payload === 'object')) return;

            if (typeof action.payload.enabled === 'boolean' && action.payload.enabled) {
                new Tag('resumebgm').run();
            } else {
                new Tag('pausebgm').run();
            }
            break;
        default:
            break;
    }
}

document.addEventListener('message', oiceActionHandler); // For App
window.addEventListener('message', oiceActionHandler); // For Web

/**
 * Pre-oice action
 */
changeTextDelay(10);
'''

PRE_OICE_SCRIPT = '''
;----------
;淡出播放按鈕
;----------
*startoice
@backlay
@layopt layer=message0 page=back visible=false
@trans method=crossfade time=300 rule=01 from="left" stay="nostay" layer="message0"
@wt

@clickskip enabled=true

@postoiceaction type="oice.start"
@o2_savestat

@history enabled=false

@oice_glyph

'''

POST_OICE_SCRIPT = '''
*endOice
;-------
;畫面變暗
;-------
[o2_iscript]
$("<style type='text/css'>@-webkit-keyframes fadein{0%,25%{opacity:0}100%{opacity:1}}@keyframes fadein{0%, 25%{opacity:0}100%{opacity:1}}</style>").appendTo("head");
$("#main-wrapper").append('<div style="-webkit-animation:1s fadein 0s 1;animation: 1s fadein 0s 1;background-color:rgba(0,0,0,0.8);z-index:9999;position:relative;width:100%;height:100%;"></div>');
[o2_endscript]
@wait time=1000 canskip=false

@postoiceaction type="oice.end"

'''