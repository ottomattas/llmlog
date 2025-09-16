def generate_completion(provider: str, prompt: str, **kwargs) -> str:
    """
    Generate a completion using the specified provider.

    Args:
        provider (str): The provider name, e.g., 'anthropic' or 'openai'.
        prompt (str): The prompt text to complete.
        **kwargs: Additional arguments to pass to the provider-specific generate_completion function (such as max_tokens).

    Returns:
        str: The generated completion text.

    Raises:
        NotImplementedError: If the specified provider is not implemented.
        ValueError: If the provider is unknown.
    """
    provider = provider.lower()
    if provider == "anthropic":
        from .anthropic_client import generate_completion as anthropic_generate_completion
        return anthropic_generate_completion(prompt, **kwargs)
    elif provider == "openai":
        raise NotImplementedError("OpenAI provider is not implemented yet")
    else:
        raise ValueError(f"Unknown provider: {provider}")


if __name__ == "__main__":
    # Test the provider manager using a sample prompt for Anthropics.
    test_prompt = "What is the future of AI in simple terms?"
    print("Using Anthropics provider:")
    try:
        response = generate_completion("anthropic", test_prompt, max_tokens=150)
        print("Prompt:", test_prompt)
        print("Response:", response)
    except Exception as e:
        print("Error:", e) 