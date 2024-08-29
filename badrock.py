from flask import Flask, request, jsonify
import boto3
import json, os
from botocore.exceptions import ClientError
from sync2 import alinhar_listas
from batch import call_model_openai_batch
from langdetect import detect
from openai import OpenAI
import requests
from easygoogletranslate import EasyGoogleTranslate
from Levenshtein import distance
from difflib import SequenceMatcher

app = Flask(__name__)

# Initialize boto3 client for Bedrock
client = boto3.client('bedrock-runtime', region_name='us-west-2')  # Adjust region as needed

# Initialize the OpenAI API
openai_client = OpenAI(
    api_key = "***REMOVED***"
)

# Model ID
MODEL_ID = "gpt-4o-mini"
# MODEL_ID = "meta.llama3-1-8b-instruct-v1:0"
delimiter1="<|§|>"
delimiter2="<|/§|>"


def similarity(str1, str2):
    # return 1 - (distance(str1, str2) / min(len(str1), len(str2)))
    return SequenceMatcher(None, str1, str2).ratio()


def local_translate(text, source_lang, target_lang):
    output = {"target_lang": target_lang, "source_lang": source_lang}
    target_lang = target_lang.lower()
    source_lang = source_lang.lower()
    if "portuguese" in target_lang:
        tlang = "pt"
    elif "spanish" in target_lang:
        tlang = "es"
    elif "english" in target_lang:
        tlang = "en"
    elif "chinese" in target_lang:
        tlang = "zh"
    
    if "portuguese" in source_lang:
        slang = "pt"
    elif "spanish" in source_lang:
        slang = "es"
    elif "english" in source_lang:
        slang = "en"
    elif "chinese" in source_lang:
        slang = "zh"

    translator = EasyGoogleTranslate(
        source_language=slang,
        target_language=tlang,
        timeout=10
    )
    result = translator.translate(text)

    return result

# function to determine if the output is positive
def is_positive(text):
    lower_text = text.lower()
    positive_words = ["sim", "yes", "si"]
    negative_words = ["não", "no", "nao"]
    for word in positive_words:
        if word in lower_text:
            return True
    for word in negative_words:
        if word in lower_text:
            return False
    return None

# Function to call Amazon Bedrock API using boto3
def call_model_bedrock(system_prompt, user_prompt, assistant_prompt, model_id=MODEL_ID, max_gen_len=2048, temperature=0.2, top_p=0.9):
    prompt = f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt}
<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{user_prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
{assistant_prompt}
"""
    # Format the request payload using the model's native structure
    native_request = {
        "prompt": prompt,
        "max_gen_len": max_gen_len,
        "temperature": temperature,
        "top_p": top_p
    }

    # Convert the native request to JSON
    request_body = json.dumps(native_request)
    print(f"Request: {request_body}")

    try:
        # Invoke the model with the request
        response = client.invoke_model(modelId=model_id, body=request_body)

        # Decode the response body
        model_response = json.loads(response["body"].read())

        # Extract and return the response text
        translated_text = model_response["generation"]
        return translated_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        raise


def call_model_openai(system_prompt, user_prompt, assistant_prompt=None, model_id=None, max_tokens=2048, temperature=0.2, top_p=0.9):
    try:
        # Prepare the messages for the conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # If there's an assistant prompt, include it
        if assistant_prompt:
            messages.append({"role": "assistant", "content": assistant_prompt})
        
        # Make the API call
        response = openai_client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        # Return the assistant's response
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise e

def call_model(system_prompt, user_prompt, assistant_prompt, model_id, max_tokens=2048, temperature=0.2, top_p=0.9):
    if "gpt" in model_id.lower():
        # Use OpenAI 
        return call_model_openai(system_prompt, user_prompt, assistant_prompt, model_id, max_tokens, temperature, top_p)
    else:
        # Use Amazon Bedrock
        return call_model_bedrock(system_prompt, user_prompt, assistant_prompt, model_id, max_tokens, temperature, top_p)

def call_model_batch(system_prompt, user_prompt, assistant_prompt=None, model_id="gpt-4o-mini", max_tokens=2048, temperature=0.2, top_p=0.9):
    if "gpt" in model_id.lower():
        return call_model_openai_batch(system_prompt, user_prompt, assistant_prompt, model_id, max_tokens, temperature, top_p)
    else:
        raise Exception(f"Batch not supported for model '{model_id}'")

# Function to translate a dialogue from source language to target language
def translate_call(text, source_lang, target_lang):
    # split the texts by the break line
    texts = text.split('\n')
    # add delimiter to separate texts
    texts = [f"{delimiter1}{text}{delimiter2}" for text in texts]
    # join the texts
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

    # remove delimiter from the texts
    result = result.replace(delimiter1, "").replace(delimiter2, "")
    return result

# function to determine if the language is target
def is_target_lang(lang, text):
    dtct = detect(text)
    if dtct == lang:
        return True
    elif dtct == "pt" and lang == "portuguese":
        return True
    elif dtct == "es" and lang == "spanish":
        return True
    elif dtct == "en" and lang == "english":
        return True
    elif lang == "chinese" and (dtct == "zh" or dtct == "zh-cn" or dtct == "zh-tw" or dtct == "ko" or dtct == "jp"):
        return True

    prompt="""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Determine if the language is {lang}. You must return exactly 'yes' if the text is in {lang} or 'no' if it is not.
<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{text}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>Response:"""
    response = call_model(prompt, model_id="meta.llama3-1-8b-instruct-v1:0", max_gen_len=6, temperature=0.1, top_p=0.9)
    print(f"Is target lang? {response}")
    return is_positive(response)

# function to determine if the translations are missaligned
def is_misaligned(text1, text2):
    # if there are no empty string texts, return False
    if not any([not t1.strip() or not t2.strip() for t1, t2 in zip(text1, text2)]):
        return False

    # use zip to align the texts with ->
    text = "\n".join([f"{delimiter1}{t1} -> {t2}{delimiter2}" for t1, t2 in zip(text1, text2)])
    prompt = f"""
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Determine if the translations are misaligned. You must return exactly 'yes' or 'no'.
<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{text}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>Response:"""
    response = call_model(prompt, model_id="meta.llama3-1-8b-instruct-v1:0", max_gen_len=6, temperature=0.8, top_p=0.9)
    print(f"Is misaligned? {response}")
    return is_positive(response)

# EasyNMT API simulation
@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    source_lang = data.get("source_lang", "auto")
    target_lang = data.get("target_lang")
    texts = data.get("text", [])

    if not target_lang or not texts:
        return jsonify({"error": "target_lang and text fields are required"}), 400

    # §

    # join texts to a single string
    texts = "\n".join(texts)

    # translate localy as reference text
    try:
        reference_text = local_translate(texts, source_lang, target_lang)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
    reference_texts = reference_text.split('\n')

    # call the translation function
    try:
        translated_text = translate_call(texts, source_lang, target_lang)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500


    # convert the translated text back to a list
    translated_texts = translated_text.split('\n')

    # filter out empty trimmed texts
    translated_texts = [text for text in translated_texts if text.strip()]

    # remove delimiter from the texts
    original_texts = [text.replace(delimiter1, "") for text in texts.split('\n')]
    original_texts = [text.replace(delimiter2, "") for text in original_texts]

    # align the reference and translated texts
    _, trans = alinhar_listas(reference_texts, translated_texts)

    orig = original_texts
    # if source is chinese, skip alignment
    if source_lang == "chinese":
        trans = translated_texts

    # print each line mapped to the original text and reference text
    for i, (original, reference, translated) in enumerate(zip(orig, reference_texts, trans)):
        # if similarity is less than 0.5, print warn emoji
        sim = similarity(reference, translated)
        if translated.strip() == "":
            print(f"{original} -> {translated}<empty> 🚨, reference: {reference}")
            # replace empty translations with the reference
            trans[i] = reference
        elif sim < 0.5:
            print(f"{original} -> {translated} ⚠️ similarity: {sim}, reference: {reference}")
        else:
            print(f"{original} -> {translated}")

    # if user confirmation is set, wait for user confirmation using an input
    c = os.getenv('USER_CONFIRMATION', False)

    if c:
        # if user input antyhing other than 'y', return an error 500
        if input("\n\n\n\n========> Continue? (y/n): ") != 'y':
            return jsonify({"error": "User cancelled the operation"}), 500
    else:
        # check if the output is translated
        if not is_target_lang(target_lang, "".join(trans)):
            reason = "Output is not translated"
            print(f"ERROR: {reason}, target_lang={target_lang}, source_lang={source_lang}")
            return jsonify({"error": reason}), 500

        # check if the translations are misaligned
        if is_misaligned(orig, trans):
            reason = "Translations are misaligned"
            return jsonify({"error": reason}), 500

    # check if the number of translated texts is the same as the number of input texts
    if len(orig) != len(trans):
        return jsonify({"error": "Number of translated texts does not match the number of input texts"}), 500

    response = {
        "target_lang": target_lang,
        "source_lang": source_lang,
        "detected_langs": [source_lang],  # Assuming detection not handled in this code
        "translated": trans,
        "translation_time": 0  # You can measure actual time if needed
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=24080)
