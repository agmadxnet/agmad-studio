"""Exercise private-reference regressions against disposable tracked documents."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("privacy", ROOT / "scripts/check_doc_privacy.py")
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)
NAME = "\u004d\u0065\u0064\u0068\u0061\u0074"
ARABIC_NAME = "\u0645\u062f\u062d\u062a"

class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)

    def track(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        subprocess.run(["git", "-C", str(self.root), "add", "--", name],
                       check=True, capture_output=True)
        return path

    def test_private_attribution_in_both_languages_is_blocked(self):
        for content in [NAME, NAME.lower(), ARABIC_NAME]:
            with self.subTest(language="private attribution"):
                self.track("docs/nested/guide.md", content)
                with self.assertRaises(ValueError) as error:
                    privacy.check_repository(self.root)
                self.assertNotIn(content, str(error.exception))
                self.assertIn("personal attribution", str(error.exception))

    def test_private_workspace_forms_are_blocked(self):
        for content in ["/Users/" + "tester/Documents/private",
                        "/home/" + "tester/project",
                        "C:\\" + "Users\\tester\\Desktop\\private",
                        "owner " + "workspace",
                        "Documents/" + "Codex/project",
                        "work/" + "export151/VALIDATION.json",
                        "outputs/" + "Agmad_Release_1.5.1_Review"]:
            with self.subTest(category="workspace"):
                self.track("README.md", content)
                with self.assertRaises(ValueError) as error:
                    privacy.check_repository(self.root)
                self.assertNotIn(content, str(error.exception))

    def test_new_tracked_formats_and_directories_are_covered(self):
        for name in ["new/deep/page.html", "new/catalog.json", ".github/new.yml",
                     "journal/new.rst", "video/new.txt", "future/new.markdown"]:
            with self.subTest(name=name):
                self.track(name, NAME)
                with self.assertRaises(ValueError):
                    privacy.check_repository(self.root)
                (self.root / name).write_text("Clean public example\n", encoding="utf-8")
        self.assertEqual(privacy.check_repository(self.root), 6)

    def test_technical_paths_and_legal_notices_are_preserved(self):
        content = ("~/Library/Application Support/Agmad Silent Cutter\n"
                   "%LOCALAPPDATA%\\Agmad Silent Cutter\n/path/to/build\n"
                   "/Users/<username>/Downloads\n/home/runner/work/project\n")
        guide = self.track("README.md", content)
        license_file = self.track("LICENSE", "MIT License\nCopyright 2026 Example Contributors\n")
        original = {p: p.read_bytes() for p in [guide, license_file]}
        self.assertEqual(privacy.check_repository(self.root), 2)
        self.assertEqual({p: p.read_bytes() for p in original}, original)

    def test_missing_unreadable_encoding_and_symlink_docs_fail_closed(self):
        path = self.track("docs/guide.md", "Clean guide\n")
        path.unlink()
        with self.assertRaises(ValueError):
            privacy.check_repository(self.root)
        path.write_bytes(b"\xff\xfe")
        with self.assertRaises(ValueError):
            privacy.check_repository(self.root)
        path.unlink()
        target = self.root / "target"
        target.write_text("Clean target\n", encoding="utf-8")
        path.symlink_to(target)
        with self.assertRaises(ValueError):
            privacy.check_repository(self.root)

    def test_sensitive_filename_is_redacted_from_diagnostics(self):
        self.track("docs/" + NAME + ".md", NAME)
        with self.assertRaises(ValueError) as error:
            privacy.check_repository(self.root)
        self.assertNotIn(NAME, str(error.exception))
        self.assertIn("path redacted", str(error.exception))

    def test_untracked_private_notes_are_not_published_inputs(self):
        self.track("README.md", "Public guide\n")
        (self.root / "untracked.md").write_text(NAME, encoding="utf-8")
        self.assertEqual(privacy.check_repository(self.root), 1)

    def test_cli_fails_without_a_git_document_snapshot(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_doc_privacy.py"), "--root", str(self.root)],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No tracked documentation", result.stderr)

if __name__ == "__main__":
    unittest.main()
