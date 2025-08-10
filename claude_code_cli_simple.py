#!/usr/bin/env python3
"""
Simple Claude Code CLI client without MCP dependency issues.
Uses basic HTTP requests to interact with Claude API directly.
"""

import asyncio
import sys
import os
from typing import List

from anthropic import Anthropic
from anthropic.types import MessageParam
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env


class SimpleClaudeClient:
    """Simple Claude client without MCP dependencies."""
    
    def __init__(self):
        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key.strip() == "":
            print("⚠️  Error: ANTHROPIC_API_KEY not found or empty in environment.")
            print("   Please add it to your .env file:")
            print("   ANTHROPIC_API_KEY=your_anthropic_api_key_here")
            print("   You can get your API key from: https://console.anthropic.com/")
            sys.exit(1)  # Exit if no API key provided
            
        # Clean up the API key
        api_key = api_key.strip()
        
        # Validate API key format (Anthropic keys start with sk-ant-)
        if not api_key.startswith("sk-ant-") or len(api_key) < 50:
            print("⚠️  Error: API key format appears invalid.")
            print("   Anthropic API keys should start with 'sk-ant-' and be at least 50 characters long.")
            print("   Current key length:", len(api_key))
            print("   Please check your ANTHROPIC_API_KEY value.")
            print("   You can get your API key from: https://console.anthropic.com/")
            sys.exit(1)
            
        self.anthropic = Anthropic(api_key=api_key)
        self.conversation_history: List[MessageParam] = []
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        # Ensure role is valid
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
        
        message: MessageParam = {"role": role, "content": content}  # type: ignore
        self.conversation_history.append(message)
        
        # Keep only last 10 messages to avoid token limits
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    async def process_query(self, query: str) -> str:
        """Process a query using Claude."""
        # Add user query to history
        self.add_to_history("user", query)
        
        try:
            # Call Claude API
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=self.conversation_history,
                system="You are a helpful assistant working on an astrological application called Astroloh. "
                       "You have access to the codebase and can help with development, debugging, and improvements."
            )
            
            # Extract response text
            response_text = ""
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
            
            # Add response to history
            self.add_to_history("assistant", response_text)
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error calling Claude API: {str(e)}"
            print(f"Error: {error_msg}")
            return error_msg
    
    async def chat_loop(self):
        """Run an interactive chat loop."""
        print("\n🤖 Simple Claude Code CLI Started!")
        print("This is a simplified version without MCP dependencies.")
        print("Type your queries or 'quit' to exit.")
        print("Commands:")
        print("  - 'clear' to clear conversation history")
        print("  - 'history' to show conversation history")
        print("  - 'quit' to exit")
        
        while True:
            try:
                query = input("\n💬 Query: ").strip()
                
                if query.lower() == "quit":
                    print("👋 Goodbye!")
                    break
                elif query.lower() == "clear":
                    self.conversation_history = []
                    print("🧹 Conversation history cleared.")
                    continue
                elif query.lower() == "history":
                    print("\n📜 Conversation History:")
                    for i, msg in enumerate(self.conversation_history, 1):
                        role_emoji = "👤" if msg["role"] == "user" else "🤖"
                        # Safely extract content text
                        content = msg["content"]
                        if isinstance(content, str):
                            content_preview = content[:100]
                        else:
                            content_preview = str(content)[:100]
                        print(f"{i}. {role_emoji} {msg['role']}: {content_preview}...")
                    continue
                elif not query:
                    continue
                
                print("\n🤔 Thinking...")
                response = await self.process_query(query)
                print(f"\n🤖 Claude: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")


async def main():
    """Main function."""
    client = SimpleClaudeClient()
    
    # Check if we have a specific query as command line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"🤖 Processing query: {query}")
        response = await client.process_query(query)
        print(f"\n🤖 Response: {response}")
    else:
        # Start interactive chat
        await client.chat_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)