import contextlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from avatar_workflow.voices import load_catalog, menu_text, prepare_request


class VoiceSelectionTests(unittest.TestCase):
    def test_user_requested_counts_and_no_false_taiwan_labels(self):
        catalog = load_catalog()
        self.assertEqual(Counter(v['group'] for v in catalog['voices']),
                         {'boy':3,'girl':4,'man':8,'woman':8})
        for voice in catalog['voices']:
            if voice['group'] in ('boy','girl') or voice['id'] in ('1603','1604'):
                self.assertFalse(voice['taiwan_explicit'])

    def test_preflight_requires_matching_choice_and_preserves_existing_request(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'config').mkdir()
            (root/'config/round04.json').write_text(json.dumps({'voice':'TTSMaker:1202','script':'大家好！我是阿忠。'}),encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                with self.assertRaises(ValueError):
                    prepare_request(root,'round04','1401')
                self.assertFalse((root/'outputs/round04/voice_request.json').exists())
                request=prepare_request(root,'round04','1202')
                old=request.read_bytes()
                with self.assertRaises(FileExistsError):
                    prepare_request(root,'round04','1202')
                self.assertEqual(request.read_bytes(),old)
            output=stdout.getvalue()
            for voice in load_catalog()['voices']:
                self.assertIn(voice['name'],output)
                self.assertIn(voice['id'],output)
            self.assertEqual(json.loads(old)['status'],'prepared-not-synthesized')


if __name__ == '__main__':
    unittest.main()
