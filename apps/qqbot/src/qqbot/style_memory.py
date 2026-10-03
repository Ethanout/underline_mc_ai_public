"""Persistent per-group style memory: QQ journal -> embeddings -> ChromaDB.

The bot's weights never change, so the only way it drifts toward sounding like
itself over time is better context.  This module builds the retrieval half of
that loop: every line seen in a group is embedded and stored together with who
said it and whether it was 毯毯's own reply, so later stages can pull the
nearest existing lines for an incoming message and put them in the prompt.

Scope note: this stores *what was said*, not *what should have been said*.  The
frozen anchor examples and the anti-pattern list stay outside this store, and
nothing here decides that a line is good -- read the numbers, then look at the
retrieved lines yourself before trusting them.

No model is loaded and no database is opened at import time; both happen when a
command actually runs.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .embedding import Embedder, build_embedder


MAX_TEXT_CHARS = 500
DEFAULT_BATCH_SIZE = 64
DEFAULT_JOURNAL = "runtime/private/qq_events.jsonl"
DEFAULT_DB = "runtime/private/qq_style"
DEFAULT_PREFIX = "style"


def message_text(event: dict) -> str:
    """Concatenate the text segments of one OneBot message, ignoring the rest."""
    segments = event.get("message")
    if not isinstance(segments, list):
        return ""
    parts: list[str] = []
    for segment in segments:
        if not isinstance(segment, dict) or segment.get("type") != "text":
            continue
        parts.append(str(segment.get("data", {}).get("text", "")))
    return "".join(parts).strip()


def parse_since(value: str) -> float:
    """Parse ``2026-10-04`` or ``2026-10-04 12:30`` into a local timestamp."""
    text = value.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d":
            parsed = parsed.replace(hour=0, minute=0, second=0)
        return parsed.timestamp()
    raise ValueError(f"看不懂的时间：{value}（要 2026-10-04 或 2026-10-04 12:30 这种）")


def reply_target_id(event: dict) -> str:
    """Return the quoted message id when this message is a reply, else ''."""
    segments = event.get("message")
    if not isinstance(segments, list):
        return ""
    for segment in segments:
        if not isinstance(segment, dict) or segment.get("type") != "reply":
            continue
        value = segment.get("data", {}).get("id")
        if value is not None:
            return str(value)
    return ""


def _speaker_name(sender: dict, user_id: str) -> str:
    raw = sender.get("nickname") or sender.get("card") or user_id or "群友"
    return " ".join(str(raw).splitlines()) or "群友"


@dataclass(frozen=True)
class Utterance:
    """One stored line of group chat."""

    event_key: str
    group_id: str
    user_id: str
    speaker: str
    text: str
    ts: float
    is_bot: bool = False
    reply_to_id: str = ""
    reply_to_text: str = ""

    def metadata(self) -> dict[str, str | float | bool]:
        return {
            "group_id": self.group_id,
            "user_id": self.user_id,
            "speaker": self.speaker,
            "ts": self.ts,
            "is_bot": self.is_bot,
            "reply_to_id": self.reply_to_id,
            "reply_to_text": self.reply_to_text,
        }


def read_journal(path: str | Path) -> list[dict]:
    """Read the append-only event journal, skipping unreadable lines."""
    journal = Path(path)
    if not journal.exists():
        return []
    records: list[dict] = []
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and isinstance(record.get("event"), dict):
            records.append(record)
    return records


def collect_utterances(
    records: Iterable[dict],
    max_chars: int = MAX_TEXT_CHARS,
    since: float | None = None,
    bot_since: float | None = None,
) -> list[Utterance]:
    """Turn journal records into storable lines, resolving quoted replies.

    ``since`` drops anything older than that timestamp.  ``bot_since`` drops
    only the bot's own old lines, which is what the reply-trigger fix needs:
    lines recorded before it carry no ``reply`` segment, so they read as bare
    statements with nothing to answer and teach the store the wrong shape.
    """
    records = list(records)
    bot_ids = {"self"}
    for record in records:
        self_id = (record.get("event") or {}).get("self_id")
        if self_id is not None:
            bot_ids.add(str(self_id))

    texts_by_id: dict[str, str] = {}
    for record in records:
        event = record.get("event") or {}
        message_id = event.get("message_id")
        text = message_text(event)
        if message_id is not None and text:
            texts_by_id[str(message_id)] = text

    utterances: list[Utterance] = []
    for record in records:
        event = record.get("event") or {}
        if event.get("post_type") != "message" or event.get("message_type") != "group":
            continue
        text = message_text(event)
        if not text:
            continue
        event_key = str(record.get("event_key") or event.get("message_id") or "")
        if not event_key:
            continue
        sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
        user_id = str(event.get("user_id", ""))
        is_bot = user_id in bot_ids or str(sender.get("role", "")) == "bot"
        reply_id = reply_target_id(event)
        timestamp = event.get("time") or record.get("received_at") or 0.0
        timestamp = float(timestamp)
        cutoff = bot_since if is_bot else since
        if cutoff is not None and timestamp < cutoff:
            continue
        utterances.append(
            Utterance(
                event_key=event_key,
                group_id=str(event.get("group_id", "")),
                user_id=user_id,
                speaker="毯毯" if is_bot else _speaker_name(sender, user_id),
                text=text[:max_chars],
                ts=timestamp,
                is_bot=is_bot,
                reply_to_id=reply_id,
                reply_to_text=texts_by_id.get(reply_id, ""),
            )
        )
    return utterances


def collection_name(prefix: str, group_id: str) -> str:
    """Build a Chroma-safe collection name: 3+ chars of [a-zA-Z0-9._-]."""
    safe = "".join(char if (char.isalnum() or char in "._-") else "_" for char in str(group_id))
    safe = safe.strip("._-") or "unknown"
    return f"{prefix}_{safe}"[:512]


class StyleMemory:
    """Per-group ChromaDB collections of embedded chat lines."""

    def __init__(self, path: str | Path, embedder: Embedder, prefix: str = DEFAULT_PREFIX) -> None:
        self.path = str(path)
        self.embedder = embedder
        self.prefix = prefix
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import chromadb

            Path(self.path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.path)
        return self._client

    def collection(self, group_id: str):
        return self.client.get_or_create_collection(
            name=collection_name(self.prefix, group_id),
            metadata={"hnsw:space": "cosine"},
        )

    def close(self) -> None:
        """Drop the client so Windows releases the sqlite file handle."""
        self._client = None

    def __enter__(self) -> "StyleMemory":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def add(self, utterances: Sequence[Utterance], batch_size: int = DEFAULT_BATCH_SIZE) -> int:
        """Embed and upsert lines.  Re-running over the same journal is safe."""
        by_group: dict[str, list[Utterance]] = {}
        for utterance in utterances:
            by_group.setdefault(utterance.group_id, []).append(utterance)
        stored = 0
        for group_id, items in by_group.items():
            collection = self.collection(group_id)
            for start in range(0, len(items), batch_size):
                chunk = items[start : start + batch_size]
                vectors = self.embedder.encode([item.text for item in chunk])
                collection.upsert(
                    ids=[item.event_key for item in chunk],
                    embeddings=vectors,
                    documents=[item.text for item in chunk],
                    metadatas=[item.metadata() for item in chunk],
                )
                stored += len(chunk)
        return stored

    def groups(self) -> list[str]:
        """Return the group ids that have a collection, newest-agnostic order."""
        names = []
        for item in self.client.list_collections():
            name = item if isinstance(item, str) else getattr(item, "name", "")
            if name.startswith(f"{self.prefix}_"):
                names.append(name[len(self.prefix) + 1 :])
        return sorted(names)

    def stats(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.client.list_collections():
            name = item if isinstance(item, str) else getattr(item, "name", "")
            if not name.startswith(f"{self.prefix}_"):
                continue
            collection = self.client.get_collection(name)
            counts[name[len(self.prefix) + 1 :]] = collection.count()
        return counts

    def search(
        self,
        text: str,
        group_id: str,
        k: int = 5,
        is_bot: bool | None = None,
    ) -> list[dict]:
        """Return the k nearest stored lines, with cosine score and metadata."""
        collection = self.collection(group_id)
        if collection.count() == 0:
            return []
        vector = self.embedder.encode([text])[0]
        where = {"is_bot": is_bot} if is_bot is not None else None
        result = collection.query(
            query_embeddings=[vector],
            n_results=min(k, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        hits: list[dict] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            hits.append(
                {
                    "text": document,
                    "score": 1.0 - float(distance),
                    "speaker": metadata.get("speaker", ""),
                    "is_bot": bool(metadata.get("is_bot", False)),
                    "ts": metadata.get("ts", 0.0),
                    "reply_to_text": metadata.get("reply_to_text", ""),
                }
            )
        return hits


def _force_utf8_stdout() -> None:
    """Windows consoles default to GBK and would mangle the Chinese output."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="把 QQ 群消息写进风格记忆库，并按需检索")
    parser.add_argument("--journal", default=os.environ.get("QQBOT_EVENT_LOG", DEFAULT_JOURNAL))
    parser.add_argument("--db", default=os.environ.get("QQBOT_STYLE_DB", DEFAULT_DB))
    parser.add_argument("--backend", default=None, choices=["local", "api"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--device", default=None, help="本地后端的设备，默认 cpu")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--since", default=None, help="只收这个时间之后的记录，如 2026-10-04")
    parser.add_argument(
        "--bot-since",
        default=None,
        help="只对毯毯自己的话生效的时间下限；修好引用之前的旧回复没有 reply 段，默认不收",
    )
    parser.add_argument("--stats", action="store_true", help="只显示库里的条数")
    parser.add_argument("--query", default=None, help="检索一句话，看看库里最相近的记录")
    parser.add_argument("--group", default=None, help="检索用的群号，省略时用库里唯一的群")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--bot-only", action="store_true", help="只检索毯毯自己说过的话")
    parser.add_argument("--human-only", action="store_true", help="只检索群友说过的话")
    args = parser.parse_args(argv)

    _force_utf8_stdout()
    try:
        since = parse_since(args.since) if args.since else None
        bot_since = parse_since(args.bot_since) if args.bot_since else None
    except ValueError as exc:
        print(exc)
        return 2
    # Read and filter the journal *before* building an embedder.  Building one
    # is the expensive half -- a model download on the local backend, a live
    # HTTP client on the api one -- and an absent or fully-filtered journal is
    # the common case when someone is still setting the thing up.  Reporting
    # "没有可写入的消息" should not cost a download first.
    pending: list[Utterance] = []
    if not args.stats and not args.query:
        records = read_journal(args.journal)
        pending = collect_utterances(records, since=since, bot_since=bot_since)
        if not pending:
            print(f"没有可写入的消息，检查 {args.journal}")
            return 1

    embedder = build_embedder(backend=args.backend, model=args.model, device=args.device)
    memory = StyleMemory(args.db, embedder, prefix=args.prefix)

    if pending:
        print(f"后端：{embedder.name}")
        stored = memory.add(pending, batch_size=args.batch_size)
        bot_lines = [item for item in pending if item.is_bot]
        groups = sorted({item.group_id for item in pending})
        print(f"写入 {stored} 条，其中毯毯自己的 {len(bot_lines)} 条，涉及群 {len(groups)} 个")
        tethered = sum(1 for item in bot_lines if item.reply_to_id)
        untethered = len(bot_lines) - tethered
        if untethered:
            print(f"  毯毯的话里 {untethered} 条没有引用段（看不出在回什么），{tethered} 条带引用")
            print("  这些多半是修好引用记录之前留下的，用 --bot-since 2026-10-04 之类的时间下限可以剔除")

    if args.stats or not args.query:
        for group_id, count in sorted(memory.stats().items()):
            print(f"  {group_id}: {count} 条")

    if args.query:
        group_id = args.group
        if not group_id:
            known = memory.groups()
            if len(known) != 1:
                print(f"库里有 {len(known)} 个群，请用 --group 指定：{', '.join(known) or '（空）'}")
                return 1
            group_id = known[0]
        is_bot = True if args.bot_only else (False if args.human_only else None)
        hits = memory.search(args.query, group_id, k=args.k, is_bot=is_bot)
        if not hits:
            print("库里还没有可检索的记录")
            return 1
        print(f"「{args.query}」最相近的 {len(hits)} 条：")
        for hit in hits:
            mark = "毯毯" if hit["is_bot"] else hit["speaker"]
            print(f"  {hit['score']:.3f}  {mark}：{hit['text']}")
            if hit["reply_to_text"]:
                print(f"         └ 回的是：{hit['reply_to_text'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
