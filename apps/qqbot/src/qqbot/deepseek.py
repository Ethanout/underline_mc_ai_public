"""DeepSeek request details shared by the task agent, collection and images.

Facts measured against the official API (2026-10) live next to the code that
depends on them: thinking is on unless disabled explicitly, ``max_tokens``
covers reasoning too, and images go through the Files API.
"""

from __future__ import annotations

import os
import struct
import zlib
from typing import Any, Callable


def thinking_fields(effort: str | None) -> dict[str, Any]:
    """Request fields for DeepSeek thinking mode.

    Thinking is on by default server-side, so ``none`` must send an explicit
    disabled flag rather than omit the field; ``reasoning_effort`` only means
    something while thinking is on and is passed through as configured.
    """
    if effort == "none":
        return {"thinking": {"type": "disabled"}}
    return {"thinking": {"type": "enabled"}, "reasoning_effort": effort}


DEFAULT_THINKING_BUDGET = 4000


def token_budget(answer_tokens: int, effort: str | None) -> int:
    """``max_tokens`` for a request whose visible answer should fit ``answer_tokens``.

    Measured on deepseek-flash (2026-10): max_tokens caps reasoning and answer
    together.  A 220 budget was used up by reasoning on a mildly tricky
    question (finish_reason=length, empty content), and even 1500 was not
    always enough.  So the thinking allowance is added on top rather than
    shared with the answer.
    """
    if effort == "none":
        return answer_tokens
    try:
        extra = int(os.environ.get("QQBOT_THINKING_BUDGET", DEFAULT_THINKING_BUDGET))
    except ValueError:
        extra = DEFAULT_THINKING_BUDGET
    return answer_tokens + max(0, min(60000, extra))


def empty_reason(choice: dict[str, Any]) -> str:
    # max_tokens appears to cap reasoning and answer together, so a small
    # budget can be spent entirely on thinking.
    if choice.get("finish_reason") == "length":
        return "DeepSeek 没有返回正文：思考过程把 token 用完了，调高 QQBOT_THINKING_BUDGET 或降低思考深度"
    return "DeepSeek 没有返回正文"


def probe_png(size: int = 8) -> bytes:
    """A small solid RGB PNG for the image-input probe.

    DeepSeek rejects a 1x1 grayscale PNG as "unsupported image" (measured
    2026-10), which made the probe report no image support at all; an 8x8 RGB
    image is accepted.
    """

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    row = bytes.fromhex("00") + bytes.fromhex("ffffff") * size  # filter byte, white pixels
    return (
        bytes.fromhex("89504e470d0a1a0a")  # PNG signature
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * size))
        + chunk(b"IEND", b"")
    )


def probe_capabilities(
    post: Callable[[dict[str, Any]], dict[str, Any]], upload=None, model=None
) -> dict:
    """Probe optional API features with tiny requests and keep no model output."""
    result = {"tools": False, "images": False, "thinking": False, "errors": {}}
    base = {
        "model": model or os.environ.get("QQBOT_MODEL", "deepseek-flash"),
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "1"}],
    }
    for name, extra in (
        (
            "tools",
            {
                "tools": [
                    {
                        "type": "function",
                        "function": {"name": "ping", "parameters": {"type": "object"}},
                    }
                ]
            },
        ),
        ("thinking", thinking_fields("low")),
    ):
        try:
            post({**base, **extra})
        except Exception as exc:
            result["errors"][name] = str(exc)[:200]
            continue
        result[name] = True
    if upload is None:
        result["errors"]["images"] = "上传探测未配置"
        return result
    from .deepseek_files import image_part

    png = probe_png()
    try:
        file_id = upload(png, 3600)
    except Exception as exc:
        result["errors"]["images"] = f"上传图片探测失败：{exc}"
        return result
    try:
        post(
            {
                **base,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "1"}, image_part(file_id)],
                    }
                ],
            }
        )
    except Exception as exc:
        result["errors"]["images"] = f"引用图片探测失败：{exc}"
    else:
        result["images"] = True
    return result
