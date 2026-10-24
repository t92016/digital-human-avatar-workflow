import tempfile
import unittest
from pathlib import Path
from avatar_workflow.hardware import parse_nvidia
from avatar_workflow.recommend import recommend
from avatar_workflow.tools import contained
from avatar_workflow.captions import make_captions
from avatar_workflow.assets import FILES, export_pack, import_pack, files_for_round


def hardware(vram=2048, free=1450, cap=None, driver="456.71", ram=15.92):
    return {"gpus": [{"vendor": "nvidia", "vram_mib": vram, "free_vram_mib": free,
                       "compute_capability": cap, "driver": driver}],
            "ram": {"total_gib": ram, "available_gib": ram * .75}, "project_disk_free_gib": 200}


class HardwareTests(unittest.TestCase):
    def test_legacy_gpu_falls_back(self):
        self.assertEqual(recommend(hardware())["tier"], "lightweight-2d")

    def test_no_gpu_or_unified_memory_is_not_cuda(self):
        hw = {"gpus": [], "apple_unified_memory": True, "ram": {"total_gib": 64}}
        result = recommend(hw, offline=True)
        self.assertEqual(result["tier"], "lightweight-2d")
        self.assertEqual(result["voice"]["primary"], "existing-audio")

    def test_large_gpu_is_only_a_candidate(self):
        result = recommend(hardware(24576, 23000, 8.9, "580.10", 64))
        self.assertEqual(result["tier"], "gpu-video-candidate")
        self.assertFalse(result["runtime_verified"])
        self.assertFalse(result["auto_install_models"])

    def test_busy_gpu_does_not_pass_video_gate(self):
        self.assertNotEqual(recommend(hardware(24576, 1000, 8.9, "580.10", 64))["tier"], "gpu-video-candidate")

    def test_busy_or_unknown_ram_does_not_pass_video_gate(self):
        for available in (2, None):
            hw = hardware(24576, 23000, 8.9, "580.10", 64)
            hw["ram"]["available_gib"] = available
            self.assertNotEqual(recommend(hw)["tier"], "gpu-video-candidate")

    def test_does_not_combine_vram(self):
        hw = hardware(12288, 11000, 8.6, "580.10", 64)
        hw["gpus"] *= 2
        self.assertNotEqual(recommend(hw)["tier"], "gpu-video-candidate")

    def test_missing_capability_does_not_imply_support(self):
        self.assertEqual(recommend(hardware(49152, 45000, None, "580.10", 64))["tier"], "lightweight-2d")

    def test_gpu_csv_fallback(self):
        row = parse_nvidia("GeForce GT 710, 2048, 1458, 456.71", False)[0]
        self.assertEqual(row["vram_mib"], 2048)
        self.assertIsNone(row["compute_capability"])


class SafetyAndTimingTests(unittest.TestCase):
    def test_round02_pack_has_own_allowlist_and_rejects_escape(self):
        names = files_for_round("round02")
        self.assertTrue(all(name.startswith("outputs/round02/") for name in names))
        for round_name in ("../round01", "round02/../../", "round-02", "C:/outside"):
            with self.assertRaises(ValueError):
                files_for_round(round_name)

    def test_asset_pack_roundtrip_and_conflict_before_any_write(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source, target = base / "source", base / "target"
            for name in FILES:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode())
            archive = base / "assets.zip"
            export_pack(source, archive)
            conflict = target / FILES[-1]
            conflict.parent.mkdir(parents=True)
            conflict.write_bytes(b"user-edited")
            with self.assertRaises(FileExistsError):
                import_pack(target, archive)
            self.assertFalse((target / FILES[0]).exists())
            self.assertEqual(conflict.read_bytes(), b"user-edited")
            clean = base / "clean"
            import_pack(clean, archive)
            self.assertTrue(all((clean / n).read_bytes() == n.encode() for n in FILES))

    def test_rejects_zip_escape_on_both_path_conventions(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ["../outside", "/outside", "C:/outside", "a\\..\\outside"]:
                with self.assertRaises(ValueError):
                    contained(Path(folder), name)

    def test_preserves_script_and_uses_actual_word_start(self):
        speech = {"script": "大家好！我是阿忠，", "duration": 8,
                  "boundaries": [{"text": "大家好", "start": 0.2, "duration": 1},
                                 {"text": "我是阿忠", "start": 4, "duration": 2}]}
        captions = make_captions(speech)
        self.assertEqual("".join(c["text"] for c in captions), speech["script"])
        self.assertEqual(captions[1]["start"], 4)
        speech["script"] = "另一段話"
        with self.assertRaises(ValueError):
            make_captions(speech)


if __name__ == "__main__":
    unittest.main()
