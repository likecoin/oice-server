class LatinTextWrap extends TextCustomizer {
  constructor(textLayer, oldTexts, newTexts) {
    super(textLayer, oldTexts, newTexts);
    this.textLayer = textLayer;
    this.newTexts = newTexts;
    this.wordRegex = /[a-zA-Z0-9.,'"?!$#%()@;，、。？！：；《》「」『』À-ÖØ-öø-ÿ]/i;
  }

  perform() {
    // Only work for horizontal writing
    if (!this.textLayer.vertical) {
      const margin = this.textLayer.margin;
      const lineWidth = this.textLayer.rect.width - margin.left - margin.right;

      let word = '';
      let _x = this.textLayer.textCursor.x;
      let _y = this.textLayer.textCursor.y;

      this.newTexts.forEach((text, index, texts) => {
        const isWordCharacter = this.wordRegex.test(text.text);

        if (_x > lineWidth) {
          // Set position to new line
          _x = margin.left;
          _y += this.textLayer.lastLineSize + this.textLayer.style.lineSpacing;

          // For English, move the whole word to new line
          // For avoiding any leading punctuation in Chinese and Japanese,
          // move the previous character to new line only
          const textsToBeMoved = (index > 0 && isWordCharacter && word.length === 0) ? texts[index - 1].text : word;
          for (let i = index - textsToBeMoved.length; i < index; i++) {
            let _text = texts[i];

            _text.rect.x = _x;
            _text.rect.y = _y;

            _x = _text.rect.x + _text.rect.width;
          }
        }

        if (isWordCharacter) {
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