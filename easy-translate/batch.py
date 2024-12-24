import openai
import json
import time
import os

def prepare_batch_file(file_path, requests):
    with open(file_path, 'w') as f:
        for i, request in enumerate(requests):
            batch_entry = {
                "custom_id": f"request-{i+1}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": request
            }
            f.write(json.dumps(batch_entry) + "\n")

def upload_batch_file(client, file_path):
    with open(file_path, 'rb') as f:
        batch_input_file = client.files.create(file=f, purpose="batch")
    return batch_input_file.id

def create_batch(client, batch_input_file_id):
    batch = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "batch job"}
    )
    return batch.id

def check_batch_status(client, batch_id):
    return client.batches.retrieve(batch_id)

def retrieve_batch_results(client, output_file_id):
    file_response = client.files.content(output_file_id)
    with open("batch_output.jsonl", "w") as f:
        f.write(file_response.text)

def call_model_openai_batch(system_prompt, user_prompt, assistant_prompt=None, model_id="gpt-4o-mini", max_tokens=2048, temperature=0.2, top_p=0.9):
    try:
        # Prepare the messages for each conversation in the batch
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if assistant_prompt:
            messages.append({"role": "assistant", "content": assistant_prompt})

        request_body = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        # Prepare the batch input file
        batch_file_path = "batchinput.jsonl"
        prepare_batch_file(batch_file_path, [request_body])  # Add as many requests as needed

        # Initialize OpenAI client
        client = openai.OpenAI(
            api_key = os.getenv("OPENAI_API_KEY")
        )

        # Upload the batch input file
        batch_input_file_id = upload_batch_file(client, batch_file_path)

        # Create the batch
        batch_id = create_batch(client, batch_input_file_id)

        # Poll for batch completion
        status = check_batch_status(client, batch_id)
        print(f"Batch Status: {status}")
        while status.status in ['validating', 'in_progress', 'finalizing']:
            time.sleep(30)
            status = check_batch_status(client, batch_id)

        if status.status == 'completed':
            print("Batch completed successfully.")
            retrieve_batch_results(client, status.output_file_id)
        else:
            print(f"Batch failed with status: {status.status}")

    except Exception as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise e

if __name__ == "__main__":
    system_prompt = "You are a helpful assistant."
    user_prompt = "Hello world!"
    assistant_prompt = None

    call_model_openai_batch(system_prompt, user_prompt, assistant_prompt)
