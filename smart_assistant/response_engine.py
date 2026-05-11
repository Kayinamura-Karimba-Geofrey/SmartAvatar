import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file at project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# ─── Configuration ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
MAX_HISTORY        = 10   # Maximum number of conversation turns to keep in memory

SYSTEM_PROMPT = """You are SmartAvatar, a sophisticated and helpful AI voice assistant.
Your goal is to provide clear, engaging, and accurate information.
When giving long or detailed answers, structure them in easy-to-digest paragraphs.
Avoid using complex markdown like tables, but you can use simple natural language.
Keep responses voice-friendly but don't hesitate to be thorough if the topic requires it."""

# ─── Response Engine ──────────────────────────────────────────────────────────

class ResponseEngine:
    def __init__(self):
        """
        Initializes the LLM-powered response engine using OpenRouter.
        OpenRouter is compatible with the OpenAI SDK - just point it to the
        correct base_url and provide your OpenRouter API key.
        """
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Please add it to your .env file at the project root."
            )

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = OPENROUTER_MODEL

        # Conversation history — maintains context across multiple turns
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        print(f"ResponseEngine ready. Model: {self.model}")

    def generate_response(self, user_text: str) -> str:
        """
        Sends the user's message to OpenRouter and returns the assistant's reply.
        Maintains a rolling conversation history for multi-turn dialogue.

        Args:
            user_text: The transcribed text from the user.

        Returns:
            The assistant's text response, ready to be passed to TTS.
        """
        if not user_text or not user_text.strip():
            return "I didn't catch that. Could you please repeat?"

        # Append user message to history
        self.conversation_history.append({"role": "user", "content": user_text})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=256,
            )

            assistant_reply = response.choices[0].message.content.strip()

            # Append assistant reply to history for context retention
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_reply}
            )

            # Trim history to avoid token limit issues (keep system prompt + last N turns)
            if len(self.conversation_history) > MAX_HISTORY + 1:
                self.conversation_history = (
                    [self.conversation_history[0]]          # Always keep system prompt
                    + self.conversation_history[-(MAX_HISTORY):]  # Keep last N messages
                )

            return assistant_reply

        except Exception as e:
            error_msg = str(e)
            print(f"[ResponseEngine] OpenRouter API error: {error_msg}")

            # Friendly fallback so the avatar doesn't crash silently
            return "I'm having trouble connecting right now. Please try again in a moment."

    def reset_conversation(self):
        """Resets conversation history, starting a fresh session."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        print("[ResponseEngine] Conversation history cleared.")


if __name__ == "__main__":
    # Quick test — run: python response_engine.py
    engine = ResponseEngine()
    print(engine.generate_response("Hello! Who are you?"))
    print(engine.generate_response("What can you do?"))
