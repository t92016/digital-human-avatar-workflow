import unittest
from avatar_workflow.external_speech import reviewed_boundaries


class ExternalTimingTests(unittest.TestCase):
    def test_mismatch_needs_explicit_review_and_preserves_audio_times(self):
        asr={'duration':4,'segments':[{'words':[{'text':'走廊','start':.2,'end':1},
                                                {'text':'滿滿走','start':1.4,'end':3.7}]}]}
        with self.assertRaises(ValueError):
            reviewed_boundaries(asr,'走廊慢慢走。',[])
        rows=reviewed_boundaries(asr,'走廊慢慢走。',[{'word_index':1,'from':'滿滿走','to':'慢慢走'}])
        self.assertEqual(rows[1]['start'],1.4)
        self.assertEqual(rows[1]['duration'],2.3)
        self.assertEqual(asr['segments'][0]['words'][1]['text'],'滿滿走')
        with self.assertRaises(ValueError):
            reviewed_boundaries(asr,'走廊慢慢走。',[{'word_index':1,'from':'過期校稿','to':'慢慢走'}])

    def test_invalid_audio_timing_does_not_become_subtitles(self):
        for start,end in [(-1,1),(2,1),(0,6)]:
            with self.assertRaises(ValueError):
                reviewed_boundaries({'duration':4,'segments':[{'words':[{'text':'好','start':start,'end':end}]}]},'好！',[])


if __name__ == '__main__':
    unittest.main()
