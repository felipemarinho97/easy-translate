from easygoogletranslate import EasyGoogleTranslate

def google_translate(texts, source_lang, target_lang):
    text = '\n'.join(texts)

    translator = EasyGoogleTranslate(
        source_language=source_lang,
        target_language=target_lang,
        timeout=10
    )
    result = translator.translate(text)

    return result.split("\n")