import asyncio
import os
import sys
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from google import genai
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig, Content, Part

def convert_mcp_tools_to_gemini(tools):
    gemini_tools = []
    for tool in tools:
        schema = getattr(tool, "input_schema", {})
        if "title" in schema:
            schema = {k: v for k, v in schema.items() if k != "title"}
        func = FunctionDeclaration(
            name=tool.name,
            description=tool.description or "",
            parameters=schema,
        )
        gemini_tools.append(Tool(function_declarations=[func]))
    return gemini_tools

async def main():
    server_script = "../server/spotify-server.py"
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("Set GEMINI_API_KEY")
        sys.exit(1)
    genai_client = genai.Client(api_key=gemini_key)

    transport = PythonStdioTransport(script_path=server_script, python_cmd=sys.executable, env=os.environ)
    async with Client(transport) as client:
        tools = await client.list_tools()
        gemini_tools = convert_mcp_tools_to_gemini(tools)

        while True:
            query = input("Query: ").strip()
            if query.lower() == "quit":
                break

            user_content = Content(role="user", parts=[Part(text=query)])
            response = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                config=GenerateContentConfig(tools=gemini_tools),
                contents=[user_content],
            )

            reply = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call:
                        name = part.function_call.name
                        args = part.function_call.arguments
                        result = await client.call_tool(name, args)
                        func_part = Part.from_function_response(name=name, response={"result": result.content})
                        tool_content = Content(role="tool", parts=[func_part])
                        follow = genai_client.generate_content(
                            model="gemini-2.5-flash",
                            content_config=GenerateContentConfig(tools=gemini_tools),
                            contents=[user_content, part, tool_content],
                        )
                        reply += follow.candidates[0].content.parts[0].text
                    else:
                        reply += part.text

            print(reply)

asyncio.run(main())