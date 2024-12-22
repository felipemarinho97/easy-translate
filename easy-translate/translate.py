import os
from difflib import SequenceMatcher
from utils.sync import align_lists
from batch import call_model_openai_batch
from langdetect import detect
from providers.badrock import call_model_bedrock
from providers.openai import call_model_openai
from providers.cloud import google_translate
from utils.codes import get_language

# Model ID
MODEL_ID = os.getenv("MODEL")
delimiter1 = "<|§|>"
delimiter2 = "<|/§|>"

def similarity(str1, str2):
    return SequenceMatcher(None, str1, str2).ratio()

def call_model(system_prompt, user_prompt, assistant_prompt, model_id, max_tokens=2048, temperature=0.2, top_p=0.9):
    model_name = model_id.split("/")[-1]
    if "openai" in model_id.lower():
        return call_model_openai(system_prompt, user_prompt, assistant_prompt, model_name, max_tokens, temperature, top_p)
    elif "bedrock" in model_id.lower():
        return call_model_bedrock(system_prompt, user_prompt, assistant_prompt, model_name, max_tokens, temperature, top_p)
    else:
        raise Exception(f"Model '{model_id}' not supported")

def call_model_batch(system_prompt, user_prompt, assistant_prompt=None, model_id="openai/gpt-4o-mini", max_tokens=2048, temperature=0.2, top_p=0.9):
    model_name = model_id.split("/")[-1]
    if "openai/" in model_id.lower():
        return call_model_openai_batch(system_prompt, user_prompt, assistant_prompt, model_name, max_tokens, temperature, top_p)
    else:
        raise Exception(f"Batch not supported for model '{model_id}'")

def translate_call(texts, source_lang, target_lang):
    texts = [f"{delimiter1}{text}{delimiter2}" for text in texts]
    text = "\n".join(texts)
    system_prompt = f"""Translate the following dialogues from {source_lang} to {target_lang}.
Rules:
Ensure that the translation captures the tone, context, and nuances of the original dialogue.
Where appropriate, use expressions, slang, or phrases that are more natural and relatable for {target_lang} speakers.
Maintain the formatting, such as the time codes and speaker tags, as they are critical for subtitles.
The translation should be accurate, culturally relevant, and easy to understand for native {target_lang} speakers.
Use the separator {delimiter1} and {delimiter2} to separate the dialogues.
"""
    assistant_prompt = f"""Here is the translation of the dialog from {source_lang} to {target_lang}:"""

    result = call_model(system_prompt, text, assistant_prompt, model_id=MODEL_ID)

    result = result.replace(delimiter1, "").replace(delimiter2, "")
    return result.split("\n")

def is_target_lang(lang_code, text):
    dtct = detect(text)
    if dtct == lang_code:
        return True

def translate_texts(texts, source_lang_code, target_lang_code):
    source_lang = get_language(source_lang_code)
    target_lang = get_language(target_lang_code)

    try:
        reference_texts = google_translate(texts, source_lang["code"], target_lang["code"])
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise e

    try:
        translated_texts = translate_call(texts, source_lang["englishName"], target_lang["englishName"])
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise e

    translated_texts = [text for text in translated_texts if text.strip()]

    _, trans = align_lists(reference_texts, translated_texts)

    for i, (original, reference, translated) in enumerate(zip(texts, reference_texts, trans)):
        sim = similarity(reference, translated)
        if translated.strip() == "":
            print(f"{original} -> <empty> 🚨, reference: {reference}")
            trans[i] = reference
        elif sim < 0.5:
            print(f"{original} -> {translated} ⚠️ similarity: {sim}, reference: {reference}")
        else:
            print(f"{original} -> {translated}")

    if len(texts) != len(trans):
        raise Exception("Number of translated texts does not match the number of input texts")

    return trans, source_lang["code"], target_lang["code"]
