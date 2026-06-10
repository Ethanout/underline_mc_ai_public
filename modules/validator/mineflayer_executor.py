"""
Minecraft Mineflayer 命令执行器 - 直接读取命令返回值
基于 yuniko-software/minecraft-mcp-server 的思路，使用 Node.js + Mineflayer
"""
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import os


try:
    from ..config import MINEFLAYER_DIR
except ImportError:
    # Keep direct script execution working without assuming a fixed directory depth.
    import sys

    for candidate in Path(__file__).resolve().parents:
        if (candidate / "modules" / "config.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    from modules.config import MINEFLAYER_DIR


class MineflayerCommandExecutor:
    """使用 Mineflayer bot 执行命令并直接获取返回值"""
    
    def __init__(
        self,
        bot_username: str = "CommandBot",
        server_host: str = "localhost",
        server_port: int = 25565,
        node_script_dir: Optional[Path] = None
    ):
        self.bot_username = bot_username
        self.server_host = server_host
        self.server_port = server_port
        self.node_script_dir = node_script_dir or MINEFLAYER_DIR
        self.node_script_dir.mkdir(exist_ok=True)
        self.bot_process: Optional[subprocess.Popen] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.response_queue: asyncio.Queue = asyncio.Queue()
        
    def _ensure_bot_script(self):
        """确保 Node.js bot 脚本存在"""
        package_json = self.node_script_dir / "package.json"
        bot_script = self.node_script_dir / "bot.js"
        
        # 创建 package.json
        if not package_json.exists():
            package_json.write_text(json.dumps({
                "name": "minecraft-command-bot",
                "version": "1.0.0",
                "type": "module",
                "dependencies": {
                    "mineflayer": "^4.20.1"
                }
            }, indent=2), encoding='utf-8')
        
        # 创建 bot.js
        if not bot_script.exists() or bot_script.stat().st_size == 0:
            bot_script.write_text("""
import mineflayer from 'mineflayer';
import readline from 'readline';

// 强制 stdout 立即刷新（解决管道缓冲问题）
process.stdout.setDefaultEncoding('utf8');
const originalLog = console.log;
console.log = (...args) => {
  originalLog(...args);
  process.stdout.write('');  // 触发刷新
};

const bot = mineflayer.createBot({
  host: process.env.MC_HOST || 'localhost',
  port: parseInt(process.env.MC_PORT || '25565'),
  username: process.env.MC_USERNAME || 'CommandBot',
  version: false, // 自动检测版本
});

// 等待命令响应的 Promise
let currentCommandResolver = null;
let commandTimeout = null;

bot.once('spawn', () => {
  console.log(JSON.stringify({
    type: 'ready',
    username: bot.username,
    position: bot.entity.position,
  }));
});

bot.on('error', (err) => {
  console.error(JSON.stringify({
    type: 'error',
    error: err.message,
  }));
});

bot.on('kicked', (reason) => {
  console.error(JSON.stringify({
    type: 'kicked',
    reason: reason,
  }));
  process.exit(1);
});

// 监听所有聊天消息（包括命令反馈）
bot.on('message', (message) => {
  const text = message.toString();
  
  console.log(JSON.stringify({
    type: 'chat',
    message: text,
    time: Date.now(),
  }));
  
  // 如果正在等待命令响应，立即返回
  if (currentCommandResolver) {
    clearTimeout(commandTimeout);
    currentCommandResolver(text);
    currentCommandResolver = null;
  }
});

// 从 stdin 读取命令
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', async (line) => {
  try {
    const data = JSON.parse(line);
    
    if (data.type === 'command') {
      // 执行命令并等待响应
      const command = data.command.startsWith('/') ? data.command : '/' + data.command;
      const waitMs = data.wait_ms || 1000;
      
      // 设置响应监听器
      const responsePromise = new Promise((resolve) => {
        currentCommandResolver = resolve;
        commandTimeout = setTimeout(() => {
          if (currentCommandResolver) {
            currentCommandResolver('[超时：无响应]');
            currentCommandResolver = null;
          }
        }, waitMs);
      });
      
      // 发送命令
      bot.chat(command);
      
      // ��待响应
      const response = await responsePromise;
      
      console.log(JSON.stringify({
        type: 'command_response',
        command: data.command,
        output: response,
        success: true,
      }));
    }
    else if (data.type === 'get_position') {
      console.log(JSON.stringify({
        type: 'position',
        position: bot.entity.position,
        yaw: bot.entity.yaw,
        pitch: bot.entity.pitch,
      }));
    }
    else if (data.type === 'get_health') {
      console.log(JSON.stringify({
        type: 'health',
        health: bot.health,
        food: bot.food,
      }));
    }
    else if (data.type === 'ping') {
      console.log(JSON.stringify({
        type: 'pong',
        time: Date.now(),
      }));
    }
  } catch (err) {
    console.error(JSON.stringify({
      type: 'error',
      error: err.message,
    }));
  }
});

bot.on('end', () => {
  process.exit(0);
});
""", encoding='utf-8')
        
        return bot_script
    
    async def start_bot(self) -> bool:
        """启动 Mineflayer bot"""
        try:
            # 确保脚本存在
            bot_script = self._ensure_bot_script()
            
            # 检查并安装依赖
            package_json = self.node_script_dir / "package.json"
            node_modules = self.node_script_dir / "node_modules"
            
            if not node_modules.exists():
                print("正在安装 Mineflayer 依赖...")
                # Windows 需要使用 shell=True 来找到 npm
                if os.name == 'nt':  # Windows
                    install_process = await asyncio.create_subprocess_shell(
                        "npm install",
                        cwd=str(self.node_script_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    install_process = await asyncio.create_subprocess_exec(
                        "npm", "install",
                        cwd=str(self.node_script_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                await install_process.wait()
                if install_process.returncode != 0:
                    stderr = await install_process.stderr.read()
                    raise RuntimeError(f"npm install 失败: {stderr.decode('utf-8', errors='ignore')}")
            
            # 启动 bot
            env = os.environ.copy()
            env.update({
                "MC_HOST": self.server_host,
                "MC_PORT": str(self.server_port),
                "MC_USERNAME": self.bot_username,
            })
            
            # Windows 需要使用 shell=True 或完整路径
            if os.name == 'nt':  # Windows
                self.bot_process = await asyncio.create_subprocess_shell(
                    f'node "{bot_script}"',
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.node_script_dir),
                    env=env
                )
            else:
                self.bot_process = await asyncio.create_subprocess_exec(
                    "node", str(bot_script),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.node_script_dir),
                    env=env
                )
            
            # 启动输出监听
            self._monitor_task = asyncio.create_task(self._monitor_bot_output())
            
            # 等待 bot 就绪
            for _ in range(30):  # 最多等待 30 秒
                try:
                    msg = await asyncio.wait_for(self.response_queue.get(), timeout=1.0)
                    if msg.get("type") == "ready":
                        print(f"Bot 已连接: {msg}")
                        return True
                except asyncio.TimeoutError:
                    continue
            
            raise RuntimeError("Bot 启动超时")
            
        except Exception as e:
            print(f"启动 bot 失败: {e}")
            return False
    
    async def _monitor_bot_output(self):
        """监听 bot 的输出"""
        if not self.bot_process:
            return
        
        while True:
            try:
                line = await self.bot_process.stdout.readline()
                if not line:
                    break
                
                try:
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    if not line_str:
                        continue
                    data = json.loads(line_str)
                    await self.response_queue.put(data)
                except json.JSONDecodeError:
                    pass
            except Exception as e:
                print(f"监听输出错误: {e}")
                break
    
    async def execute_command_with_output(
        self,
        command: str,
        wait_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        执行命令并直接获取返回值
        
        Args:
            command: 要执行的命令（可以带或不带 /）
            wait_ms: 等待响应的最大时间（毫秒）
        
        Returns:
            {
                "success": bool,
                "command": str,
                "output": str,  # 命令的输出文本
                "error": str    # 如果失败
            }
        """
        if not self.bot_process:
            return {"success": False, "error": "Bot 未启动"}
        
        try:
            # 发送命令请求
            request = {
                "type": "command",
                "command": command,
                "wait_ms": wait_ms
            }
            
            self.bot_process.stdin.write(
                (json.dumps(request) + "\n").encode('utf-8')
            )
            await self.bot_process.stdin.drain()
            
            # 等待响应
            timeout_seconds = (wait_ms / 1000) + 2  # 额外 2 秒缓冲
            response = await asyncio.wait_for(
                self._wait_for_response("command_response"),
                timeout=timeout_seconds
            )
            
            return {
                "success": response.get("success", False),
                "command": response.get("command", command),
                "output": response.get("output", "[无输出]"),
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "command": command,
                "error": "命令执行超时"
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    async def _wait_for_response(self, response_type: str, timeout: float = 10.0) -> Dict[str, Any]:
        """等待特定类型的响应，非匹配消息重新入队"""
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError()
            try:
                msg = await asyncio.wait_for(self.response_queue.get(), timeout=remaining)
            except asyncio.TimeoutError:
                raise
            if msg.get("type") == response_type:
                return msg
            await self.response_queue.put(msg)
            await asyncio.sleep(0.01)
    
    async def get_bot_position(self) -> Dict[str, Any]:
        """获取 bot 位置"""
        if not self.bot_process:
            return {"success": False, "error": "Bot 未启动"}
        
        try:
            request = {"type": "get_position"}
            self.bot_process.stdin.write(
                (json.dumps(request) + "\n").encode('utf-8')
            )
            await self.bot_process.stdin.drain()
            
            response = await asyncio.wait_for(
                self._wait_for_response("position"),
                timeout=5.0
            )
            
            return {"success": True, "data": response}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_bot_health(self) -> Dict[str, Any]:
        """获取 bot 健康状态"""
        if not self.bot_process:
            return {"success": False, "error": "Bot 未启动"}
        
        try:
            request = {"type": "get_health"}
            self.bot_process.stdin.write(
                (json.dumps(request) + "\n").encode('utf-8')
            )
            await self.bot_process.stdin.drain()
            
            response = await asyncio.wait_for(
                self._wait_for_response("health"),
                timeout=5.0
            )
            
            return {"success": True, "data": response}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stop_bot(self):
        """停止 bot"""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self.bot_process:
            self.bot_process.terminate()
            try:
                await asyncio.wait_for(self.bot_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.bot_process.kill()
                await self.bot_process.wait()
            self.bot_process = None


# ============= 测试代码 =============
async def test_mineflayer_executor():
    """测试 Mineflayer 执行器"""
    executor = MineflayerCommandExecutor(
        bot_username="TestBot",
        server_host="localhost",
        server_port=25565
    )
    
    print("=== 启动 Bot ===")
    success = await executor.start_bot()
    if not success:
        print("Bot 启动失败")
        return
    
    print("\n=== 等待 3 秒 ===")
    await asyncio.sleep(3)
    
    print("\n=== 测试 1: 查询游戏时间 ===")
    result = await executor.execute_command_with_output("time query daytime")
    print(f"命令: {result.get('command')}")
    print(f"输出: {result.get('output')}")
    
    print("\n=== 测试 2: 查询在线玩家 ===")
    result = await executor.execute_command_with_output("list")
    print(f"输出: {result.get('output')}")
    
    print("\n=== 测试 3: 获取 Bot 位置 ===")
    result = await executor.get_bot_position()
    print(result)
    
    print("\n=== 测试 4: 获取 Bot 健康状态 ===")
    result = await executor.get_bot_health()
    print(result)
    
    print("\n=== 停止 Bot ===")
    await executor.stop_bot()


if __name__ == "__main__":
    asyncio.run(test_mineflayer_executor())
