"""LLM Service for AI-powered conversations using Claude API"""
import uuid
from datetime import datetime
from typing import Optional, List, AsyncGenerator
import anthropic

from ..config import get_settings
from ..models.schemas import ChatMessage


class LLMService:
    """Service for AI conversation using Claude API"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.anthropic_api_key
        self.model = self.settings.llm_model
        self._conversations: dict = {}  # In-memory conversation storage

        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def get_system_prompt(self, persona: Optional[str] = None) -> str:
        """Get the system prompt for the AI avatar"""
        base_prompt = """あなたは親しみやすいAIアバターです。
ユーザーとの会話を自然に行い、質問に答えたり、雑談を楽しんだりします。

以下のガイドラインに従ってください：
- 日本語で自然に会話してください
- 簡潔で分かりやすい回答を心がけてください
- 適度に感情を表現してください
- 不適切な内容や有害な情報は提供しないでください
- 回答は音声で読み上げられるため、読みやすい長さにしてください（通常2-3文程度）
"""
        if persona:
            base_prompt += f"\n\n追加の人格設定:\n{persona}"

        return base_prompt

    async def create_conversation(self, persona: Optional[str] = None) -> str:
        """Create a new conversation session"""
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = {
            "messages": [],
            "persona": persona,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return conversation_id

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        persona: Optional[str] = None
    ) -> tuple[str, str, ChatMessage]:
        """
        Generate a response to the user's message.

        Returns:
            Tuple of (conversation_id, response_text, response_message)
        """
        # Create new conversation if needed
        if not conversation_id or conversation_id not in self._conversations:
            conversation_id = await self.create_conversation(persona)

        conv = self._conversations[conversation_id]

        # Add user message to history
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        conv["messages"].append(user_message)

        # Generate response
        if self.client:
            response_text = await self._call_claude(
                message,
                conv["messages"][:-1],  # History without current message
                conv.get("persona")
            )
        else:
            # Demo mode
            response_text = self._generate_demo_response(message)

        # Create response message
        response_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow()
        )
        conv["messages"].append(response_message)
        conv["updated_at"] = datetime.utcnow()

        return conversation_id, response_text, response_message

    async def _call_claude(
        self,
        message: str,
        history: List[ChatMessage],
        persona: Optional[str]
    ) -> str:
        """Call Claude API for response generation"""
        try:
            # Build messages for API
            messages = []
            for msg in history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            messages.append({
                "role": "user",
                "content": message
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.settings.llm_max_tokens,
                system=self.get_system_prompt(persona),
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            print(f"Claude API error: {e}")
            return f"申し訳ありません、エラーが発生しました。もう一度お試しください。"

    async def stream_chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        persona: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response generation for real-time display.

        Yields:
            Response text chunks
        """
        if not conversation_id or conversation_id not in self._conversations:
            conversation_id = await self.create_conversation(persona)

        conv = self._conversations[conversation_id]

        # Add user message
        user_message = ChatMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        conv["messages"].append(user_message)

        full_response = ""

        if self.client:
            try:
                messages = []
                for msg in conv["messages"][-10:]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=self.settings.llm_max_tokens,
                    system=self.get_system_prompt(conv.get("persona")),
                    messages=messages
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        yield text

            except Exception as e:
                error_msg = "申し訳ありません、エラーが発生しました。"
                full_response = error_msg
                yield error_msg
        else:
            # Demo mode - simulate streaming
            demo_response = self._generate_demo_response(message)
            words = demo_response.split()
            for word in words:
                full_response += word + " "
                yield word + " "
                import asyncio
                await asyncio.sleep(0.05)

        # Save response to history
        response_message = ChatMessage(
            role="assistant",
            content=full_response.strip(),
            timestamp=datetime.utcnow()
        )
        conv["messages"].append(response_message)
        conv["updated_at"] = datetime.utcnow()

    def _generate_demo_response(self, message: str) -> str:
        """Generate a demo response when API key is not available"""
        responses = {
            "default": [
                "こんにちは！何かお手伝いできることはありますか？",
                "はい、お話を聞いていますよ。",
                "なるほど、興味深いですね！",
                "それについてもっと教えていただけますか？",
            ],
            "greeting": [
                "こんにちは！今日はどんなお話をしましょうか？",
                "やあ！元気ですか？",
                "いらっしゃい！何でも聞いてくださいね。",
            ],
            "question": [
                "良い質問ですね！考えてみましょう。",
                "その質問は面白いですね。私の考えでは...",
            ]
        }

        import random

        # Simple keyword matching
        message_lower = message.lower()
        if any(word in message_lower for word in ["こんにちは", "はじめまして", "hello", "hi"]):
            return random.choice(responses["greeting"])
        elif "?" in message or "？" in message:
            return random.choice(responses["question"])
        else:
            return random.choice(responses["default"])

    async def get_conversation_history(self, conversation_id: str) -> Optional[dict]:
        """Get conversation history"""
        conv = self._conversations.get(conversation_id)
        if conv:
            return {
                "conversation_id": conversation_id,
                "messages": conv["messages"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"]
            }
        return None

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        if conversation_id in self._conversations:
            self._conversations[conversation_id]["messages"] = []
            self._conversations[conversation_id]["updated_at"] = datetime.utcnow()
            return True
        return False

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def filter_content(self, text: str) -> tuple[bool, str]:
        """
        Filter inappropriate content.

        Returns:
            Tuple of (is_safe, filtered_text_or_reason)
        """
        # Basic content filtering
        blocked_patterns = [
            # Add patterns to block
        ]

        text_lower = text.lower()
        for pattern in blocked_patterns:
            if pattern in text_lower:
                return False, "不適切な内容が検出されました。"

        return True, text
