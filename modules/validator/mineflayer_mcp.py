#!/usr/bin/env python3
"""
Minecraft Mineflayer MCP 服务器
使用 Mineflayer bot 直接读取命令返回值，无需 OCR
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).parent))
from mineflayer_executor import MineflayerCommandExecutor


class MineflayerMCPServer:
    """基于 Mineflayer 的 MCP 服务器"""
    
    def __init__(self):
        self.executor = None
        self.tools = [
            {
                "name": "execute_minecraft_command_with_output",
                "description": "执行 Minecraft 命令并直接获取返回值（通过 Mineflayer bot，无需 OCR）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令，可以带或不带前缀 /"
                        },
                        "wait_ms": {
                            "type": "number",
                            "description": "等待响应的最大时间（毫秒，默认 1000）",
                            "default": 1000
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "get_bot_position",
                "description": "获取 Mineflayer bot 的当前位置",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_bot_health",
                "description": "获取 Mineflayer bot 的健康状态（生命值、饱食度）",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "start_minecraft_bot",
                "description": "启动 Mineflayer bot 连接到 Minecraft 服务器",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Bot 的用户名（默认 CommandBot）",
                            "default": "CommandBot"
                        },
                        "host": {
                            "type": "string",
                            "description": "服务器地址（默认 localhost）",
                            "default": "localhost"
                        },
                        "port": {
                            "type": "number",
                            "description": "服务器端口（默认 25565）",
                            "default": 25565
                        }
                    }
                }
            },
            {
                "name": "stop_minecraft_bot",
                "description": "停止 Mineflayer bot",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: dict) -> Any:
        """处理工具调用"""
        try:
            if tool_name == "start_minecraft_bot":
                username = arguments.get("username", "CommandBot")
                host = arguments.get("host", "localhost")
                port = arguments.get("port", 25565)
                
                self.executor = MineflayerCommandExecutor(
                    bot_username=username,
                    server_host=host,
                    server_port=port
                )
                
                success = await self.executor.start_bot()
                return {
                    "success": success,
                    "message": "Bot 已启动" if success else "Bot 启动失败"
                }
            
            elif tool_name == "stop_minecraft_bot":
                if self.executor:
                    await self.executor.stop_bot()
                    self.executor = None
                    return {"success": True, "message": "Bot 已停止"}
                else:
                    return {"success": False, "error": "Bot 未运行"}
            
            elif tool_name == "execute_minecraft_command_with_output":
                if not self.executor:
                    return {"success": False, "error": "Bot 未启动，请先调用 start_minecraft_bot"}
                
                wait_ms = arguments.get("wait_ms", 1000)
                return await self.executor.execute_command_with_output(
                    arguments["command"],
                    wait_ms=wait_ms
                )
            
            elif tool_name == "get_bot_position":
                if not self.executor:
                    return {"success": False, "error": "Bot 未启动"}
                return await self.executor.get_bot_position()
            
            elif tool_name == "get_bot_health":
                if not self.executor:
                    return {"success": False, "error": "Bot 未启动"}
                return await self.executor.get_bot_health()
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run(self):
        """运行 MCP 服务器（stdio 协议）"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break
                
                request = json.loads(line.strip())
                
                # 处理初始化
                if request.get("method") == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "protocolVersion": "0.1.0",
                            "serverInfo": {
                                "name": "minecraft-mineflayer-mcp-server",
                                "version": "1.0.0"
                            },
                            "capabilities": {
                                "tools": {}
                            }
                        }
                    }
                    print(json.dumps(response), flush=True)
                
                # 列出工具
                elif request.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "tools": self.tools
                        }
                    }
                    print(json.dumps(response), flush=True)
                
                # 调用工具
                elif request.get("method") == "tools/call":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = await self.handle_tool_call(tool_name, arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                                }
                            ]
                        }
                    }
                    print(json.dumps(response), flush=True)
                
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {request.get('method')}"
                        }
                    }
                    print(json.dumps(response), flush=True)
            
            except json.JSONDecodeError:
                continue
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()


async def main():
    server = MineflayerMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
