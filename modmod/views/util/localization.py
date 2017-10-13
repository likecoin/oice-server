import babel


def normalize_language(language):
    language.replace('_', '-')
    try:
        parts = babel.Locale.parse(language, sep='-')
    except babel.UnknownLocaleError:
        parts = babel.Locale('en')

    language = parts.language
    script   = parts.script
    region   = parts.territory

    # Special handle for Chinese
    if language == 'zh':
        if region not in ['HK', 'TW', 'CN']:
            if script == 'Hans':
                region = 'CN'
            else:
                region = 'TW'
        language += '-' + region

    return language


def normalize_ui_language(language):
    if language == 'ja' or language[:2] == 'zh':
        return language
    return'en'


def get_language_code_for_translate(language):
    language_code = language.lower()
    # zh will be regarded as Simplified Chinese
    if language_code[:2] == 'zh' and ('hk' in language_code or 'tw' in language_code):
        language_code = 'zh-TW'
    else:
        language_code = language_code[:2]
        
    return language_code
