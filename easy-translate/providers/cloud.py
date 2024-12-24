from easygoogletranslate import EasyGoogleTranslate

def google_translate(texts, source_lang, target_lang, max_chars=5000):
    def batch_texts(texts, max_chars):
        current_batch = []
        current_length = 0
        for text in texts:
            # Check if adding this text will exceed the max character limit
            if current_length + len(text) + 1 > max_chars:  # +1 for the newline character
                yield current_batch
                current_batch = []
                current_length = 0
            
            # Add the text to the current batch
            current_batch.append(text)
            current_length += len(text) + 1  # +1 for the newline character
        
        # Yield the last batch if it exists
        if current_batch:
            yield current_batch

    result = []
    translator = EasyGoogleTranslate(
        source_language=source_lang.split("-")[0] if source_lang != "auto" else "",
        target_language=target_lang.split("-")[0],
        timeout=10
    )

    # Process each batch and translate
    for batch in batch_texts(texts, max_chars):
        text_to_translate = '\n'.join(batch)
        translated_text = translator.translate(text_to_translate)
        result.extend(translated_text.split("\n"))

    return result