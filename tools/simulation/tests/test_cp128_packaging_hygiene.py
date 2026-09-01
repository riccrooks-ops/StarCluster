import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO / 'tools' / 'checkpoints' / 'prepackage_repository_hygiene.py'
spec = importlib.util.spec_from_file_location('prepackage_repository_hygiene', MODULE_PATH)
hygiene = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hygiene)


class Cp128PackagingHygieneTests(unittest.TestCase):
    def test_large_nested_validation_evidence_is_rejected_but_reference_zip_is_not(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / 'docs' / 'validation' / 'evidence' / 'checkpoint-x'
            refs = root / 'docs' / 'references'
            evidence.mkdir(parents=True)
            refs.mkdir(parents=True)
            # Stored incompressible-sized payload: the guard is about distributed archive bytes.
            payload = b'x' * (hygiene.MAX_VALIDATION_EVIDENCE_ARCHIVE_BYTES + 1)
            with zipfile.ZipFile(evidence / 'too-large.zip', 'w', compression=zipfile.ZIP_STORED) as z:
                z.writestr('raw.bin', payload)
            with zipfile.ZipFile(refs / 'reference.zip', 'w', compression=zipfile.ZIP_STORED) as z:
                z.writestr('reference.bin', payload)
            errors = hygiene.check_repository_hygiene(root)
            self.assertTrue(any('larger than 5 MiB' in e for e in errors))
            self.assertFalse(any('reference.zip' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
