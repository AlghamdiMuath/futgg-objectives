"""Arabic catalog coverage and translation batch safety."""

import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from translate_objectives import source_strings, translate_batch


HERE = Path(__file__).parent


class ArabicCatalogTests(unittest.TestCase):
    def test_catalog_is_valid_and_covers_known_objectives(self):
        export = json.loads((HERE / "fc27_interpreted.json").read_text(encoding="utf-8"))
        catalog = json.loads((HERE / "web" / "ar.json").read_text(encoding="utf-8"))
        self.assertIn("Daily Objectives", source_strings(export) & catalog.keys())
        self.assertTrue(all(isinstance(value, str) and value.strip() for value in catalog.values()))

    def test_batch_requires_all_markers_in_order(self):
        malformed = [[['###T001###\nواحد\n###T000###\nاثنان', None]]]
        with patch("translate_objectives.urlopen", return_value=io.BytesIO(json.dumps(malformed).encode())):
            with self.assertRaises(ValueError):
                translate_batch(["one", "two"])


if __name__ == "__main__":
    unittest.main()
