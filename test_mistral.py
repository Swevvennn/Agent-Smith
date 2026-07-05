import os
from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPEN_ROUTER_API_KEY")

    if not api_key:
        print("ERROR: OPEN_ROUTER_API_KEY not found in .env")
        return
    client = OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_key,
    )

    print("Sending message to Mistral ...")
    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=[
            {
                "role": "user",
                "content": "Write a Python function that multiple two numbers. Keep it short.",
            }
        ],
    )

    text = response.choices[0].message.content
    print("\n=== Mistral response: ===")
    print(text)

    print("\n=== Token usage: ===")
    print("Input tokens (prompt):", response.usage.prompt_tokens)
    print("Output tokens (answer):", response.usage.completion_tokens)


if __name__ == "__main__":
    main()