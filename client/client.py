import asyncio
import os
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack

from dotenv import load_dotenv
load_dotenv()

# MCP client and server connection
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.subprocess_server import SubprocessServer

# Gemini
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.GEMINI_API_KEY:
            print("Please set the GEMINI_API_KEY environment variable.")
            sys.exit(1)

        self.genai_client = genai.Client(api_key=self.GEMINI_API_KEY)

    async def connect_to_mcp_server(self, server_script_path: str):
        # Launch server via subprocess
        server = SubprocessServer(
            command="python",
            args=[server_script_path],
            env=os.environ,
        )

        # Connect client to server
        self.stdio, self.write = await self.exit_stack.enter_async_context(stdio_client(server))
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        self.function_declarations = convert_mcp_tools_to_gemini(tools)

    async def process_query(self, query: str) -> str:
        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=query)]
        )

        response = self.genai_client.generate_content(
            model="gemini-1.5-flash",
            content_config=GenerateContentConfig(
                max_output_tokens=1000,
                temperature=0.2,
                top_p=0.95,
                tools=self.function_declarations,
            ),
            contents=[user_prompt_content],
        )

        final_text = []

        for candidate in response.candidates:
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if part.function_call:
                        tool_name = part.function_call.name
                        tool_args = part.function_call.arguments
                        print(f"\n🔧 Calling tool: {tool_name} with args: {tool_args}")

                        try:
                            result = await self.session.call_tool(tool_name, tool_args)
                            function_response = {"result": result.content}
                        except Exception as e:
                            function_response = {"error": str(e)}

                        tool_response_part = types.Part.from_function_response(
                            name=tool_name,
                            response=function_response
                        )

                        tool_response_content = types.Content(
                            role="tool",
                            parts=[tool_response_part]
                        )

                        # Step 2: Send tool response back to Gemini
                        follow_up = self.genai_client.generate_content(
                            model="gemini-1.5-flash",
                            content_config=GenerateContentConfig(
                                max_output_tokens=1000,
                                temperature=0.2,
                                top_p=0.95,
                                tools=self.function_declarations,
                            ),
                            contents=[user_prompt_content, part, tool_response_content],
                        )

                        final_text.append(follow_up.candidates[0].content.parts[0].text)
                    else:
                        final_text.append(part.text)

        return "\n".join(final_text)

    async def chat_loop(self):
        print("\n🤖 MCP Client Started. Type 'quit' to exit.")
        while True:
            query = input("\n📝 Query: ").strip()
            if query.lower() == 'quit':
                break
            response = await self.process_query(query)
            print("\n💬 Response:", response)

    async def cleanup(self):
        await self.exit_stack.aclose()

def convert_mcp_tools_to_gemini(mcp_tools):
    gemini_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema)
        func = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters,
        )
        gemini_tools.append(Tool(function_declarations=[func]))
    return gemini_tools

def clean_schema(schema):
    if isinstance(schema, dict):
        schema.pop("title", None)
        if "properties" in schema:
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_mcp_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())