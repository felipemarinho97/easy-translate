# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
import time
from translate import translate_texts

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    source_lang_code = data.get("source_lang", "auto")
    target_lang_code = data.get("target_lang")
    texts = data.get("text", [])
    start_time = time.time()

    if not target_lang_code or not texts:
        return jsonify({"error": "target_lang and text fields are required"}), 400

    try:
        trans, source_lang, target_lang = translate_texts(texts, source_lang_code, target_lang_code)
    except Exception as e:
        print(f"translate_texts failed: {str(e)}")
        return jsonify({"error": f"translate_texts failed: {str(e)}"}), 500

    response = {
        "target_lang": target_lang,
        "source_lang": source_lang,
        "detected_langs": [source_lang],  # Assuming detection not handled in this code
        "translated": trans,
        "translation_time": time.time() - start_time
    }

    return jsonify(response)

@app.route('/translate', methods=['GET'])
def translate_get():
    text = request.args.getlist("text")
    target_lang_code = request.args.get("target_lang")
    source_lang_code = request.args.get("source_lang", "auto")
    start_time = time.time()

    if not target_lang_code or not text:
        return jsonify({"error": "target_lang and text fields are required"}), 400
    
    try:
        trans, source_lang, target_lang = translate_texts(text, source_lang_code, target_lang_code)
    except Exception as e:
        print(f"translate_texts failed: {str(e)}")
        return jsonify({"error": f"translate_texts failed: {str(e)}"}), 500
    
    response = {
        "target_lang": target_lang,
        "source_lang": source_lang,
        "detected_langs": [source_lang],  # Assuming detection not handled in this code
        "translated": trans,
        "translation_time": time.time() - start_time
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=24080)
