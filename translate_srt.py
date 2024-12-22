import argparse
import requests
import os
import json
import time
from tqdm import tqdm

log_file = "translation_errors.log"

def translate_texts(texts, source_lang, target_lang, server_url, initial_batch_size=20, max_retries=3, retry_delay=5):
    url = f"{server_url}/translate"
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    translated_texts = []
    batch_size = initial_batch_size
    failed_batches = []
    original_failed_size = None
    min_batch_size = 3

    i = 0
    progress_bar = tqdm(total=len(texts), desc="Translating", unit="texts")

    while i < len(texts):
        batch = texts[i:i+batch_size]
        data = {
            "target_lang": target_lang,
            "source_lang": source_lang,
            "text": batch
        }

        success = False
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries} for batch {i // batch_size + 1}, batch size: {batch_size}")
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                translated_texts.extend(response.json().get('translated', []))
                progress_bar.update(len(batch))
                success = True
                break
            else:
                log_failed_request(data, response.status_code, response.text)
                print(f"Error: Translation request failed with status code {response.status_code}. Attempt {attempt+1} of {max_retries}.")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        if not success:
            # If the batch size is the minimum, add empty strings to the translated texts
            if batch_size == min_batch_size:
                print(f"Failed to translate batch after {max_retries} attempts. Adding empty strings to the translated texts.")
                translated_texts.extend([""] * len(batch))
                i += len(batch)
                if failed_batches and len(failed_batches[0]) < len(translated_texts[-len(batch):]):
                    failed_batches[0] = failed_batches[0][len(batch):]
                continue
            # If the batch fails after all retries, halve the batch size
            failed_batches.append(batch)
            if original_failed_size is None:
                original_failed_size = len(batch)
            batch_size = max(min_batch_size, batch_size // 2)
            print(f"Reducing batch size to {batch_size} due to failure.")
        else:
            i += len(batch)

            if failed_batches and len(failed_batches[0]):
                # shrunk the failed batches by the number of translated texts
                failed_batches[0] = failed_batches[0][len(batch):]

            # Check if we should restore the batch size
            if failed_batches and len(failed_batches[0]) < len(translated_texts[-len(batch):]):
                failed_batches.pop(0)
                if not failed_batches:
                    batch_size = initial_batch_size
                    original_failed_size = None
                    print(f"Restoring original batch size to {batch_size}.")

    # if there is any empty translation left, try to translate them again the line only
    for i, text in enumerate(translated_texts):
        if text.strip() == "":
            data = {
                "target_lang": target_lang,
                "source_lang": source_lang,
                "text": [texts[i]]
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                translated_text = response.json().get('translated', [])
                if len(translated_text) > 0:
                    translated_texts[i] = translated_text[0]
                else:
                    log_failed_request(data, response.status_code, response.text)
                    print(f"Error: Translation request failed with status code {response.status_code}.")
                    print(f"Fallback to original text: {texts[i]}")
                    translated_texts[i] = texts[i]
            else:
                log_failed_request(data, response.status_code, response.text)
                print(f"Error: Translation request failed with status code {response.status_code}.")
                # Fallback to original text in case of failure
                print(f"Fallback to original text: {texts[i]}")
                translated_texts[i] = texts[i]
            progress_bar.update(1)


    progress_bar.close()
    return translated_texts



def translate_texts_old(texts, source_lang, target_lang, server_url, batch_size=20, max_retries=3, retry_delay=5):
    url = f"{server_url}/translate"
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    translated_texts = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        data = {
            "target_lang": target_lang,
            "source_lang": source_lang,
            "text": batch
        }
        
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                translated_texts.extend(response.json().get('translated', []))
                break
            else:
                log_failed_request(data, response.status_code, response.text)
                print(f"Error: Translation request failed with status code {response.status_code}. Attempt {attempt+1} of {max_retries}.")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    return translated_texts, Exception(f"Failed to translate batch after {max_retries} attempts.")

    # if there is any empty translation left, try to translate them again the line only
    for i, text in enumerate(translated_texts):
        if text.strip() == "":
            data = {
                "target_lang": target_lang,
                "source_lang": source_lang,
                "text": [texts[i]]
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                translated_text = response.json().get('translated', [])
                if len(translated_text) > 0:
                    translated_texts[i] = translated_text[0]
                else:
                    log_failed_request(data, response.status_code, response.text)
                    print(f"Error: Translation request failed with status code {response.status_code}.")
                    translated_texts[i] = texts[i]
            else:
                log_failed_request(data, response.status_code, response.text)
                print(f"Error: Translation request failed with status code {response.status_code}.")
                # Fallback to original text in case of failure
                translated_texts[i] = texts[i]

    return translated_texts, None

def log_failed_request(request_data, status_code, response_text):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(current_dir, log_file)
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"Status Code: {status_code}\n")
        log.write(f"Response Text: {response_text}\n")
        log.write(f"Request Data: {json.dumps(request_data, ensure_ascii=False)}\n\n")
    print(f"Logged failed request to {log_path}")

def parse_srt(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('\n\n')
    lines = []
    for block in blocks:
        parts = block.split('\n')
        if len(parts) >= 3:
            index = parts[0]
            time_range = parts[1]
            text = ' '.join(parts[2:])
            lines.append((index, time_range, text))
    
    return lines

def write_srt(output_file, translated_lines):
    with open(output_file, 'w', encoding='utf-8') as f:
        for index, time_range, text in translated_lines:
            f.write(f"{index}\n")
            f.write(f"{time_range}\n")
            f.write(f"{text}\n\n")

def translate_srt(input_file, output_file, source_lang, target_lang, server_url, batch_size, max_retries, retry_delay):
    parsed_lines = parse_srt(input_file)
    texts_to_translate = [text for _, _, text in parsed_lines]
    
    translated_texts = translate_texts(texts_to_translate, source_lang, target_lang, server_url, batch_size, max_retries, retry_delay)
    
    translated_lines = [(index, time_range, translated_text) 
                        for (index, time_range, _), translated_text 
                        in zip(parsed_lines, translated_texts)]
    
    write_srt(output_file, translated_lines)

def main():
    parser = argparse.ArgumentParser(description="Translate SRT subtitles using EasyNMT server")
    parser.add_argument('input_file', type=str, help="Path to the input .srt file")
    parser.add_argument('output_file', type=str, help="Path to save the translated .srt file")
    parser.add_argument('source_lang', type=str, help="Source language code (e.g., 'pt')")
    parser.add_argument('target_lang', type=str, help="Target language code (e.g., 'en')")
    parser.add_argument('--server_url', type=str, default='http://localhost:24080', help="EasyNMT server URL")
    parser.add_argument('--batch_size', type=int, default=500, help="Number of lines to send per translation request")
    parser.add_argument('--max_retries', type=int, default=3, help="Number of retries in case of server failure")
    parser.add_argument('--retry_delay', type=int, default=5, help="Delay (in seconds) between retries")

    args = parser.parse_args()
    
    translate_srt(args.input_file, args.output_file, args.source_lang, args.target_lang, args.server_url, args.batch_size, args.max_retries, args.retry_delay)

if __name__ == "__main__":
    main()
