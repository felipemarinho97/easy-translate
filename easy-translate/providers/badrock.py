import boto3
import json
from botocore.exceptions import ClientError

# Initialize boto3 client for Bedrock
client = boto3.client('bedrock-runtime')  # Adjust region as needed

# Function to call Amazon Bedrock API using boto3
def call_model_bedrock(system_prompt, user_prompt, assistant_prompt, model_id="meta.llama3-1-8b-instruct-v1:0", max_gen_len=2048, temperature=0.2, top_p=0.9):
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
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise
