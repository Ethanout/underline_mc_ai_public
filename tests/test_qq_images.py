import base64
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from workspace_bootstrap import add_workspace_packages

add_workspace_packages()
from qqbot.embedding import ApiEmbedder, supports_images  # noqa: E402
from qqbot.images import ImageCache, ImageRef, data_uri, image_segments, sniff_image  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
GIF = b"GIF89a" + b"\x00" * 32


class FakeCache(ImageCache):
    """Serves canned bytes instead of touching the network."""

    def __init__(self, root, payloads, **kwargs):
        super().__init__(root, **kwargs)
        self.payloads = payloads
        self.downloads = []

    def _download(self, url):
        self.downloads.append(url)
        payload = self.payloads[url]
        if isinstance(payload, Exception):
            raise payload
        if len(payload) > self.max_bytes:
            raise ValueError("too big")
        return payload


class SegmentTests(unittest.TestCase):
    def test_image_segments_keep_http_images_in_order(self):
        event = {"message": [
            {"type": "text", "data": {"text": "看"}},
            {"type": "image", "data": {"file": "A.jpg", "url": "https://x/a", "summary": "[动画表情]", "sub_type": 1}},
            {"type": "image", "data": {"file": "local.jpg", "url": "file:///C:/secret.jpg"}},
            {"type": "image", "data": {"file": "B.png"}},
            {"type": "image", "data": {"file": "C.png", "url": "http://x/c"}},
        ]}
        refs = image_segments(event)
        self.assertEqual([(ref.index, ref.file) for ref in refs], [(0, "A.jpg"), (1, "C.png")])
        self.assertEqual(refs[0].summary, "[动画表情]")
        self.assertEqual(refs[0].sub_type, "1")
        self.assertEqual(image_segments({"message": "not-a-list"}), [])

    def test_cache_key_prefers_file_over_url(self):
        same_file = [ImageRef(0, "https://x/a?rkey=1", file="A.jpg"), ImageRef(0, "https://x/a?rkey=2", file="A.jpg")]
        self.assertEqual(same_file[0].cache_key, same_file[1].cache_key)
        self.assertNotEqual(ImageRef(0, "https://x/1").cache_key, ImageRef(0, "https://x/2").cache_key)

    def test_sniff_image_by_magic_bytes(self):
        self.assertEqual(sniff_image(PNG), ("image/png", ".png"))
        self.assertEqual(sniff_image(GIF)[0], "image/gif")
        self.assertEqual(sniff_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ")[0], "image/webp")
        self.assertIsNone(sniff_image(b"<html>expired</html>"))


class CacheTests(unittest.TestCase):
    def test_fetch_downloads_once_then_serves_cache(self):
        with TemporaryDirectory() as directory:
            cache = FakeCache(directory, {"https://x/a": PNG})
            ref = ImageRef(0, "https://x/a", file="A.jpg")
            first = cache.fetch(ref)
            self.assertEqual(first.suffix, ".png")
            self.assertEqual(first.read_bytes(), PNG)
            self.assertEqual(cache.fetch(ref), first)
            self.assertEqual(cache.downloads, ["https://x/a"])

    def test_fetch_rejects_non_images_and_leaves_nothing_behind(self):
        with TemporaryDirectory() as directory:
            cache = FakeCache(directory, {"https://x/a": b"<html>expired</html>"})
            ref = ImageRef(0, "https://x/a")
            with self.assertRaises(ValueError):
                cache.fetch(ref)
            self.assertIsNone(cache.get(ref))

    def test_fetch_rejects_oversized_payload(self):
        with TemporaryDirectory() as directory:
            cache = FakeCache(directory, {"https://x/a": PNG}, max_bytes=8)
            with self.assertRaises(ValueError):
                cache.fetch(ImageRef(0, "https://x/a"))

    def test_real_download_refuses_non_http_schemes(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ImageCache(directory)._download("file:///C:/Windows/win.ini")

    def test_fetch_event_survives_dead_links(self):
        with TemporaryDirectory() as directory:
            cache = FakeCache(directory, {"https://x/a": OSError("410 Gone"), "https://x/b": GIF})
            event = {"message_id": 7, "message": [
                {"type": "image", "data": {"url": "https://x/a"}},
                {"type": "image", "data": {"url": "https://x/b"}},
            ]}
            self.assertEqual(cache.fetch_event(event), 1)

    def test_data_uri_carries_the_mime_prefix(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "a.bin"
            path.write_bytes(GIF)
            uri = data_uri(path)
            self.assertTrue(uri.startswith("data:image/gif;base64,"))
            self.assertEqual(base64.b64decode(uri.split(",", 1)[1]), GIF)


class ApiEmbedderImageTests(unittest.TestCase):
    def test_encode_images_sends_data_uris_in_batches(self):
        sent = []

        class Recording(ApiEmbedder):
            def _post(self, inputs):
                sent.append(json.loads(json.dumps(inputs)))
                return [[float(len(sent)), 0.0] for _ in inputs]

        with TemporaryDirectory() as directory:
            paths = []
            for index in range(3):
                path = Path(directory) / f"{index}.png"
                path.write_bytes(PNG)
                paths.append(path)
            embedder = Recording(api_key="k", image_batch_size=2)
            self.assertTrue(supports_images(embedder))
            vectors = embedder.encode_images(paths)
        self.assertEqual(len(vectors), 3)
        self.assertEqual([len(batch) for batch in sent], [2, 1])
        self.assertTrue(sent[0][0]["image"].startswith("data:image/png;base64,"))

    def test_text_path_still_sends_plain_strings(self):
        sent = []

        class Recording(ApiEmbedder):
            def _post(self, inputs):
                sent.append(inputs)
                return [[1.0] for _ in inputs]

        Recording(api_key="k").encode(["在吗"])
        self.assertEqual(sent, [["在吗"]])


if __name__ == "__main__":
    unittest.main()
