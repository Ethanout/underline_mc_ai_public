from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()

from qqbot.organize import organize  # noqa: E402


class OrganizeExportTests(unittest.TestCase):
    def test_organize_preserves_source_and_copies_media(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "source"
            media_dir = source_dir / "media"
            media_dir.mkdir(parents=True)
            (media_dir / "one.png").write_bytes(b"image")
            source = source_dir / "messages.json"
            source.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"message_id": "1", "content": [{"type": "text", "data": {"text": "beet"}}], "media": []},
                            {"message_id": "2", "content": [{"type": "text", "data": {"text": "beet"}}], "media": [{"type": "image", "file": "media/one.png"}]},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            before = source.read_bytes()
            result = organize(source, root / "organized")

            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(result["message_count"], 2)
            self.assertEqual(result["copied_media_count"], 1)
            self.assertEqual(result["duplicate_count"], 0)
            self.assertEqual(len(list((root / "organized" / "documents").glob("*.md"))), 2)
            self.assertEqual(len(list((root / "organized" / "media").iterdir())), 1)
