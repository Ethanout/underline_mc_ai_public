"""Archived with embedding.py: the API embedder's image batching."""

import base64
import json
import unittest

from qqbot.embedding import ApiEmbedder, supports_images  # noqa: E402

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
