from __future__ import annotations

import argparse
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()

from qqbot import essence_exporter as exporter  # noqa: E402


def export_args(output: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "endpoint": "http://127.0.0.1:3000",
        "token_env": "TEST_ONEBOT_TOKEN",
        "group_id": "12345",
        "action": "get_essence_msg_list",
        "message_action": "get_msg",
        "root_envelope": False,
        "output": str(output),
        "page_size": 100,
        "max_pages": 1,
        "max_messages": 0,
        "diagnose": False,
        "delay": 0,
        "refresh": False,
        "overwrite": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class EssenceResponseTests(unittest.TestCase):
    def test_fetch_message_detail_fills_metadata_only_essence_item(self) -> None:
        metadata = {"message_id": 7, "content": []}
        detail = {"message": [{"type": "text", "data": {"text": "trick"}}]}
        with patch.object(exporter, "api_call", return_value=detail) as call:
            result = exporter.fetch_message_detail("http://test", "token", metadata, "get_msg", False)
        self.assertEqual(result["message"], detail["message"])
        call.assert_called_once_with("http://test", "token", "get_msg", {"message_id": "7"}, False)

    def test_fetch_message_detail_keeps_existing_content(self) -> None:
        metadata = {"message_id": 7, "content": [{"type": "text", "data": {"text": "ready"}}]}
        with patch.object(exporter, "api_call") as call:
            result = exporter.fetch_message_detail("http://test", "token", metadata, "get_msg", False)
        self.assertIs(result, metadata)
        call.assert_not_called()

    def test_find_list_and_extract_media_preserve_content_segments(self) -> None:
        message = {
            "message_id": 7,
            "content": [
                {"type": "text", "data": {"text": "private text"}},
                {"type": "image", "data": {"url": "https://example.test/image.png"}},
                {"type": "record", "data": {"file_url": "https://example.test/sound.ogg"}},
            ],
        }

        self.assertEqual(exporter.find_list([message]), [message])
        self.assertEqual(
            [(kind, url) for kind, url, _ in exporter.extract_media(message)],
            [("image", "https://example.test/image.png"), ("record", "https://example.test/sound.ogg")],
        )

    def test_diagnostic_mode_does_not_write_private_export(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "private-export"
            with patch.object(exporter, "api_call", return_value=[{"message_id": 1, "content": []}]):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(exporter.export(export_args(output, diagnose=True)), 0)

            self.assertIn("数量=1", stdout.getvalue())
            self.assertFalse(output.exists())


class EssenceIncrementalExportTests(unittest.TestCase):
    def test_incremental_export_deduplicates_and_records_media_failure(self) -> None:
        existing = {"schema_version": 1, "messages": [{"message_id": "existing", "content": []}]}
        new_message = {
            "message_id": "new",
            "content": [
                {"type": "image", "data": {"url": "https://example.test/missing.png"}},
            ],
        }
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "private-export"
            output.mkdir()
            (output / "messages.json").write_text(json.dumps(existing), encoding="utf-8")
            with patch.object(exporter, "api_call", return_value=[new_message]), patch.object(
                exporter, "download", side_effect=OSError("download unavailable")
            ):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(exporter.export(export_args(output)), 0)

            manifest = json.loads((output / "messages.json").read_text(encoding="utf-8"))
            self.assertEqual({item["message_id"] for item in manifest["messages"]}, {"existing", "new"})
            new_record = next(item for item in manifest["messages"] if item["message_id"] == "new")
            self.assertEqual(new_record["media"][0]["type"], "image")
            self.assertIn("error", new_record["media"][0])
            self.assertIn("失败 1 个", stdout.getvalue())
