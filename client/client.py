import asyncio
import os
import sys
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: list[ClientSession] = []
        self.tool_name_to_session: dict[str, ClientSession] = {}
        self.function_declarations = []
        self.exit_stack = AsyncExitStack()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")
        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_servers(self, server_script_paths: list[str]):
        for server_script_path in server_script_paths:
            command = "python" if server_script_path.endswith('.py') else "node"
            server_params = StdioServerParameters(command=command, args=[server_script_path])
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session.append(await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write)))
            await self.session[-1].initialize()
            response = await self.session[-1].list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
            self.function_declarations.extend(convert_mcp_tools_to_gemini(tools))

    async def process_query(self, query: str) -> str:
        # tool/argument guide for Gemini
        tool_guide = "Available tools and their arguments:\n"
        for tool in self.function_declarations:
            for func in tool.function_declarations:
                if hasattr(func.parameters, 'model_dump'):
                    params_dict = func.parameters.model_dump()
                elif hasattr(func.parameters, 'dict'):
                    params_dict = func.parameters.dict()
                else:
                    params_dict = dict(func.parameters)
                params = params_dict.get('properties', {})
                param_list = ', '.join([f"'{k}'" for k in params.keys()])
                tool_guide += f"- {func.name}({param_list})\n"
        
        tool_guide += "\nUse these tools to answer the query. If a tool is needed, call it with the required parameters.\n If an error occurs, provide the error message and a traceback. \n\n"

        user_prompt_content = types.Content(
            role='user',
            parts=[types.Part.from_text(text=tool_guide + query)]
        )
        response = self.genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_prompt_content],
            config=types.GenerateContentConfig(
                tools=self.function_declarations,
            ),
        )
        final_text = []
        for candidate in response.candidates:
            if candidate.content.parts:
                for part in candidate.content.parts:
                    if isinstance(part, types.Part):
                        if part.function_call:
                            function_call_part = part
                            tool_name = function_call_part.function_call.name
                            tool_args = function_call_part.function_call.args
                            print(f"\n[Gemini requested tool call: {tool_name} with args {tool_args}]")
                            try:
                                result = await self.session.call_tool(tool_name, tool_args)
                                function_response = {"result": result.content}
                            except Exception as e:
                                function_response = {"error": str(e)}
                            function_response_part = types.Part.from_function_response(
                                name=tool_name,
                                response=function_response
                            )
                            function_response_content = types.Content(
                                role='tool',
                                parts=[function_response_part]
                            )
                            response = self.genai_client.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=[
                                    user_prompt_content,
                                    function_call_part,
                                    function_response_content,
                                ],
                                config=types.GenerateContentConfig(
                                    tools=self.function_declarations,
                                ),
                            )
                            final_text.append(response.candidates[0].content.parts[0].text)
                        else:
                            final_text.append(part.text)
        return "\n".join(final_text)

    async def chat_loop(self):
        print("\nMCP Client Started! Type 'quit' to exit.")
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
            response = await self.process_query(query)
            print("\n" + response)

    async def cleanup(self):
        await self.exit_stack.aclose()

def clean_schema(schema):
    if isinstance(schema, dict):
        schema.pop("title", None)
        schema.pop("$ref", None)
        schema.pop("$defs", None)
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema

def convert_mcp_tools_to_gemini(mcp_tools):
    gemini_tools = []
    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema)
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )
        gemini_tool = Tool(function_declarations=[function_declaration])
        gemini_tools.append(gemini_tool)
    return gemini_tools

async def main():

    available_servers = [
        "server/terminal_server.py",
        "server/spotify_server.py",
    ]

    client = MCPClient()

    try:
        await client.connect_to_servers(available_servers)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

