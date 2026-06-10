"""
知识库自动验证器
使用 Mineflayer 自动验证知识库中的命令示例
"""
import asyncio
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

from ..config import VALIDATION_DIR
sys.path.insert(0, str(Path(__file__).parent))
from mineflayer_executor import MineflayerCommandExecutor


class KnowledgeValidator:
    """知识库验证器"""
    
    def __init__(
        self,
        knowledge_dir: Path,
        executor: MineflayerCommandExecutor,
        output_dir: Optional[Path] = None
    ):
        self.knowledge_dir = knowledge_dir
        self.executor = executor
        self.output_dir = output_dir or VALIDATION_DIR
        self.entries_dir = knowledge_dir if knowledge_dir.name == "entries" else knowledge_dir / "entries"
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_commands_from_markdown(self, content: str) -> List[Dict[str, Any]]:
        """从 Markdown 文件中提取命令示例"""
        commands = []
        
        # 匹配代码块中的命令
        code_blocks = re.findall(r'```(?:mcfunction|minecraft)?\n(.*?)```', content, re.DOTALL)
        
        for block in code_blocks:
            lines = block.strip().split('\n')
            for line in lines:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 提取命令（去掉前缀 /）
                if line.startswith('/'):
                    line = line[1:]
                
                commands.append({
                    "command": line,
                    "source": "code_block"
                })
        
        # 匹配行内命令（`/command` 或 `/command ...`）
        inline_commands = re.findall(r'`(/[^`]+)`', content)
        for cmd in inline_commands:
            if cmd.startswith('/'):
                cmd = cmd[1:]
            commands.append({
                "command": cmd,
                "source": "inline"
            })
        
        return commands
    
    def parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """解析 YAML frontmatter"""
        if not content.startswith("---"):
            return {}
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        
        meta = {}
        for line in parts[1].strip().split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            
            if val.startswith('"') and val.endswith('"'):
                meta[key] = val[1:-1]
            elif val == "true":
                meta[key] = True
            elif val == "false":
                meta[key] = False
            else:
                meta[key] = val
        
        return meta
    
    async def validate_technique(self, file_path: Path) -> Dict[str, Any]:
        """验证单个技术条目"""
        print(f"\n{'=' * 60}")
        print(f"验证: {file_path.name}")
        print('=' * 60)
        
        content = file_path.read_text(encoding="utf-8")
        meta = self.parse_frontmatter(content)
        commands = self.extract_commands_from_markdown(content)
        
        print(f"标题: {meta.get('title', '未知')}")
        print(f"ID: {meta.get('id', '未知')}")
        print(f"找到 {len(commands)} 个命令")
        
        results = {
            "file": file_path.name,
            "id": meta.get("id"),
            "title": meta.get("title"),
            "timestamp": datetime.now().isoformat(),
            "total_commands": len(commands),
            "commands": []
        }
        
        for i, cmd_info in enumerate(commands, 1):
            command = cmd_info["command"]
            print(f"\n[{i}/{len(commands)}] 测试命令: {command}")
            
            # 执行命令
            result = await self.executor.execute_command_with_output(
                command,
                wait_ms=1500
            )
            
            cmd_result = {
                "command": command,
                "source": cmd_info["source"],
                "success": result["success"],
                "output": result.get("output", ""),
                "error": result.get("error", "")
            }
            
            if result["success"]:
                output = result.get("output", "")
                # 判断命令是否有效（不包含错误信息）
                is_error = any(keyword in output.lower() for keyword in [
                    "unknown", "incorrect", "invalid", "expected", "错误", "未知"
                ])
                
                if is_error:
                    print(f"  ⚠️  命令可能有误: {output}")
                    cmd_result["status"] = "warning"
                else:
                    print(f"  ✅ 输出: {output}")
                    cmd_result["status"] = "success"
            else:
                print(f"  ❌ 失败: {result.get('error')}")
                cmd_result["status"] = "failed"
            
            results["commands"].append(cmd_result)
            
            # 短暂延迟，避免命令过快
            await asyncio.sleep(0.3)
        
        # 统计
        success_count = sum(1 for c in results["commands"] if c["status"] == "success")
        warning_count = sum(1 for c in results["commands"] if c["status"] == "warning")
        failed_count = sum(1 for c in results["commands"] if c["status"] == "failed")
        
        results["summary"] = {
            "success": success_count,
            "warning": warning_count,
            "failed": failed_count,
            "pass_rate": f"{(success_count / len(commands) * 100):.1f}%" if commands else "N/A"
        }
        
        print(f"\n总结: ✅ {success_count} | ⚠️ {warning_count} | ❌ {failed_count}")
        
        return results
    
    async def validate_all(self, pattern: str = "t*.md") -> Dict[str, Any]:
        """验证所有技术条目"""
        entries_dir = self.entries_dir
        if not entries_dir.exists():
            raise FileNotFoundError(f"知识库目录不存在: {entries_dir}")
        
        files = sorted(entries_dir.glob(pattern))
        print(f"\n找到 {len(files)} 个文件待验证")
        
        all_results = {
            "validation_time": datetime.now().isoformat(),
            "total_files": len(files),
            "files": []
        }
        
        for file_path in files:
            try:
                result = await self.validate_technique(file_path)
                all_results["files"].append(result)
            except Exception as e:
                print(f"\n❌ 验证失败: {e}")
                all_results["files"].append({
                    "file": file_path.name,
                    "error": str(e),
                    "status": "error"
                })
        
        # 保存结果
        output_file = self.output_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.write_text(
            json.dumps(all_results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"\n\n{'=' * 60}")
        print("验证完成！")
        print('=' * 60)
        print(f"结果已保存到: {output_file}")
        
        # 打印总体统计
        total_commands = sum(f.get("total_commands", 0) for f in all_results["files"] if "total_commands" in f)
        total_success = sum(f.get("summary", {}).get("success", 0) for f in all_results["files"] if "summary" in f)
        total_warning = sum(f.get("summary", {}).get("warning", 0) for f in all_results["files"] if "summary" in f)
        total_failed = sum(f.get("summary", {}).get("failed", 0) for f in all_results["files"] if "summary" in f)
        
        print(f"\n总体统计:")
        print(f"  文件数: {len(files)}")
        print(f"  命令数: {total_commands}")
        print(f"  成功: {total_success} ({total_success/total_commands*100:.1f}%)" if total_commands else "  成功: 0")
        print(f"  警告: {total_warning}")
        print(f"  失败: {total_failed}")
        
        return all_results


def run(technique_id=None, cancel_event=None):
    from ..config import KNOWLEDGE_DIR, ENTRIES_DIR

    executor = MineflayerCommandExecutor(
        bot_username="ValidatorBot",
        server_host="localhost",
        server_port=25565,
    )

    loop = asyncio.new_event_loop()
    try:
        success = loop.run_until_complete(executor.start_bot())
        if not success:
            return {"ok": False, "cancelled": False, "validated": 0, "error": "Bot failed to start"}

        loop.run_until_complete(asyncio.sleep(3))

        validator = KnowledgeValidator(KNOWLEDGE_DIR, executor)

        validated = 0
        if technique_id:
            file_path = ENTRIES_DIR / f"{technique_id}_*.md"
            matches = list(ENTRIES_DIR.glob(f"{technique_id}_*.md"))
            if not matches:
                return {"ok": False, "cancelled": False, "validated": 0, "error": f"File not found for {technique_id}"}
            loop.run_until_complete(validator.validate_technique(matches[0]))
            validated = 1
        else:
            files = sorted(ENTRIES_DIR.glob("t*.md"))
            for i, fp in enumerate(files):
                if cancel_event and cancel_event.is_set():
                    return {"ok": False, "cancelled": True, "validated": validated}
                try:
                    loop.run_until_complete(validator.validate_technique(fp))
                    validated += 1
                except Exception as e:
                    print(f"Validation error for {fp.name}: {e}")

        return {"ok": True, "cancelled": False, "validated": validated}
    finally:
        loop.run_until_complete(executor.stop_bot())
        loop.close()


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="知识库自动验证工具")
    parser.add_argument("--host", default="localhost", help="Minecraft 服务器地址")
    parser.add_argument("--port", type=int, default=25565, help="Minecraft 服务器端口")
    parser.add_argument("--username", default="ValidatorBot", help="Bot 用户名")
    parser.add_argument("--pattern", default="t*.md", help="文件匹配模式")
    parser.add_argument("--single", help="只验证单个文件（例如：t0001_basic_syntax.md）")

    args = parser.parse_args()

    # 创建执行器
    executor = MineflayerCommandExecutor(
        bot_username=args.username,
        server_host=args.host,
        server_port=args.port
    )

    print("=" * 60)
    print("Minecraft 知识库自动验证器")
    print("=" * 60)

    # 启动 bot
    print(f"\n连接到 {args.host}:{args.port}...")
    success = await executor.start_bot()

    if not success:
        print("\n❌ Bot 启动失败！")
        print("\n请确保：")
        print("  1. Minecraft 服务器已启动")
        print("  2. 服务器允许离线模式或此用户名")
        print("  3. 服务器端口正确")
        return

    print("✅ Bot 已连接")

    # 等待 bot 完全加载
    print("\n等待 Bot 加载...")
    await asyncio.sleep(3)

    # 创建验证器
    from ..config import KNOWLEDGE_DIR
    knowledge_dir = KNOWLEDGE_DIR
    validator = KnowledgeValidator(knowledge_dir, executor)

    try:
        if args.single:
            # 验证单个文件
            file_path = knowledge_dir / "entries" / args.single
            if not file_path.exists():
                print(f"\n❌ 文件不存在: {file_path}")
                return

            await validator.validate_technique(file_path)
        else:
            # 验证所有文件
            await validator.validate_all(pattern=args.pattern)

    finally:
        # 停止 bot
        print("\n\n停止 Bot...")
        await executor.stop_bot()
        print("✅ Bot 已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
    except Exception as e:
        print(f"\n\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
