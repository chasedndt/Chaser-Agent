import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'brand/chaser-agent/releases/motion-v1.1.0'

class NativeReleaseTest(unittest.TestCase):
    def test_exact_approved_release(self):
        self.assertEqual(hashlib.sha256((PACK/'manifest.json').read_bytes()).hexdigest(),
            '6f71d10a7eaff17e1ab03835bebe308464ec42a3f977ae22641187d641ad367c')
        m=json.loads((PACK/'manifest.json').read_text())
        self.assertEqual(len(m['assets']),31)
        self.assertEqual(len(m['states']),10)
        self.assertFalse(m['speech_synchronized'])
        for a in m['assets']:
            with self.subTest(file=a['file']):
                b=(PACK/a['file']).read_bytes()
                self.assertEqual(len(b),a['bytes'])
                self.assertEqual(hashlib.sha256(b).hexdigest(),a['sha256'])

    def test_readme_uses_owned_workspaces_and_bounded_claims(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        self.assertNotIn('chaser-agent-runtime-workspace.chaseintech.chatgpt.site',text)
        self.assertIn('https://chaseos.ai/chaser-agent/workspace/#run',text)
        self.assertIn('https://chaseintech.com/projects/chaser-agent/workspace/#workspace',text)
        self.assertIn('speech is a separate study',text)
        self.assertTrue((ROOT/'docs/media/chaser-agent-native-motion-v1.1.gif').is_file())

if __name__=='__main__':unittest.main()
