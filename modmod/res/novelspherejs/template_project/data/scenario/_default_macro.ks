;Helper functions
[o2_iscript]
tf._getDefaultDialogMessageLayerSetting = function (override) {
  var VIEW_SIZE = tf.oiceDefaults.viewSize;
  var MESSAGE_LAYER = tf.oiceDefaults.messageLayer;

  var setting = {
    left: 0,
    width: VIEW_SIZE,
    height: MESSAGE_LAYER.height,
    margin: {
      top: MESSAGE_LAYER.margin.top - MESSAGE_LAYER.minPadding - tf.oiceDefaults.lineSpacing,
      left: MESSAGE_LAYER.margin.left,
      right: MESSAGE_LAYER.margin.right,
    },
    lineHeight: tf.oiceDefaults.fontSize + tf.oiceDefaults.lineSpacing
  };

  setting.top = VIEW_SIZE - setting.height;

  if (override) {
      setting = Object.assign(setting, override)
  }

  return setting;
};
[o2_endscript]


;Communication
;=============
[o2_iscript]
Tag.actions.postoiceaction = new TagAction({
    rules: {
        type:    { type: "STRING", required: true },
        payload: { type: "STRING", required: false },
    },
    action: function(args) {
        var action = { type: args.type };
        if (args.payload) {
            action.payload = args.payload;
            try {
                action.payload = JSON.parse(args.payload);
            } catch(e) {
                // Do nothing
            }
        }

        window.parent.postMessage(JSON.stringify(action), "*");

        return 0;
    }
});

Tag.actions.oice_error = new TagAction({
    rules: {
        code:    { type: "STRING", required: true },
        message: { type: "STRING", required: false },
    },
    action: function(args) {
        o2.error('[oice] ' + args.message);
        new Tag('postoiceaction', {
            type: 'oice.error',
            payload: JSON.stringify({
                code: args.code,
                message: args.message,
            }),
        }).run();

        return 0;
    }
});
[o2_endscript]


;Load external javascript
;------------------------
[o2_iscript]
Tag.actions.oice_request = new TagAction({
    rules: {
        param: { type: "STRING", required: false }
    },
    action: function(args) {
        var _this = this;
        $.getJSON(tf.oiceDefaults.communicationURL + '?' + args.param, function(json) {
            eval(json.script);
            _this.done();
        }).fail(function() {
            new Tag('oice_error', {
                code: 'ERR_LOAD_EXTERNAL_SCRIPT_FAIL',
            		message: 'There is an error when fetching external script.'
            }).run();
            _this.done();
        });
        return 1;
    }
});
[o2_endscript]

@o2_loadplugin module="latin_text_wrap.js?v=1"
@toggle_latin_text_wrap layer="message0" page="fore"


;Play Behavior
;=============
[macro name=autoplay]
@if o2_exp="!o2.autoMode"
@o2_enterautomode
@endif
@if o2_exp="mp.autoWaitTimeInterval"
@eval o2_exp="f.autoWaitTimeInterval = mp.autoWaitTimeInterval"
@else
@eval o2_exp="f.autoWaitTimeInterval = 400"
@endif
@delay speed=%delayspeed|60
[endmacro]

[macro name=autowait]
@if o2_exp="f.autoWaitTimeInterval"
@wait time="&f.autoWaitTimeInterval" canskip=true
@endif
[endmacro]


[macro name=oice_jump]
@eval o2_exp="tf._hasJumped = true"
@jump storage=%storage target=%target
[endmacro]


;Dialog
;======
[macro name=keyword]
@font color=%color|0xffff00
[endmacro]

[macro name=endkeyword]
@resetstyle
@resetfont
[endmacro]

[macro name=clearmessage]
@backlay
@layopt layer=message0 visible=false page=back
@layopt layer=message1 visible=false page=back
@layopt layer=message2 visible=false page=back
@trans method=crossfade time=200
@wt
[endmacro]

/**
 * Set wait click glyph
 * @attr {Number} framewidth  (Optional) The width of the message layer that contains the glyph 
 * @attr {Number} frameheight (Optional) The height of the message layer that contains the glyph 
 */
[macro name=oice_glyph]
[o2_iscript]
tf._glyph = function () {
  var defaultMessageSetting = tf._getDefaultDialogMessageLayerSetting();
  var offset = tf.oiceDefaults.glyph.size + tf.oiceDefaults.glyph.offset;

  var framewidth = mp.framewidth || defaultMessageSetting.width;
  var frameheight = mp.frameheight || defaultMessageSetting.height;

  return {
    left: framewidth - offset,
    top: frameheight - offset,
  };
}();
[o2_endscript]
@glyph fix=true left=&tf._glyph.left top=&tf._glyph.top
[endmacro]

/**
 * Show dialog layer 
 */
[macro name=dialog]
[o2_iscript]
tf._dialog = tf._getDefaultDialogMessageLayerSetting();
if (mp.fullscreen == "true") {
  tf._dialog.top = 0;
  tf._dialog.height = tf.oiceDefaults.viewSize;
  tf._dialog.margin.top = tf.oiceDefaults.messageLayer.height;
}
tf._dialog.page = mp.fadein === 'true' ? 'back' : 'fore';
[o2_endscript]

;Fade in dialog frame
@backlay o2_cond="mp.fadein === 'true'"

[position layer=message0
          page=&tf._dialog.page
          left=0
          top=&tf._dialog.top
          width=&tf._dialog.width
          height=&tf._dialog.height
          marginl=&tf._dialog.margin.left
          margint=&tf._dialog.margin.top
          marginr=&tf._dialog.margin.right
          visible=true
          color=&tf.oiceDefaults.messageLayer.color
          opacity=&tf.oiceDefaults.messageLayer.opacity
          frame=""
]

;Fade in dialog frame
[if o2_exp="mp.fadein === 'true'"]
	@trans method=crossfade time=200
	@wt
[endif]

@current layer=message0 page=fore
;Repostion wait click glyph
@oice_glyph framewidth=&tf._dialog.width frameheight=&tf._dialog.height
@resetfont
@resetstyle
[endmacro]

;Narrator
;--------
[macro name=asideTalk]
;Hide character name
@position layer=message1 visible=false page=fore
@position layer=message1 visible=false page=back
[endmacro]

;Fade out message layer
[macro name=asideOut]
@backlay
@layopt layer=message0 page=back visible=false
@trans method=crossfade time=200
@wt canskip=true
[endmacro]


;Character
;=========
[macro name=charactername]
@optionclear
[o2_iscript]
if (!tf._characterdialog) {
  tf._characterdialog = function () {
    var FACTOR = tf.oiceDefaults.scaleFactor;
    var VIEW_SIZE = tf.oiceDefaults.viewSize;
    var MESSAGE_LAYER = tf.oiceDefaults.messageLayer;

    var messageSetting = tf._getDefaultDialogMessageLayerSetting();

    // Name field
    var nameSetting = {
      left: 0,
      width: VIEW_SIZE,
      height: 80 * FACTOR,
      margin: {
        top: 22 * FACTOR - tf.oiceDefaults.lineSpacing - MESSAGE_LAYER.minPadding, 
        left: messageSetting.margin.left,
      },
      fontSize: 40 * FACTOR,
    };

    nameSetting.top = messageSetting.top - nameSetting.height;

    return {
      name: nameSetting,
    };
  }();
}
[o2_endscript]
;Character name
@current layer=message1 page=fore
[position layer=message1
          page=fore
          top=&tf._characterdialog.name.top
          left=&tf._characterdialog.name.left
          width=&tf._characterdialog.name.width
          height=&tf._characterdialog.name.height
          margint=&tf._characterdialog.name.margin.top
          marginl=&tf._characterdialog.name.margin.left
          visible=true
          frame="name_bg"
]
@resetfont
@resetstyle
@font size=&tf._characterdialog.name.fontSize bold=true
@ch text=%name
[endmacro]

;角色进场处理
;---------
[macro name=fgLeft]
;显示左边的人物图像，参数需要storage，top，left，fliplr（默认=0，不翻转）
[layopt layer=1 index=100]
[backlay]
[image storage=%storage layer=1 page=back top=%top|0 left=%left|0 visible=true fliplr=%fliplr|0 visible=true]
[layopt layer=1 index=100]
[trans time=200]
[wt canskip=true]
[endmacro]

[macro name=fgRight]
;显示右边的人物图像，参数需要storage，top，left，fliplr（默认=1，翻转）
[layopt layer=2 index=200]
[backlay]
[image storage=%storage layer=2 page=back top=%top|0 left=%left|0 visible=true fliplr=%fliplr|1 visible=true]
[layopt layer=2 index=200]
[trans time=200]
[wt canskip=true]
[endmacro]

[macro name=fgMiddle]
;显示中间的人物图像，参数需要storage，top，left，fliplr（默认=0，不翻转）
[layopt layer=3 index=300]
[backlay]
[image storage=%storage layer=3 page=back top=%top|0 left=%left|0 visible=true fliplr=%fliplr|0 visible=true]
[layopt layer=3 index=300]
[trans time=200]
[wt canskip=true]
[endmacro]

;角色对话变换的立绘移位处理
;--------------------
[macro name=fgLeftToDark]
;显示左边变暗过程，参数需要storage，path，fliplr
;path=npcdata的pathDl的值，是人物变暗并移动的目的地路径；
;例如:pathDl=(-110,-90,255)，第三个参数是透明度，这里固定填255；
;mopacity="172"，是人物变暗的尺度，固化数值，不给用户修改；
[if o2_exp="tf._hasJumped"]
@eval o2_exp="tf._hasJumped = false"
[else]
@stoptrans
@image storage=%storage layer=1 page=fore top=%top|0 left=%left|0 visible=true mcolor=0x000000 mopacity=172 fliplr=%fliplr|0
@wait time=50
@move layer=1 path=%path time=140
@layopt layer=1 index=5
@layopt layer=2 index=20
@layopt layer=3 index=30
@wm canskip=true
[endif]
[endmacro]

[macro name=fgRightToDark]
;显示右边变暗过程，参数需要storage，path，fliplr
;path=npcdata的pathDr的值，是人物变暗并移动的目的地路径；
;例如:pathDr=(-110,-90,255)，第三个参数是透明度，这里固定填255；
;mopacity="172"，是人物变暗的尺度，固化数值，不给用户修改；
[if o2_exp="tf._hasJumped"]
@eval o2_exp="tf._hasJumped = false"
[else]
@stoptrans
@image storage=%storage layer=2 page=fore top=%top|0 left=%left|0 visible=true mcolor=0x000000 mopacity=172 fliplr=%fliplr|1
@wait time=50
@move layer=2 path=%path time=140
@layopt layer=1 index=10
@layopt layer=2 index=5
@layopt layer=3 index=30
@wm canskip=true
[endif]
[endmacro]

[macro name=fgLeftToBright]
;显示左边变亮过程，参数需要storage，path，fliplr
;path=npcdata的pathl的值，是人物变亮并移动的目的地路径；
;例如:pathl=(-110,-90,255)，第三个参数是透明度，这里固定填255；
@stoptrans
@image storage=%storage layer=1 page=fore top=%top|0 left=%left|0 visible=true fliplr=%fliplr|0
@wait time=50
@move layer=1 path=%path time=140
@layopt layer=1 index=25
@layopt layer=2 index=20
@layopt layer=3 index=30
@wm
[endmacro]

[macro name=fgRightToBright]
;显示右边变亮过程，参数需要storage，path，fliplr
;path=npcdata的pathr的值，是人物变亮并移动的目的地路径；
;例如:pathr=(-110,-90,255)，第三个参数是透明度，这里固定填255；
@stoptrans
@image storage=%storage layer=2 page=fore top=%top|0 left=%left|0 visible=true fliplr=%fliplr|1
@wait time=50
@move layer=2 path=%path time=140
@layopt layer=1 index=10
@layopt layer=2 index=20
@layopt layer=3 index=30
@wm
[endmacro]

;角色退场处理
;---------
[macro name=fgExitLeft]
@backlay layer=1
@freeimage layer=1 page=back
@trans layer=1 method=crossfade time=200
@wt
[endmacro]

[macro name=fgExitRight]
@backlay layer=2
@freeimage layer=2 page=back
@trans layer=2 method=crossfade time=200
@wt
[endmacro]

[macro name=fgExitMiddle]
@backlay layer=3
@freeimage layer=3 page=back
@trans layer=3 method=crossfade time=200
@wt
[endmacro]


;Options
;=======
;選項問題
;------
[macro name=optionstart]
;隱藏對話層
@clearmessage
;顯示選項層
[o2_iscript]
if (!tf._option) {
  tf._option = tf._getDefaultDialogMessageLayerSetting({
    top: 0,
    height: tf.oiceDefaults.viewSize,
  });
}
[o2_endscript]
[position layer=message2
          page=back
          top=&tf._option.top
          left=&tf._option.left
          width=&tf._option.width
          height=&tf._option.height
          margint=&tf._option.margin.top
          marginl=&tf._option.margin.left
          marginr=&tf._option.margin.right
          visible=true
          frame="option_bg"
]
@current layer=message2 page=back
@nowait
@resetfont
@resetstyle
[endmacro]

[o2_iscript]
var OptionButton = function (normal, on, over, x, y) {
    KAGButton.call(this, normal, x, y);
    this.rect.width = normal.naturalWidth; // get actual width of the button image
    this.options.clipWidth = this.rect.width;

    this.normal = normal;
    this.on = on;
    this.over = over;
    this.text = "";
    this.layerFont = {};
    this.oiceId = 0;
    this.blockId = 0;
    this.index = 0;
};

OptionButton.prototype = Object.create(KAGButton.prototype);

OptionButton.prototype.clone = function() {
    var newButton = new OptionButton(this.normal, this.on, this.over, this.rect.x, this.rect.y);
    newButton.importFrom(this);
    return newButton;
}

OptionButton.prototype.importFromKAGArgs = function (args) {
    KAGButton.prototype.importFromKAGArgs.call(this, args);
    this.text = decodeURIComponent((args.text || "").replace(/!/g, '%')); // Decode text
    this.oiceId = args.oiceid || 0;
    this.blockId = args.blockid || 0;
    this.index = args.index || 0;

    var _click = this.click;

    this.click = function (x, y, layer, isSynthetic) {
        tf._hasJumped = true;

        var payload = {
            oiceId: this.oiceId,
            blockId: this.blockId,
            buttonIndex: this.index,
            isSynthetic: isSynthetic || false,
        }
        var args = {
            type: "oice.didClickOptionButton",
            payload: JSON.stringify(payload),
        }
        new Tag("postoiceaction", args).run();

        _click.apply(this, arguments);
    }
};

OptionButton.prototype.importFrom = function (other) {
    KAGButton.prototype.importFrom.call(this, other);
    this.normal = other.normal;
    this.on = other.on;
    this.over = other.over;
    this.text = other.text;
    this.layerFont = clone(other.layerFont);
}

OptionButton.prototype.drawOnContext = function (context) {
    switch (this.state) {
        case Button.STATE_HOVER:
            this.image = this.over;
            break;

        case Button.STATE_DOWN:
            this.image = this.on;
            break;

        case Button.STATE_NORMAL:
        default:
            this.image = this.normal;
    }

    Button.prototype.drawOnContext.apply(this, arguments);

    var marginTop = 14 * tf.oiceDefaults.scaleFactor;
    var marginBottom = marginTop;
    var marginLeft = 132 * tf.oiceDefaults.scaleFactor;
    var marginRight = tf.oiceDefaults.messageLayer.margin.right;
    var lineSpacing = tf.oiceDefaults.lineSpacing;

    var texts = new TextProperties("");
    $.extend(texts.styles, this.layerFont);
    texts.styles.visible = true;
    texts.styles.size = tf.oiceDefaults.fontSize;
    texts.rect = {
        x: this.rect.x + marginLeft,
        y: this.rect.y + marginTop,
        width: tf.oiceDefaults.viewSize - marginLeft - marginRight,
        height: 164 * tf.oiceDefaults.scaleFactor - marginTop - marginBottom,
    };

    context.textBaseline = "top";

    var lines = [texts.text];
    for (i = 0; i < this.text.length; i++) {        
        // Concat each character and measure the text size
        texts.text = lines[lines.length - 1] += this.text[i];
        var textSize = texts.measure(context);

        // Split text into blocks
        var shouldStartNewLine = textSize.width + texts.styles.size > texts.rect.width;
        if (shouldStartNewLine) {
            lines.push("");
        }
    }

    // Render text
    var lineHeight = texts.styles.size + lineSpacing;
    var textHeight = lineHeight * lines.length - lineSpacing;
    var centerOffset = (texts.rect.height - textHeight) / 2;
    texts.rect.y += centerOffset - tf.oiceDefaults.messageLayer.minPadding;
    for (i = 0; i < lines.length; i++) {
      texts.text = lines[i];
      texts.drawOnContext(context);
      texts.rect.y += lineHeight;
    }
};

Tag.actions.optionbutton = new TagAction({
    rules: {
        normal:  { type: "STRING", required: true },
        on:      { type: "STRING", required: true },
        over:    { type: "STRING", required: true },
        storage: { type: "STRING" },
        target:  { type: "STRING" },
        text:    { type: "STRING", required: true },
        blockid: { type: "INT" },
        oiceid:  { type: "INT" },
        index:   { type: "INT" },
    },
    action: function (args) {
        var _this = this;

        var normal = ResourceLoader.loadImage(args.normal);
        var on = ResourceLoader.loadImage(args.on);
        var over = ResourceLoader.loadImage(args.over);

        $.when(normal, on, over).done(function(normal, on, over) {
            setTimeout(function () {
                var cursor = o2.currentMessageLayer.textCursor;

                var newButton = new OptionButton(normal, on, over, cursor.x, cursor.y);
                newButton.layerFont = clone(o2.currentMessageLayer.font);
                newButton.importFromKAGArgs(args);

                o2.currentMessageLayer.addButton(newButton);

                if (o2.currentMessageLayerWithBack) {
                    o2
                    .currentMessageLayer
                    .getCorrespondingLayer()
                    .addButton(clone(newButton));
                }

                _this.done();
            });
        });

        return 1;
    }
});
[o2_endscript]

;選項答案按鈕
;---------
[macro name="optionanswer"]
;Based on the current number of options, change the background image and y position of button
[o2_iscript]
tf._optionanswer = function() {
  var index = parseInt(mp.index);
  var defaultMessageSetting = tf._getDefaultDialogMessageLayerSetting();
  var setting = {
    x: -1 * defaultMessageSetting.margin.left,
    y: (
      index * 164 * tf.oiceDefaults.scaleFactor
      + defaultMessageSetting.height
      - defaultMessageSetting.margin.top
      - tf.oiceDefaults.lineSpacing
    ),
    image: {
      normal: 'option_' + (index + 1),
    },
  };
  setting.image.hover = setting.image.normal + '_hover';
  return setting;
}();
[o2_endscript]
;Translate the layer to place button
@locate x=&tf._optionanswer.x y=&tf._optionanswer.y
;Display the button
[optionbutton storage=%storage
              target=%target
              normal=&tf._optionanswer.image.normal
              on=&tf._optionanswer.image.hover
              over=&tf._optionanswer.image.hover
              text=%text
              oiceid=%oiceid
              blockid=%blockid
              index=%index
]
[endmacro]

;完結選項
;------
[macro name=optionend]
@endnowait
@trans method=crossfade time=300 rule=01 from=left stay=nostay layer=message2
@wt canskip=true
@s
[endmacro]

;清除選項介面
;---------
[macro name=optionclear]
;如果有選項框的話，便要清除
@if o2_exp="tf._optionanswer !== null"
@eval o2_exp = "tf._optionanswer = null"
@layopt layer=message2 page=back visible=false frame=""
@trans method=crossfade vague=1 time=300
@wt
@endif
[endmacro]

;Miscellaneous
;-------------

;閃
;--
[macro name=flash]
@backlay
[position layer=message3
          page=back
          top=0
          left=0
          width=&tf.oiceDefaults.viewSize
          height=&tf.oiceDefaults.viewSize
          color=%color|0xFF0000
          visible=true
]
@trans method=crossfade time=50
@wt
@backlay
@position layer=message3 page=back visible=false
@trans method=crossfade time=%time|200
@wt
[endmacro]

@return