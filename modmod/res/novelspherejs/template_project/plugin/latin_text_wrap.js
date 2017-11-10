class LatinTextWrap extends TextCustomizer {
  constructor(textLayer, oldTexts, newTexts) {
    super(textLayer, oldTexts, newTexts);
    this.textLayer = textLayer;
    this.newTexts = newTexts;
  }

  perform() {
    // Only work for horizontal writing
    if (!this.textLayer.vertical) {
      const margin = this.textLayer.margin;
      const lineWidth = this.textLayer.rect.width - margin.left - margin.right;

      let word = '';
      let _x = this.textLayer.textCursor.x;
      let _y = this.textLayer.textCursor.y;

      this.newTexts.forEach((text, index) => {
        if (_x > lineWidth) {

          // Set position to new line
          _x = margin.left;
          _y += this.textLayer.lastLineSize + this.textLayer.style.lineSpacing;

          // Move word to new line
          for (let i = index - word.length; i < index; i++) {
            let _text = this.newTexts[i];
            _text.rect.x = _x;
            _text.rect.y = _y;
  
            _x = _text.rect.x + _text.rect.width;
          }
        }

        const isLatin = /[A-zÀ-ÖØ-öø-ÿ]/i.test(text.text);
        if (isLatin) {
          word += text.text;
        } else {
          word = '';
        }

        text.rect.x = _x;
        text.rect.y = _y;

        _x += text.rect.width;
      });
    }
  }
}

MessageLayer.textCustomizers.latinTextWrap = LatinTextWrap;

Tag.actions.toggle_latin_text_wrap = new TagAction({
  rules: {
    layer: { type: 'MESSAGE_LAYER', required: true },
    page : { type: /fore|back/, required: true }
  },
  action: (args) => {
    const layer = args.layer[args.page];
    let index = layer.textCustomizers.indexOf('latinTextWrap');
    if (index >= 0) {
      layer.textCustomizers.splice(index, 1);
    } else {
      layer.textCustomizers.push('latinTextWrap');
    }
    return 0;
  }
});