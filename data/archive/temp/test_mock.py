"""
模拟测试 - 不需要实际的 Minecraft 客户端
测试代码逻辑和 API 调用结构
"""
import asyncio
import json
from pathlib import Path


async def test_without_minecraft():
    """在没有 Minecraft 的情况下测试代码结构"""
    
    print("=" * 60)
    print("Minecraft 命令执行器 - 模拟测试")
    print("=" * 60)
    
    # 测试 1: 检查模块导入
    print("\n[测试 1] 检查模块导入...")
    try:
        from minecraft_executor import MinecraftCommandExecutor
        print("✓ minecraft_executor 模块导入成功")
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return
    
    # 测试 2: 检查类初始化
    print("\n[测试 2] 检查类初始化...")
    try:
        executor = MinecraftCommandExecutor()
        print(f"✓ MinecraftCommandExecutor 初始化成功")
        print(f"  - Mod API: {executor.mod_api_base}")
        print(f"  - SiliconFlow API: {executor.siliconflow_api_base}")
        print(f"  - 截图目录: {executor.screenshot_dir}")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return
    
    # 测试 3: 检查截图目录
    print("\n[测试 3] 检查截图目录...")
    if executor.screenshot_dir.exists():
        print(f"✓ 截图目录已存在: {executor.screenshot_dir}")
    else:
        print(f"✗ 截图目录不存在")
    
    # 测试 4: 检查 API Key
    print("\n[测试 4] 检查 SiliconFlow API Key...")
    if executor.siliconflow_api_key:
        key_preview = executor.siliconflow_api_key[:10] + "..." if len(executor.siliconflow_api_key) > 10 else "***"
        print(f"✓ API Key 已设置: {key_preview}")
    else:
        print(f"⚠ API Key 未设置 (环境变量 SILICONFLOW_API_KEY)")
        print(f"  提示: 设置方式 - $env:SILICONFLOW_API_KEY = 'your-key'")
    
    # 测试 5: 测试 Minecraft API 连接
    print("\n[测试 5] 测试 Minecraft mod API 连接...")
    try:
        import requests
        response = requests.post(
            "http://127.0.0.1:9876/api/cmd",
            json={"method": "ping"},
            timeout=2
        )
        if response.ok:
            print(f"✓ Minecraft mod API 连接成功")
            print(f"  响应: {response.text}")
        else:
            print(f"✗ API 返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"⚠ 无法连接到 Minecraft mod API (端口 9876)")
        print(f"  这是正常的，如果你还没有启动 Minecraft")
        print(f"\n  启动步骤:")
        print(f"    1. 启动 Minecraft 客户端")
        print(f"    2. 确保 minecraft-mod-mcp mod 已加载")
        print(f"    3. 进入单人世界")
        print(f"    4. Open to LAN")
    except Exception as e:
        print(f"✗ 连接测试失败: {e}")
    
    # 测试 6: 模拟数据结构
    print("\n[测试 6] 测试数据结构...")
    mock_result = {
        "success": True,
        "command": "time query daytime",
        "output": "The time is 1000",
        "screenshot": str(executor.screenshot_dir / "test.png")
    }
    print(f"✓ 返回数据结构示例:")
    print(json.dumps(mock_result, indent=2, ensure_ascii=False))
    
    # 测试 7: 检查 MCP 服务器文件
    print("\n[测试 7] 检查 MCP 服务器文件...")
    mcp_server_file = Path(__file__).parent / "minecraft_mcp_server.py"
    if mcp_server_file.exists():
        print(f"✓ MCP 服务器文件存在: {mcp_server_file}")
    else:
        print(f"✗ MCP 服务器文件不存在")
    
    # 测试 8: 检查 opencode.json 配置
    print("\n[测试 8] 检查 opencode.json 配置...")
    opencode_json = Path(__file__).parent / "opencode.json"
    if opencode_json.exists():
        try:
            config = json.loads(opencode_json.read_text(encoding="utf-8"))
            if "mcp" in config and "minecraft-enhanced" in config["mcp"]:
                print(f"✓ opencode.json 配置正确")
                mcp_config = config["mcp"]["minecraft-enhanced"]
                print(f"  - 已启用: {mcp_config.get('enabled')}")
                print(f"  - 命令: {' '.join(mcp_config.get('command', []))}")
            else:
                print(f"⚠ opencode.json 中没有 minecraft-enhanced 配置")
        except Exception as e:
            print(f"✗ 读取配置失败: {e}")
    else:
        print(f"✗ opencode.json 不存在")
    
    print("\n" + "=" * 60)
    print("模拟测试完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 如果 API Key 未设置，请设置环境变量")
    print("2. 启动 Minecraft 并 Open to LAN")
    print("3. 运行 test_minecraft.py 进行完整测试")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_without_minecraft())
