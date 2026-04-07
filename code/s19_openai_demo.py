

from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

load_dotenv()  # load environment variables from .env file

# Require OPENAI_API_KEY in environment or .env
if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")):
    print("ERROR: OPENAI_API_KEY not set. Add it to your environment or .env file.")
    sys.exit(1)

client = OpenAI()


def chat_loop():
    print("Interactive chat (type /exit to quit, /reset to restart conversation)")
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    while True:
        try:
            user_text = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break

        if not user_text:
            continue
        if user_text.lower() in ("/exit", "/quit"):
            print("Goodbye.")
            break
        if user_text.lower() == "/reset":
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            print("Conversation reset.")
            continue

        messages.append({"role": "user", "content": user_text})

        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input=messages,
                max_output_tokens=512,
            )

            # Prefer convenience property if available
            text = getattr(response, "output_text", None)
            if not text:
                # Fallback parsing of response.output
                parts = []
                for item in getattr(response, "output", []):
                    for c in item.get("content", []):
                        if c.get("type") in ("output_text", "message"):
                            parts.append(c.get("text", ""))
                text = "\n".join(parts).strip()

            print("Bot:", text)
            messages.append({"role": "assistant", "content": text})
        except Exception as e:
            print("Error calling OpenAI API:", e)


if __name__ == "__main__":
    chat_loop()

