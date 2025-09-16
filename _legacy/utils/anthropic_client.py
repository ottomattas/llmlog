# utils/anthropic_client.py

import json
import anthropic


def create_anthropic_client():
    """
    Creates and returns an Anthropic API client using the API key from secrets.json.

    Raises:
        ValueError: If the secrets.json file cannot be loaded or the 'anthropic_api_key' is not set.
    """
    try:
        with open("secrets.json", "r") as f:
            secrets = json.load(f)
    except Exception as e:
        raise ValueError(f"Could not load secrets.json file: {e}")

    api_key = secrets.get("anthropic_api_key")
    if not api_key:
        raise ValueError("Anthropic API key is not set in secrets.json. Please set the 'anthropic_api_key' property.")

    return anthropic.Anthropic(api_key=api_key)


def generate_completion(prompt: str, max_tokens: int = 100, model: str = "claude-3-5-haiku-latest") -> str:
    """
    Generate a completion using the Anthropic API.

    Args:
        prompt (str): The prompt text to complete.
        max_tokens (int): Maximum tokens to generate (default: 100).
        model (str): The model to use (default: 'claude-3-5-haiku-latest').

    Returns:
        str: The generated completion text.

    Raises:
        RuntimeError: If there is an error during the API request.
    """
    client = create_anthropic_client()
    try:
        # Format the message as per latest Claude models messaging format
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        raise RuntimeError(f"Error during Anthropic API request: {e}")


if __name__ == "__main__":
    # Test the functionality with a sample prompt.
    test_prompt = "What is the future of AI in simple terms?"
    print("Sending test prompt to Anthropic API...")
    print("Prompt: ", test_prompt)
    try:
        result = generate_completion(test_prompt, 150)
        print("Received response:")
        print(result)
    except Exception as err:
        print("Error:", err)
