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

Images are stored too, when the backend can embed them (see
:func:`~qqbot.embedding.supports_images`).  Each image is its own entry with id
``<event_key>#img<n>``, embedded from the picture alone; the text of the same
message rides along as its caption.  A message that is only an image used to be
dropped here, which is exactly the sticker-reply behaviour worth keeping.

No model is loaded and no database is opened at import time; both happen when a
command actually runs.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .embedding import Embedder, build_embedder, supports_images
from .images import DEFAULT_IMAGE_DIR, ImageCache, ImageRef, image_segments

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
            "kind": "text",
            "group_id": self.group_id,
            "user_id": self.user_id,
            "speaker": self.speaker,
            "ts": self.ts,
            "is_bot": self.is_bot,
            "reply_to_id": self.reply_to_id,
            "reply_to_text": self.reply_to_text,
        }


@dataclass(frozen=True)
class ImageUtterance:
    """One image posted in a group, with the text of its message as caption."""

    event_key: str
    source_key: str
    group_id: str
    user_id: str
    speaker: str
    ts: float
    ref: ImageRef
    caption: str = ""
    is_bot: bool = False
    reply_to_id: str = ""

    @property
    def document(self) -> str:
        return self.caption or self.ref.summary or "[图片]"

    def metadata(self, path: str | Path) -> dict[str, str | float | bool]:
        return {
            "kind": "image",
            "group_id": self.group_id,
            "user_id": self.user_id,
            "speaker": self.speaker,
            "ts": self.ts,
            "is_bot": self.is_bot,
            "reply_to_id": self.reply_to_id,
            "reply_to_text": "",
            "source_key": self.source_key,
            "image_path": str(path),
            "image_file": self.ref.file,
            "image_summary": self.ref.summary,
            "image_sub_type": self.ref.sub_type,
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


@dataclass(frozen=True)
class _Message:
    event: dict
    event_key: str
    group_id: str
    user_id: str
    speaker: str
    ts: float
    is_bot: bool
    reply_to_id: str


def _accepted_messages(
    records: list[dict],
    since: float | None,
    bot_since: float | None,
) -> list[_Message]:
    """Group messages that pass the key and time filters, speaker resolved."""
    bot_ids = {"self"}
    for record in records:
        self_id = (record.get("event") or {}).get("self_id")
        if self_id is not None:
            bot_ids.add(str(self_id))

    accepted: list[_Message] = []
    for record in records:
        event = record.get("event") or {}
        if event.get("post_type") != "message" or event.get("message_type") != "group":
            continue
        event_key = str(record.get("event_key") or event.get("message_id") or "")
        if not event_key:
            continue
        sender = event.get("sender") if isinstance(event.get("sender"), dict) else {}
        user_id = str(event.get("user_id", ""))
        is_bot = user_id in bot_ids or str(sender.get("role", "")) == "bot"
        timestamp = float(event.get("time") or record.get("received_at") or 0.0)
        cutoff = bot_since if is_bot else since
        if cutoff is not None and timestamp < cutoff:
            continue
        accepted.append(
            _Message(
                event=event,
                event_key=event_key,
                group_id=str(event.get("group_id", "")),
                user_id=user_id,
                speaker="毯毯" if is_bot else _speaker_name(sender, user_id),
                ts=timestamp,
                is_bot=is_bot,
                reply_to_id=reply_target_id(event),
            )
        )
    return accepted


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
    texts_by_id: dict[tuple[str, str], str] = {}
    for record in records:
        event = record.get("event") or {}
        message_id = event.get("message_id")
        text = message_text(event)
        if message_id is not None and text:
            texts_by_id[(str(event.get("group_id", "")), str(message_id))] = text

    utterances: list[Utterance] = []
    for message in _accepted_messages(records, since, bot_since):
        text = message_text(message.event)
        if not text:
            continue
        utterances.append(
            Utterance(
                event_key=message.event_key,
                group_id=message.group_id,
                user_id=message.user_id,
                speaker=message.speaker,
                text=text[:max_chars],
                ts=message.ts,
                is_bot=message.is_bot,
                reply_to_id=message.reply_to_id,
                reply_to_text=texts_by_id.get((message.group_id, message.reply_to_id), ""),
            )
        )
    return utterances


def collect_images(
    records: Iterable[dict],
    max_chars: int = MAX_TEXT_CHARS,
    since: float | None = None,
    bot_since: float | None = None,
) -> list[ImageUtterance]:
    """Turn journal records into one entry per image, under the same filters."""
    images: list[ImageUtterance] = []
    for message in _accepted_messages(list(records), since, bot_since):
        caption = message_text(message.event)[:max_chars]
        for ref in image_segments(message.event):
            images.append(
                ImageUtterance(
                    event_key=f"{message.event_key}#img{ref.index}",
                    source_key=message.event_key,
                    group_id=message.group_id,
                    user_id=message.user_id,
                    speaker=message.speaker,
                    ts=message.ts,
                    ref=ref,
                    caption=caption,
                    is_bot=message.is_bot,
                    reply_to_id=message.reply_to_id,
                )
            )
    return images


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

    def add(
        self,
        utterances: Sequence[Utterance],
        batch_size: int = DEFAULT_BATCH_SIZE,
        skip_existing: bool = True,
    ) -> int:
        """Embed and upsert lines.  Re-running over the same journal is safe."""
        by_group: dict[str, list[Utterance]] = {}
        for utterance in utterances:
            by_group.setdefault(utterance.group_id, []).append(utterance)
        stored = 0
        for group_id, items in by_group.items():
            collection = self.collection(group_id)
            items = list({item.event_key: item for item in items}.values())
            if skip_existing and items:
                existing = set(
                    collection.get(ids=[item.event_key for item in items]).get("ids", [])
                )
                items = [item for item in items if item.event_key not in existing]
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

    def add_images(
        self,
        items: Sequence[tuple[ImageUtterance, Path]],
        batch_size: int = 8,
        skip_existing: bool = True,
    ) -> tuple[int, list[tuple[ImageUtterance, str]]]:
        """Embed and upsert ``(image, local path)`` pairs.

        Returns ``(stored, rejected)``.  A failed batch is retried one image at
        a time, so a single file the API refuses only costs itself.
        """
        if not supports_images(self.embedder):
            raise ValueError(f"{self.embedder.name} 不支持图片")
        by_group: dict[str, list[tuple[ImageUtterance, Path]]] = {}
        for item in items:
            by_group.setdefault(item[0].group_id, []).append(item)
        stored = 0
        rejected: list[tuple[ImageUtterance, str]] = []
        for group_id, entries in by_group.items():
            collection = self.collection(group_id)
            entries = list({item[0].event_key: item for item in entries}.values())
            if skip_existing and entries:
                existing = set(
                    collection.get(ids=[item[0].event_key for item in entries]).get("ids", [])
                )
                entries = [item for item in entries if item[0].event_key not in existing]
            for start in range(0, len(entries), batch_size):
                chunk = entries[start : start + batch_size]
                try:
                    vectors = self.embedder.encode_images([path for _, path in chunk])
                    pairs = list(zip(chunk, vectors))
                except Exception:  # noqa: BLE001 - narrow down to the offending image
                    pairs = []
                    for entry in chunk:
                        try:
                            pairs.append((entry, self.embedder.encode_images([entry[1]])[0]))
                        except Exception as exc:  # noqa: BLE001
                            rejected.append((entry[0], str(exc)))
                if not pairs:
                    continue
                collection.upsert(
                    ids=[image.event_key for (image, _), _ in pairs],
                    embeddings=[vector for _, vector in pairs],
                    documents=[image.document for (image, _), _ in pairs],
                    metadatas=[image.metadata(path) for (image, path), _ in pairs],
                )
                stored += len(pairs)
        return stored, rejected

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
        kind: str | None = None,
    ) -> list[dict]:
        """Return the k nearest stored entries, with cosine score and metadata.

        ``kind`` is ``"text"`` or ``"image"`` to search only one of them.  Text
        and images share a vector space, so a sentence can find a picture.
        """
        collection = self.collection(group_id)
        if collection.count() == 0:
            return []
        return self._query(collection, self.embedder.encode([text])[0], k, is_bot, kind)

    def search_image(
        self,
        path: str | Path,
        group_id: str,
        k: int = 5,
        is_bot: bool | None = None,
        kind: str | None = None,
    ) -> list[dict]:
        """Like :meth:`search`, with a local image file as the query."""
        if not supports_images(self.embedder):
            raise ValueError(f"{self.embedder.name} 不支持图片")
        collection = self.collection(group_id)
        if collection.count() == 0:
            return []
        return self._query(collection, self.embedder.encode_images([path])[0], k, is_bot, kind)

    @staticmethod
    def _query(
        collection, vector: list[float], k: int, is_bot: bool | None, kind: str | None
    ) -> list[dict]:
        conditions: list[dict] = []
        if is_bot is not None:
            conditions.append({"is_bot": is_bot})
        if kind is not None:
            conditions.append({"kind": kind})
        where = (
            {"$and": conditions} if len(conditions) > 1 else (conditions[0] if conditions else None)
        )
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
        ids = (result.get("ids") or [[""] * len(documents)])[0]
        for item_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            metadata = metadata or {}
            hits.append(
                {
                    "id": item_id,
                    "user_id": metadata.get("user_id", ""),
                    "text": document,
                    "score": 1.0 - float(distance),
                    "kind": metadata.get("kind", "text"),
                    "speaker": metadata.get("speaker", ""),
                    "is_bot": bool(metadata.get("is_bot", False)),
                    "ts": metadata.get("ts", 0.0),
                    "reply_to_text": metadata.get("reply_to_text", ""),
                    "image_path": metadata.get("image_path", ""),
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
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "notes":
        from .store import Store
        from .style_notes import refresh_notes

        parser = argparse.ArgumentParser(description="更新群聊风格笔记")
        parser.add_argument("--group", required=True)
        parser.add_argument("--no-model", action="store_true", help="只统计节奏，不调用模型")
        args = parser.parse_args(argv[1:])
        _force_utf8_stdout()
        key = os.environ.get("DEEPSEEK_API_KEY", "")
        post = None
        if key and not args.no_model:
            from .agent import make_post

            post = make_post(key, timeout=120)
        store = Store(os.environ.get("QQBOT_DB", "runtime/private/qqbot.db"))
        try:
            print(refresh_notes(store, args.group, post))
            error = store.get_state("style_notes_error:" + args.group)
            if error:
                print(f"（模型笔记没用上：{error}）")
        finally:
            store.close()
        return 0
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
    parser.add_argument(
        "--kind", default=None, choices=["text", "image"], help="只检索文字或只检索图片"
    )
    parser.add_argument("--query-image", default=None, help="用一张本地图片去检索")
    parser.add_argument("--no-images", action="store_true", help="这次只收文字，不收图片")
    parser.add_argument(
        "--images-dir",
        default=os.environ.get("QQBOT_IMAGE_DIR", DEFAULT_IMAGE_DIR),
        help="群图片的本地缓存目录，web 收消息时就往这里存",
    )
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
    querying = bool(args.query or args.query_image)
    pending: list[Utterance] = []
    pending_images: list[ImageUtterance] = []
    if not args.stats and not querying:
        records = read_journal(args.journal)
        pending = collect_utterances(records, since=since, bot_since=bot_since)
        if not args.no_images:
            pending_images = collect_images(records, since=since, bot_since=bot_since)
        if not pending and not pending_images:
            print(f"没有可写入的消息，检查 {args.journal}")
            return 1

    embedder = build_embedder(backend=args.backend, model=args.model, device=args.device)
    memory = StyleMemory(args.db, embedder, prefix=args.prefix)

    if pending or pending_images:
        print(f"后端：{embedder.name}")
    if pending:
        records_for_ingest = (
            records
            if not args.no_images
            else [
                {
                    **row,
                    "event": {
                        **row["event"],
                        "message": [
                            s for s in row["event"].get("message", []) if s.get("type") != "image"
                        ],
                    },
                }
                for row in records
            ]
        )
        result = ingest_journal(
            memory, records_for_ingest, ImageCache(args.images_dir), since, bot_since
        )
        stored = result["text"]
        bot_lines = [item for item in pending if item.is_bot]
        groups = sorted({item.group_id for item in pending})
        print(f"写入 {stored} 条，其中毯毯自己的 {len(bot_lines)} 条，涉及群 {len(groups)} 个")
        tethered = sum(1 for item in bot_lines if item.reply_to_id)
        untethered = len(bot_lines) - tethered
        if untethered:
            print(f"  毯毯的话里 {untethered} 条没有引用段（看不出在回什么），{tethered} 条带引用")
            print(
                "  这些多半是修好引用记录之前留下的，用 --bot-since 2026-10-04 之类的时间下限可以剔除"
            )
    if pending_images and not pending:
        ingest_journal(memory, records, ImageCache(args.images_dir), since, bot_since)

    if args.stats or not querying:
        for group_id, count in sorted(memory.stats().items()):
            print(f"  {group_id}: {count} 条")

    if querying:
        group_id = args.group
        if not group_id:
            known = memory.groups()
            if len(known) != 1:
                print(
                    f"库里有 {len(known)} 个群，请用 --group 指定：{', '.join(known) or '（空）'}"
                )
                return 1
            group_id = known[0]
        is_bot = True if args.bot_only else (False if args.human_only else None)
        if args.query_image:
            if not supports_images(embedder):
                print(f"{embedder.name} 不支持图片检索")
                return 1
            label = args.query_image
            hits = memory.search_image(
                args.query_image, group_id, k=args.k, is_bot=is_bot, kind=args.kind
            )
        else:
            label = args.query
            hits = memory.search(args.query, group_id, k=args.k, is_bot=is_bot, kind=args.kind)
        if not hits:
            print("库里还没有可检索的记录")
            return 1
        print(f"「{label}」最相近的 {len(hits)} 条：")
        for hit in hits:
            mark = "毯毯" if hit["is_bot"] else hit["speaker"]
            if hit["kind"] == "image":
                print(f"  {hit['score']:.3f}  {mark}：[图片] {hit['image_path']}  {hit['text']}")
            else:
                print(f"  {hit['score']:.3f}  {mark}：{hit['text']}")
            if hit["reply_to_text"]:
                print(f"         └ 回的是：{hit['reply_to_text'][:60]}")
    return 0


def _ingest_images(
    memory: StyleMemory, images: Sequence[ImageUtterance], cache: ImageCache
) -> None:
    """Resolve each image to a local file, then embed what could be found."""
    if not supports_images(memory.embedder):
        print(
            f"图片 {len(images)} 张跳过：{memory.embedder.name} 不支持图片（要用 api 后端的 VL 模型）"
        )
        return
    located: list[tuple[ImageUtterance, Path]] = []
    missing = 0
    for image in images:
        try:
            located.append((image, cache.fetch(image.ref)))
        except Exception:  # noqa: BLE001 - expired links are the normal case
            missing += 1
    stored, rejected = memory.add_images(located) if located else (0, [])
    print(f"图片写入 {stored} 张")
    if missing:
        print(
            f"  {missing} 张本地没缓存、链接也取不到了（QQ 图片链接会过期，web 开着时收到的才会自动缓存）"
        )
    if rejected:
        print(f"  {len(rejected)} 张被接口拒收，第一条原因：{rejected[0][1][:200]}")


def ingest_journal(memory, records, image_cache, since=None, bot_since=None):
    """Share incremental ingestion between CLI and scheduled service work."""
    records = list(records)
    count = memory.add(
        collect_utterances(records, since=since, bot_since=bot_since), skip_existing=True
    )
    image_count, rejected, missing = 0, [], []
    if supports_images(memory.embedder):
        located = []
        for image in collect_images(records, since=since, bot_since=bot_since):
            path = image_cache.get(image.ref)
            if path is None:
                missing.append(image.event_key)
            else:
                located.append((image, path))
        image_count, rejected = memory.add_images(located, skip_existing=True)
    return {
        "text": count,
        "images": image_count,
        "missing": missing,
        "rejected": [item.event_key for item, _ in rejected],
    }


if __name__ == "__main__":
    raise SystemExit(main())
