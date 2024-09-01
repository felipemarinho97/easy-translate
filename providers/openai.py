import os
from batch import call_model_openai_batch
from openai import OpenAI

# Initialize the OpenAI API
openai_client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

def call_model_openai(system_prompt, user_prompt, assistant_prompt=None, model_id=None, max_tokens=4096, temperature=0.2, top_p=0.9):
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

