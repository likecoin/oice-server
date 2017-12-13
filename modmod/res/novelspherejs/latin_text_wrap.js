class LatinTextWrap extends TextCustomizer {
  constructor(textLayer, oldTexts, newTexts) {
    super(textLayer, oldTexts, newTexts);
    this.textLayer = textLayer;
    this.newTexts = newTexts;

    /**
     * For English, move the whole word to new line
     * For avoiding any leading punctuation in Chinese and Japanese,
     */
    this.exceptionRegex = /[a-zA-Z0-9.,'"?!$#%()@;，、。？！：；《》「」『』À-ÖØ-öø-ÿ]/i;
  }

  perform() {
    // Only work for horizontal writing
    if (!this.textLayer.vertical) {
      const { margin, lastLineSize, rect, style, textCursor } = this.textLayer;
      const maxLineWidth = rect.width - margin.left - margin.right;

      let { x, y } = textCursor;

      this.newTexts.forEach((text, index, texts) => {
        if (x > maxLineWidth) {
          // Set position to new line
          x = margin.left;
          y += lastLineSize + style.lineSpacing;

          let moveStart = index;
          while (moveStart > 0 && this.exceptionRegex.test(texts[moveStart].text)) {
            moveStart--;
          }

          for (let i = moveStart; i < index; i++) {
            let _text = texts[i];

            _text.rect.x = x;
            _text.rect.y = y;

            // Prevent leading space in new line
            if (/\S/.test(_text.text)) x += _text.rect.width;
          }
        }

        text.rect.x = x;
        text.rect.y = y;

        x += text.rect.width;
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