# pylama:ignore=E501

character_macro_list = {
    "lr": {
        "name": "改行等待",
        "content": """
[macro name=lr]
[l][r]
[endmacro]
"""
    },
    "w": {
        "name": "改頁等待",
        "content": """
[macro name=w]
;可在這裡加入等待語音播放完畢的指令
;[endvo]
[p]
[hr]
[er]
[endmacro]
"""
    },
    "characterdialog": {
        "name": "角色對白",
        "attributes": {
            "character": {
                "name": "角色",
                "type": "character"
            },
            "fg": {
                "name": "前景（立繪）",
                "type": "fgimage"
            },
            "position": {
                "name": "位置",
                "type": "position"
            },
            "name": {
                "name": "自定義名稱",
                "type": "string"
            },
            "fliplr": {
                "name": "左右反轉",
                "type": "boolean"
            },
            "fgexit": {
                "name": "退場指令",
                "type": "boolean"
            },
            "dialog": {
                "name": "對白",
                "type": "string"
            },
            "skipwait": {
                "name": "略過等待",
                "type": "boolean",
                "default_value": "false"
            },
            "waitse": {
                "name": "等待音效完結",
                "type": "boolean",
                "default_value": "false"
            }
        },
        "macro_type": "characterdialog"
    },
    "bg": {
        "name": "顯示背景",
        "attributes": {
            "storage": {
                "name": "檔案",
                "type": "bgimage",
                "required": True
            },
            "grayscale": {
                "name": "黑白效果",
                "type": "boolean",
                "default_value": "false"
            },
            "mcolor": {
                "name": "調色",
                "type": "color"
            },
            "mopacity": {
                "name": "調色強度",
                "type": "number255"
            },
            "convert": {
                "name": "反色效果",
                "type": "boolean"
            },
            "clfg": {
                "name": "清除立繪",
                "type": "boolean"
            },
            "hidemes": {
                "name": "消除對話框",
                "type": "boolean"
            },
            "method": {
                "name": "切換樣式",
                "type": "string",
                "default_value": "crossfade"
            },
            "time": {
                "name": "切換時間",
                "type": "number",
                "default_value": "700"
            },
            "rule": {
                "name": "切換規則",
                "type": "others",
            },
            "from": {
                "name": "來自",
                "type": "string",
                "default_value": "left"
            },
            "stay": {
                "name": "停留",
                "type": "string",
                "default_value": "nostay"
            },
            "canskip": {
                "name": "可以跳過",
                "type": "boolean",
                "default_value": "true"
            }
        },
        "content": """
;------------------------------------------------------------------
;★顯示背景
;------------------------------------------------------------------
[macro name=bg]
[backlay]
;一般效果
[image * layer=base storage=%storage|black page=back visible="true" left=0 top=0 grayscale=%grayscale|false mcolor=%mcolor mopacity=%mopacity]
;反色效果
[if o2_exp="mp.convert==='true'"]
[image * layer=base storage=%storage|black page=back visible="true" left=0 top=0 grayscale=%grayscale|false mcolor=%mcolor mopacity=%mopacity rceil=0 gceil=0 bceil=0 rfloor=255 bfloor=255 gfloor=255]
[endif]

;消除立繪
[if o2_exp="mp.clfg==='true'"]
[freeimage layer=0 page="back"]
[freeimage layer=1 page="back"]
[freeimage layer=2 page="back"]
[freeimage layer=3 page="back"]
[freeimage layer=4 page="back"]
[freeimage layer=5 page="back"]
[freeimage layer=6 page="back"]
[freeimage layer=7 page="back"]
;[freeimage layer=event page="back"]
[freeimage layer=8 page="back"]
[endif]

;消除對話框
[if o2_exp="mp.hidemes==='true'"]
[current layer="message0" page="back"]
[er]
[current layer="message1" page="back"]
[er]
[current layer="message2" page="back"]
[er]
[layopt layer="message0" visible="false" page="back"]
[layopt layer="message1" visible="false" page="back"]
[hidesysbutton]
[endif]

[trans method=%method|crossfade time=%time|700 rule=%rule stay=%stay from=%from]
[wt canskip=%canskip|true]
[endmacro]
"""
    },
    "clbg": {
        "name": "清除背景",
        "attributes": {
            "clfg": {
                "name": "連同全部前景",
                "type": "boolean"
            },
            "clfg": {
                "name": "清除立繪",
                "type": "boolean"
            },
            "hidemes": {
                "name": "消除對話框",
                "type": "boolean"
            },
            "method": {
                "name": "切換樣式",
                "type": "string",
                "default_value": "crossfade"
            },
            "time": {
                "name": "切換時間",
                "type": "number",
                "default_value": "700"
            },
            "rule": {
                "name": "切換規則",
                "type": "others",
            },
            "from": {
                "name": "來自",
                "type": "string",
                "default_value": "left"
            },
            "stay": {
                "name": "停留",
                "type": "string",
                "default_value": "nostay"
            },
            "canskip": {
                "name": "可以跳過",
                "type": "boolean",
                "default_value": "true"
            }
        },
        "content": """
;------------------------------------------------------------------
;★消除背景
;------------------------------------------------------------------
[macro name=clbg]
[backlay]
[freeimage layer=base page="back"]
;連同全部前景
[if o2_exp="mp.clfg==='true'"]
[freeimage layer=0 page="back"]
[freeimage layer=1 page="back"]
[freeimage layer=2 page="back"]
[freeimage layer=3 page="back"]
[freeimage layer=4 page="back"]
[freeimage layer=5 page="back"]
[freeimage layer=6 page="back"]
[freeimage layer=7 page="back"]

;[freeimage layer=event page="back"]
[freeimage layer=8 page="back"]
[endif]

;連同對話框
[if o2_exp="mp.hidemes==='true'"]
[current layer="message0" page="back"]
[er]
[current layer="message1" page="back"]
[er]
[current layer="message2" page="back"]
[er]
[layopt layer="message0" visible="false" page="back"]
[layopt layer="message1" visible="false" page="back"]
[hidesysbutton]
[endif]

[trans method=%method|crossfade time=%time|700 rule=%rule stay=%stay from=%from]
[wt canskip=%canskip|true]
[endmacro]
;隱藏系統按鈕
[macro name=hidesysbutton]
    [layopt layer=message2 page=%page|back visible=false]
[endmacro]
"""
    },
    "clfg": {
        "name": "清除前景",
        "attributes": {
            "layer": {
                "name": "清除全部",
                "type": "string"
            },
            "clface": {
                "name": "清除頭像",
                "type": "boolean"
            },
            "hidemes": {
                "name": "連同對話框",
                "type": "boolean"
            },
            "method": {
                "name": "切換樣式",
                "type": "string",
                "default_value": "crossfade"
            },
            "time": {
                "name": "切換時間",
                "type": "number",
                "default_value": "700"
            },
            "rule": {
                "name": "切換規則",
                "type": "others",
            },
            "from": {
                "name": "來自",
                "type": "string",
                "default_value": "left"
            },
            "stay": {
                "name": "停留",
                "type": "string",
                "default_value": "nostay"
            },
            "canskip": {
                "name": "可以跳過",
                "type": "boolean",
                "default_value": "true"
            }
        },
        "content": """
;------------------------------------------------------------------
;★消除人物
;------------------------------------------------------------------
[macro name=clfg]
[backlay]
;消除全部
[if o2_exp="mp.layer=='all'"]
[freeimage layer=0 page="back"]
[freeimage layer=1 page="back"]
[freeimage layer=2 page="back"]
[freeimage layer=3 page="back"]
[freeimage layer=4 page="back"]
[freeimage layer=5 page="back"]
[freeimage layer=6 page="back"]
[freeimage layer=7 page="back"]
;[freeimage layer=event page="back"]
[freeimage layer=8 page="back"]
[endif]
;消除單層
[if o2_exp="mp.layer!='all'"]
[freeimage layer=%layer|0 page="back"]
[endif]
;消除頭像
[if o2_exp="mp.clface=='true'"]
[freeimage layer=8 page="back"]
[endif]
;連同對話框
[if o2_exp="mp.hidemes=='true'"]
[current layer="message0" page="back"]
[er]
[current layer="message1" page="back"]
[er]
[current layer="message2" page="back"]
[er]
[layopt layer="message0" visible="false" page="back"]
[layopt layer="message1" visible="false" page="back"]
[hidesysbutton]
[endif]
[trans method=%method|crossfade time=%time|700 rule=%rule stay=%stay from=%from]
[wt canskip=%canskip|true]
[endmacro]
;隱藏系統按鈕
[macro name=hidesysbutton]
    [layopt layer=message2 page=%page|back visible=false]
[endmacro]
"""
    },
    "fg": {
        "name": "顯示人物",
        "attributes": {
            "storage": {
                "name": "檔案",
                "type": "fgimage",
                "required": True
            },
            "layer": {
                "name": "圖層",
                "type": "image_layer"
            },
            "left": {
                "name": "左",
                "type": "number"
            },
            "top": {
                "name": "上",
                "type": "number"
            },
            "method": {
                "name": "切換樣式",
                "type": "string",
                "default_value": "crossfade"
            },
            "time": {
                "name": "切換時間",
                "type": "number",
                "default_value": "500"
            },
            "rule": {
                "name": "切換規則",
                "type": "others",
            },
            "from": {
                "name": "來自",
                "type": "string",
                "default_value": "left"
            },
            "stay": {
                "name": "停留",
                "type": "string",
                "default_value": "nostay"
            },
            "canskip": {
                "name": "可以跳過",
                "type": "boolean",
                "default_value": "true"
            },
            "fliplr": {
                "name": "左右反轉",
                "type": "boolean"
            }
        },
        "content": """\
;------------------------------------------------------------------
;★顯示人物
;------------------------------------------------------------------
[macro name=fg]
[backlay]
;第一次顯示,指定角色位置
[if o2_exp="mp.pos!=undefined"]
[image * storage=%storage|empty layer=%layer|0 page="back" pos=%pos visible="true"]
[else]
;不指定時,自動調整,使立繪顯示在原位置/指定位置
[eval o2_exp="mp.layer='0'" o2_cond="mp.layer==''"]
[eval o2_exp="mp.left=o2.foreLayers.imageLayers[mp.layer].rect.x" o2_cond="mp.left==undefined"]
[eval o2_exp="mp.top=o2.foreLayers.imageLayers[mp.layer].rect.y" o2_cond="mp.top==undefined"]
[image * storage=%storage layer=%layer page="back" left=%left top=%top visible="true"]
[endif]
[trans method=%method|crossfade time=%time|500 rule=%rule stay=%stay from=%from]
[wt canskip=%canskip|true]
[endmacro]
"""
    },
    "dia": {
        "name": "普通對話框(含頭像)",
        "content": """\
;------------------------------------------------------------------
;★普通對話框(含頭像)
;------------------------------------------------------------------
[macro name=dia]
[rclick enabled="true"]
[history enabled="true"]
[backlay]
[freeimage layer=8 page="back"]
[current layer="message0" page="back"]
[position page="back" layer="message0" visible="true" frame="&f.config_dia.dia.frame" left="&f.config_dia.dia.left" top="&f.config_dia.dia.top" marginl="&f.config_dia.dia.marginl" marginr="&f.config_dia.dia.marginr" margint="&f.config_dia.dia.margint" marginb="&f.config_dia.dia.marginb"]
;顯示系統按鈕層
[showsysbutton]
[trans method="crossfade" time=200]
[wt]
[current layer="message0" page="fore"]
[endmacro]
[macro name=showsysbutton]
[layopt layer=message2 page=%page|back visible=true]
[endmacro]
"""
    },

    "selstart": {
        "name": "準備選項",
        "attributes": {
            "hidemes": {
                "name": "隱藏對話層",
                "type": "boolean"
            },
            "hidesysbutton": {
                "name": "隱藏按鈕層",
                "type": "boolean"
            }
        },
        "content": """\
[macro name=selstart]
[hr]
[backlay]
;隱藏對話層、消除頭像
[if o2_exp="mp.hidemes"]
[rclick enabled="false"]
[layopt layer="message0" visible="false" page=back]
[freeimage layer="8" page=back]
[endif]
;隱藏按鈕層
[if o2_exp="mp.hidesysbutton"]
[rclick enabled="false"]
[hidesysbutton]
[endif]
;顯示選項層
;[frame layer="message1" page="back"]
;將選項背景從透明修改為專用圖
[position layer="message1" page=back visible=true frame=""]
[current layer="message1" page="back"]
[nowait]
[endmacro]
"""
    },

    "selend": {
        "name": "等待選擇-選項",
        "attributes": {
            "method": {
                "name": "切換樣式",
                "type": "string",
                "default_value": "crossfade",
                "required": True
            },
            "time": {
                "name": "時間",
                "type": "number",
                "default_value": "300",
                "required": True
            },
            "rule": {
                "name": "切換規則",
                "type": "others",
            },
            "from": {
                "name": "來自",
                "type": "string",
                "default_value": "left"
            },
            "stay": {
                "name": "停留",
                "type": "string",
                "default_value": "nostay"
            },
            "canskip": {
                "name": "可以跳過",
                "type": "boolean",
                "default_value": "true"
            },
        },
        "content": """\
[macro name=selend]
[endnowait]

[trans method=%method|crossfade time=%time|300 rule=%rule|01 from=%from stay=%stay]
[wt canskip=%canskip]
[s]
[endmacro]
"""
    },

    "selbutton": {
        "name": "按鈕選項",
        "attributes": {
            "normal": {
                "name": "普通圖像",
                "type": "image",
                "required": True
            },
            "on": {
                "name": "按下圖像",
                "type": "image",
                "required": True
            },
            "over": {
                "name": "指下去的圖像",
                "type": "image",
                "required": True
            },
            "storage": {
                "name": "檔案",
                "type": "ks_file",
                "required": True
            },
            "target": {
                "name": "目標標籤",
                "type": "string"
            },
            "text": {
                "name": "文字",
                "type": "string",
                "required": True
            }
        },
        "content": """\
[o2_iscript ]
var TextButton = function (normal, on, over, x, y) {
    KAGButton.call(this, normal, x, y);
    this.rect.width *= 3; // because text button uses separate images
    this.options.clipWidth = this.rect.width;

    this.normal = normal;
    this.on = on;
    this.over = over;
    this.text = "";
    this.layerFont = {};
};

TextButton.prototype = Object.create(KAGButton.prototype);

TextButton.prototype.clone=function(){
    var newButton = new TextButton(this.normal, this.on, this.over, this.rect.x, this.rect.y);
    newButton.importFrom(this);
    return newButton;
}

TextButton.prototype.importFromKAGArgs = function (args) {
    KAGButton.prototype.importFromKAGArgs.call(this, args);
    this.text = args.text || "";
};

TextButton.prototype.importFrom=function(other){
    KAGButton.prototype.importFrom.call(this,other);
    this.normal = other.normal;
    this.on = other.on;
    this.over = other.over;
    this.text = other.text;
    this.layerFont = clone(other.layerFont);
}

TextButton.prototype.drawOnContext = function (context) {
    switch( this.state ){
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

    var texts = new TextProperties(this.text);
    $.extend( texts.styles, this.layerFont );
    texts.styles.visible = true;
    var textSize = texts.measure(context);

    var x = (this.rect.width - textSize.width)/2;
    var y = (this.rect.height - textSize.height)/2;

    texts.rect = {
        x : x + this.rect.x,
        y : y + this.rect.y,
        width : textSize.width,
        height : textSize.height
    };
    context.textBaseline = "top";

    switch( this.state ){
        case Button.STATE_HOVER:
            texts.drawOnContext(context);
            break;

        case Button.STATE_DOWN:
            texts.drawOnContext(context);
            break;

        case Button.STATE_NORMAL:
        default:
            texts.drawOnContext(context);
    }
};

Tag.actions.selbutton = new TagAction({
    rules:{
        normal:       {type:"STRING", required:true},
        on:           {type:"STRING", required:true},
        over:         {type:"STRING", required:true},
        storage:      {type:"STRING"},
        target:       {type:"STRING"},
        text:         {type:"STRING", required:true}
    },
    action:function(args){
        var _this=this;

        var normal = ResourceLoader.loadImage(args.normal);
        var on = ResourceLoader.loadImage(args.on);
        var over = ResourceLoader.loadImage(args.over);

        $.when(normal, on, over)
        .done(function(normal, on, over){

            setTimeout(function () {
                var cursor = o2.currentMessageLayer.textCursor;

                var newButton = new TextButton(normal, on, over, cursor.x, cursor.y);
                newButton.layerFont = clone(o2.currentMessageLayer.font);
                newButton.importFromKAGArgs(args);

                o2.currentMessageLayer.addButton(newButton);

                if( o2.currentMessageLayerWithBack ){
                    o2.currentMessageLayer.getCorrespondingLayer().addButton( clone(newButton) );
                }

                _this.done();
            });
        });

        return 1;
    }
});
[o2_endscript]
"""
    }
}
