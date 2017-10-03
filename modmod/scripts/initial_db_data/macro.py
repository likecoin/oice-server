asset_types = {
    "image": {
      "name": "圖片",
      "type": "image"
    },
    "fgimage": {
      "name": "前景（立繪）",
      "type": "image"
    },
    "bgimage": {
      "name": "背景圖片",
      "type": "image"
    },
    "face": {
      "name": "頭像",
      "type": "image"
    },
    "bgm": {
      "name": "背景音樂",
      "type": "audio"
    },
    "se": {
      "name": "效果音",
      "type": "audio"
    },
    "video": {
      "name": "影片",
      "type": "video"
    },
    "not-categorized": {
      "name": "未分類",
      "type": "others"
    },
    "animation": {
      "name": "動畫檔案",
      "type": "animation"
    },
    "others": {
      "name": "其他",
      "type": "others"
    }
}

buildin_block_group = {
  "__button_group": {
    "name": "按鈕"
  },
  "__speech": {
    "name": "說話"
  }
}

buildin_macro_list = {
  "s": {
    "name": "停止"
  },
  "current": {
    "name": "指定文字圖層",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "message_layer"
      },
      "page": {
        "name": "頁",
        "type": "page"
      }
    }
  },
  "wait": {
    "name": "等待",
    "attributes": {
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "true"
      }
    }
  },
  "quake": {
    "name": "震動",
    "attributes": {
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "hmax": {
        "name": "最大水平幅度",
        "type": "number"
      },
      "vmax": {
        "name": "最大垂直幅度",
        "type": "number"
      }
    }
  },
  "wq": {
    "name": "等待震動停止",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "deffont": {
    "name": "設定預設字形",
    "attributes": {
      "size": {
        "name": "字體大小",
        "type": "number"
      },
      "face": {
        "name": "字體",
        "type": "string"
      },
      "color": {
        "name": "顏色",
        "type": "color"
      },
      "edge": {
        "name": "邊框",
        "type": "boolean"
      },
      "edgecolor": {
        "name": "邊框顏色",
        "type": "color"
      },
      "bold": {
        "name": "粗體",
        "type": "boolean"
      },
      "o2_shadow": {
        "name": "影子",
        "type": "boolean"
      },
      "o2_shadowcolor": {
        "name": "影子顏色",
        "type": "color"
      }
    }
  },
  "defstyle": {
    "name": "設定預設樣式",
    "attributes": {
      "linespacing": {
        "name": "行距",
        "type": "number"
      },
      "pitch": {
        "name": "字距",
        "type": "number"
      },
      "linesize": {
        "name": "行高",
        "type": "number"
      }
    }
  },
  "delay": {
    "name": "設定文字顯示速度",
    "attributes": {
      "speed": {
        "name": "速度",
        "type": "number",
        "required": True
      }
    }
  },
  "er": {
    "name": "重設文字圖層"
  },
  "font": {
    "name": "設定字形",
    "attributes": {
      "size": {
        "name": "大小",
        "type": "number"
      },
      "face": {
        "name": "字體",
        "type": "string"
      },
      "color": {
        "name": "顏色",
        "type": "color"
      },
      "italic": {
        "name": "斜體",
        "type": "boolean"
      },
      "edge": {
        "name": "邊框",
        "type": "boolean"
      },
      "edgecolor": {
        "name": "邊框顏色",
        "type": "color"
      },
      "bold": {
        "name": "粗體",
        "type": "boolean"
      },
      "o2_shadow": {
        "name": "影子",
        "type": "boolean"
      },
      "o2_shadowcolor": {
        "name": "影子顏色",
        "type": "color"
      }
    }
  },
  "glyph": {
    "name": "等待操作的設定",
    "attributes": {
      "line": {
        "name": "等待換行的檔案",
        "type": "string"
      },
      "page": {
        "name": "等待換頁的檔案",
        "type": "string"
      },
      "fix": {
        "name": "固定",
        "type": "boolean"
      },
      "left": {
        "name": "左",
        "type": "number"
      },
      "top": {
        "name": "上",
        "type": "number"
      }
    }
  },
  "l": {
    "name": "等待點擊（改行）"
  },
  "p": {
    "name": "等待點擊（改頁）"
  },
  "position": {
    "name": "設定文字圖層",
    "attributes": {
      "layer": {
        "name": "文字圖層",
        "type": "message_layer"
      },
      "page": {
        "name": "頁",
        "type": "page"
      },
      "left": {
        "name": "左",
        "type": "number"
      },
      "top": {
        "name": "上",
        "type": "number"
      },
      "width": {
        "name": "寬",
        "type": "number"
      },
      "height": {
        "name": "高",
        "type": "number"
      },
      "frame": {
        "name": "背景圖片",
        "type": "image"
      },
      "color": {
        "name": "顏色",
        "type": "color"
      },
      "opacity": {
        "name": "透明度",
        "type": "number"
      },
      "marginl": {
        "name": "左邊邊緣",
        "type": "number"
      },
      "margint": {
        "name": "上邊邊緣",
        "type": "number"
      },
      "marginr": {
        "name": "右邊邊緣",
        "type": "number"
      },
      "marginb": {
        "name": "下邊邊緣",
        "type": "number"
      },
      "vertical": {
        "name": "垂直",
        "type": "boolean"
      },
      "visible": {
        "name": "可視",
        "type": "boolean"
      }
    }
  },
  "r": {
    "name": "改行"
  },
  "resetfont": {
    "name": "重設字形"
  },
  "resetstyle": {
    "name": "重設樣式"
  },
  "style": {
    "name": "設定樣式",
    "attributes": {
      "align": {
        "name": "文字靠齊",
        "type": "align"
      },
      "linespacing": {
        "name": "行距",
        "type": "number"
      },
      "pitch": {
        "name": "字距",
        "type": "number"
      },
      "linesize": {
        "name": "行高",
        "type": "number"
      },
      "autoreturn": {
        "name": "自動換行",
        "type": "boolean"
      }
    }
  },
  "locate": {
    "name": "移動座標",
    "attributes": {
      "x": {
        "name": "左",
        "type": "number"
      },
      "y": {
        "name": "上",
        "type": "number"
      }
    }
  },
  "history": {
    "name": "記錄設定",
    "attributes": {
      "output": {
        "name": "輸出",
        "type": "boolean"
      },
      "enabled": {
        "name": "啓動",
        "type": "boolean"
      }
    }
  },
  "jump": {
    "name": "跳轉",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "ks_file"
      },
      "target": {
        "name": "目標",
        "type": "string"
      }
    }
  },
  "call": {
    "name": "呼叫腳本",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "ks_file"
      },
      "target": {
        "name": "目標",
        "type": "string"
      }
    }
  },
  "return": {
    "name": "返回上層",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "ks_file"
      },
      "target": {
        "name": "目標",
        "type": "string"
      }
    }
  },
  "backlay": {
    "name": "準備切換",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "layer"
      }
    }
  },
  "button": {
    "name": "顯示按鈕",
    "attributes": {
      "graphic": {
        "name": "圖片",
        "type": "image",
        "required": True
      },
      "storage": {
        "name": "調到檔案",
        "type": "ks_file"
      },
      "target": {
        "name": "目標",
        "type": "string"
      }
    }
  },
  "copylay": {
    "name": "複製圖層",
    "attributes": {
      "srclayer": {
        "name": "來自圖層",
        "type": "layer",
        "required": True
      },
      "destlayer": {
        "name": "目標圖層",
        "type": "layer",
        "required": True
      },
      "srcpage": {
        "name": "來自頁",
        "type": "page",
        "default_value": "fore"
      },
      "destpage": {
        "name": "目標頁",
        "type": "page",
        "default_value": "fore"
      }
    }
  },
  "image": {
    "name": "顯示圖片",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "image",
        "required": True
      },
      "layer": {
        "name": "圖層",
        "type": "layer",
        "required": True
      },
      "page": {
        "name": "頁",
        "type": "page",
        "default_value": "fore"
      },
      "shadow": {
        "name": "影子",
        "type": "color"
      },
      "shadowopacity": {
        "name": "影子透明度",
        "type": "number",
        "default_value": 200
      },
      "shadowx": {
        "name": "影子位移（左）",
        "type": "number",
        "default_value": 10
      },
      "shadowy": {
        "name": "影子位移（上）",
        "type": "number",
        "default_value": 10
      },
      "shadowblur": {
        "name": "模糊影子",
        "type": "number",
        "default_value": 3
      },
      "visible": {
        "name": "可視",
        "type": "boolean"
      },
      "left": {
        "name": "左",
        "type": "number"
      },
      "top": {
        "name": "上",
        "type": "number"
      },
      "opacity": {
        "name": "透明度",
        "type": "number255"
      },
      "mcolor": {
        "name": "色調",
        "type": "color"
      },
      "mopacity": {
        "name": "色調強度",
        "type": "number255"
      }
    }
  },
  "freeimage": {
    "name": "清除圖片",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "layer",
        "required": True
      },
      "page": {
        "name": "頁",
        "type": "page",
        "default_value": "fore"
      },
    }
  },
  "layopt": {
    "name": "設定圖層",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "layer",
        "required": True
      },
      "page": {
        "name": "頁面",
        "type": "page",
        "default_value": "fore"
      },
      "visible": {
        "name": "可視",
        "type": "boolean"
      },
      "left": {
        "name": "左",
        "type": "number"
      },
      "top": {
        "name": "上",
        "type": "number"
      },
      "opacity": {
        "name": "透明度",
        "type": "number255"
      }
    }
  },
  "move": {
    "name": "移動圖層",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "layer",
        "required": True
      },
      "page": {
        "name": "頁面",
        "type": "page",
        "default_value": "fore"
      },
      "spline": {
        "name": "自動曲線",
        "type": "boolean"
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "delay": {
        "name": "延遲",
        "type": "number"
      },
      "path": {
        "name": "路徑",
        "type": "string"
      },
      "accel": {
        "name": "加速度",
        "type": "number",
        "default_value": 0
      }
    }
  },
  "pimage": {
    "name": "追加圖片",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "image",
        "required": True
      },
      "layer": {
        "name": "圖層",
        "type": "layer",
        "required": True
      },
      "page": {
        "name": "頁面",
        "type": "page",
        "default_value": "fore"
      },
      "dx": {
        "name": "目標座標（左）",
        "type": "number",
        "required": True
      },
      "dy": {
        "name": "目標座標（上）",
        "type": "number",
        "required": True
      },
      "sx": {
        "name": "來源座標（左）",
        "type": "number",
        "default_value": 0
      },
      "sy": {
        "name": "來源座標（上）",
        "type": "number",
        "default_value": 0
      },
      "sw": {
        "name": "來源寬度",
        "type": "number"
      },
      "sh": {
        "name": "來源高度",
        "type": "number"
      }
    }
  },
  "stopmove": {
    "name": "停止移動"
  },
  "stoptrans": {
    "name": "停止切換"
  },
  "trans": {
    "name": "切換",
    "attributes": {
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "layer": {
        "name": "圖層",
        "type": "layer",
        "default_value": "base"
      },
      "method": {
        "name": "方式",
        "type": "string",
        "default_value": "crossfade"
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
      "vague": {
        "name": "曖昧值",
        "type": "number",
        "default_value": 64
      },
      "rule": {
        "name": "切換規則",
        "type": "image"
      }
    }
  },
  "wa": {
    "name": "等待動畫完結",
    "attributes": {
      "layer": {
        "name": "圖層",
        "type": "image_layer",
        "required": True
      },
      "page": {
        "name": "頁面",
        "type": "page",
        "default_value": "fore"
      },
      "seg": {
        "name": "槽",
        "type": "number"
      }
    }
  },
  "wm": {
    "name": "等待移動完結",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "true"
      }
    }
  },
  "wt": {
    "name": "等待切換完結",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "true"
      }
    }
  },
  "bgmopt": {
    "name": "背景音樂設定",
    "attributes": {
      "volume": {
        "name": "音量",
        "type": "number100"
      }
    }
  },
  "fadebgm": {
    "name": "切換音樂",
    "attributes": {
      "volume": {
        "name": "音量",
        "type": "number100",
        "required": True
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      }
    }
  },
  "fadeinbgm": {
    "name": "切入背景音樂",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "bgm",
        "required": True
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean",
        "default_value": "true"
      }
    }
  },
  "fadeinse": {
    "name": "切入音效",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "storage": {
        "name": "檔案",
        "type": "se",
        "required": True
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "fadeoutbgm": {
    "name": "漸出背景音樂",
    "attributes": {
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      }
    }
  },
  "fadeoutse": {
    "name": "漸出音效",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number100",
        "default_value": 0
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      }
    }
  },
  "fadepausebgm": {
    "name": "漸出並停止背景音樂",
    "attributes": {
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      }
    }
  },
  "fadese": {
    "name": "漸出並停止音效",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "volume": {
        "name": "音量",
        "type": "number100",
        "required": True
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      }
    }
  },
  "pausebgm": {
    "name": "暫停背景音樂"
  },
  "pausevideo": {
    "name": "暫停影片"
  },
  "openvideo": {
    "name": "打開影片",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "video",
        "required": True
      }
    }
  },
  "playbgm": {
    "name": "播放背景音樂",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "bgm",
        "required": True
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean",
        "default_value": "true"
      }
    }
  },
  "playse": {
    "name": "播放音效",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "storage": {
        "name": "檔案",
        "type": "se",
        "required": True
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "playvideo": {
    "name": "播放影片",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "video"
      }
    }
  },
  "resumebgm": {
    "name": "繼續播放背景音樂"
  },
  "resumevideo": {
    "name": "繼續播放影片"
  },
  "seopt": {
    "name": "音效設定",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "volume": {
        "name": "音量",
        "type": "number"
      },
      "gvolume": {
        "name": "全域音量",
        "type": "number"
      }
    }
  },
  "stopbgm": {
    "name": "停止背景音樂"
  },
  "stopse": {
    "name": "停止音效",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      }
    }
  },
  "stopvideo": {
    "name": "停止影片"
  },
  "video": {
    "name": "影片設定",
    "attributes": {
      "visible": {
        "name": "可視",
        "type": "boolean"
      },
      "left": {
        "name": "左",
        "type": "number"
      },
      "top": {
        "name": "上",
        "type": "number"
      },
      "width": {
        "name": "寬",
        "type": "number"
      },
      "height": {
        "name": "高",
        "type": "number"
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean"
      },
      "volume": {
        "name": "音量",
        "type": "number100"
      }
    }
  },
  "wb": {
    "name": "等待背景音樂切換完成",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "wf": {
    "name": "等待音效切換完成",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "wl": {
    "name": "等待背景音樂完結",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "ws": {
    "name": "等待音效完結",
    "attributes": {
      "buf": {
        "name": "槽",
        "type": "number",
        "default_value": 0
      },
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "wv": {
    "name": "等待影片完結",
    "attributes": {
      "canskip": {
        "name": "可以跳過",
        "type": "boolean",
        "default_value": "false"
      }
    }
  },
  "xchgbgm": {
    "name": "交換背景音樂",
    "attributes": {
      "storage": {
        "name": "檔案",
        "type": "bgm",
        "required": True
      },
      "loop": {
        "name": "重複播放",
        "type": "boolean",
        "default_value": "true"
      },
      "time": {
        "name": "時間",
        "type": "number",
        "required": True
      },
      "overlap": {
        "name": "覆蓋時間",
        "type": "number",
        "default_value": 0
      },
      "volume": {
        "name": "音量",
        "type": "number100"
      }
    }
  },
  "text": {
    "name": "顯示文字",
    "attributes": {
      "text": {
        "name": "文字",
        "type": "string",
        "required": True
      }
    }
  },
  "label": {
    "name": "記號",
    "attributes": {
      "name": {
        "name": "名字",
        "type": "string",
        "required": True
      },
      "caption": {
        "name": "描述",
        "type": "string"
      }
    }
  },
  "comment": {
    "name": "註解",
    "attributes": {
      "text": {
        "name": "文字",
        "type": "string"
      }
    }
  },
  "option": {
    "name": "選項",
    "attributes": {
      "question": {
        "name": "問題",
        "type": "paragraph"
      },
      "answers": {
        "name": "答案",
        "type": "composedAnswer"
      }
    }
  }
}
