from dotenv import load_dotenv

load_dotenv()

import openai
import os

# Set up the API key and organization (if you're part of one)
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = "org-KHL9Qhf8DDW1g72cO8Kb56vR"  # You can comment this out if you're not part of an organization

def chat_with_gpt(messages):
    """
    Send a list of messages to the GPT chat API and get the model's response.
    
    :param messages: A list of message objects.
    :return: The model's response message.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )
    
    # Extract the assistant's response from the returned chat completions
    assistant_response = response.choices[0].message.content
    
    return assistant_response

def main():
    # The conversation starts with an empty message list
    messages = []

    while True:
        # Get user's input message
        user_message = input("You: ")

        # Add the user's message to the message list
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Get the model's response
        response = chat_with_gpt(messages)
        print(f"Assistant: {response}")

        # Add the model's response to the message list to continue the conversation context
        messages.append({
            "role": "assistant",
            "content": response
        })

if __name__ == "__main__":
    main()
