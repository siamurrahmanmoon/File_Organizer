"""
tests/test_all_features.py - Comprehensive Unit & Integration Test Suite for All 20 Features.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path

from config import OrganizerConfig, get_default_config
from core.security import SecurityValidator
from core.parser import SmartMediaParser
from core.template_engine import TemplateEngine
from core.duplicate_detector import DuplicateDetector
from core.filter_engine import FilterEngine
from core.quality_control import QualityController
from core.subtitle_manager import SubtitleManager
from core.rollback_manager import RollbackManager
from core.analytics import AnalyticsTracker
from core.profiles_manager import ProfilesManager
from core.engine import AnimeFileOrganizer


class TestSmartMediaParser(unittest.TestCase):
    """Tests Feature 2: Advanced AI & Regex Pattern Recognition."""

    def test_release_group_and_resolution(self):
        filename = "[SubsPlease] Bleach - Thousand-Year Blood War - 01 (1080p) [x265] [7A8B9C0D].mkv"
        info = SmartMediaParser.parse_filename(filename)
        self.assertEqual(info["ReleaseGroup"], "SubsPlease")
        self.assertEqual(info["Resolution"], "1080P")
        self.assertEqual(info["VideoCodec"], "X265")
        self.assertEqual(info["Episode"], "01")
        self.assertEqual(info["CRC32"], "7A8B9C0D")
        self.assertIn("Bleach", info["Title"])

    def test_multi_episode_range(self):
        filename = "One Piece S01E1050-E1051 (2023).mp4"
        info = SmartMediaParser.parse_filename(filename)
        self.assertEqual(info["Season"], "01")
        self.assertEqual(info["Episode"], "1050")
        self.assertEqual(info["Year"], "2023")

    def test_media_type_detection(self):
        ova_info = SmartMediaParser.parse_filename("Attack on Titan OVA 01 (2013).mkv")
        self.assertEqual(ova_info["MediaType"], "OVA")

        movie_info = SmartMediaParser.parse_filename("Demon Slayer Mugen Train Movie (2020).mp4")
        self.assertEqual(movie_info["MediaType"], "Movie")

    def test_fuzzy_similarity(self):
        score = SmartMediaParser.calculate_title_similarity(
            "Jujutsu Kaisen Season 2",
            "Jujutsu Kaisen S02"
        )
        self.assertGreater(score, 0.7)

    def test_user_reported_filenames(self):
        fn1 = "ONE PIECE (1999) [Hindi]-S1E1-480P.mp4"
        info1 = SmartMediaParser.parse_filename(fn1)
        self.assertIn("ONE PIECE", info1["Title"])
        self.assertEqual(info1["Year"], "1999")
        self.assertEqual(info1["Season"], "01")
        self.assertEqual(info1["Episode"], "01")
        self.assertEqual(info1["Resolution"], "480P")

        fn2 = "Easygoing Territory Defense by the Optimistic Lord_ Production Magic Turns a Nameless Village into the Strongest Fortified City (2026) [Hindi]-S1E3-720P.mp4"
        info2 = SmartMediaParser.parse_filename(fn2)
        self.assertIn("Easygoing Territory Defense", info2["Title"])
        self.assertEqual(info2["Year"], "2026")
        self.assertEqual(info2["Season"], "01")
        self.assertEqual(info2["Episode"], "03")
        self.assertEqual(info2["EpisodeRange"], "")
        self.assertEqual(info2["Resolution"], "720P")


class TestTemplateEngine(unittest.TestCase):
    """Tests Feature 5: Custom Naming Template Engine."""

    def test_template_rendering(self):
        context = {
            "Title": "Naruto Shippuden",
            "Year": "2007",
            "Season": "02",
            "Episode": "05",
            "Resolution": "1080p",
            "Codec": "x265",
            "Group": "SubsPlease"
        }
        template = "{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}"
        rendered = TemplateEngine.render(template, context, extension=".mkv")
        self.assertEqual(rendered, "Naruto Shippuden (2007) [1080p] - S02E05.mkv")

    def test_template_validation(self):
        valid, _ = TemplateEngine.validate_template("{Title} ({Year}) - E{Episode}")
        self.assertTrue(valid)

        invalid, _ = TemplateEngine.validate_template("{Title} ({Year} - {UnknownTag}")
        self.assertFalse(invalid)


class TestDuplicateDetector(unittest.TestCase):
    """Tests Feature 3: Intelligent Duplicate Detection & Quarantine."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.quarantine_dir = Path(self.test_dir) / "quarantine"
        self.detector = DuplicateDetector(quarantine_dir=str(self.quarantine_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hashing_and_quarantine(self):
        f1 = Path(self.test_dir) / "video1.mp4"
        f1.write_bytes(b"TEST_VIDEO_PAYLOAD_1234567890" * 100)

        hash1 = DuplicateDetector.calculate_file_hash(f1, algorithm="fast")
        self.assertTrue(hash1.startswith("fast_"))

        q_path = self.detector.quarantine_file(f1)
        self.assertIsNotNone(q_path)
        self.assertTrue(q_path.exists())
        self.assertFalse(f1.exists())


class TestFilterEngine(unittest.TestCase):
    """Tests Feature 4: Multi-Criteria Filtering System."""

    def test_filter_evaluation(self):
        cfg = get_default_config()
        cfg.min_year = 2000
        cfg.max_year = 2025
        cfg.resolution_whitelist = ["1080p", "4K"]

        parsed_valid = {"Year": "2015", "Resolution": "1080P", "Languages": []}
        dummy_file = Path("test.mp4")

        # Mock stat for size
        passes, _ = FilterEngine.evaluate(dummy_file, parsed_valid, cfg)
        self.assertTrue(passes)

        parsed_old = {"Year": "1980", "Resolution": "1080P", "Languages": []}
        passes, reason = FilterEngine.evaluate(dummy_file, parsed_old, cfg)
        self.assertFalse(passes)
        self.assertIn("Year", reason)


class TestQualityControl(unittest.TestCase):
    """Tests Feature 10: Video Quality Control & Incomplete Detection."""

    def test_incomplete_markers(self):
        f_part = Path("Episode_01.mp4.part")
        valid, reason = QualityController.check_file_integrity(f_part)
        self.assertFalse(valid)
        self.assertIn("Incomplete", reason)


class TestSubtitleManager(unittest.TestCase):
    """Tests Feature 8: Subtitle & Sidecar File Management."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_sidecar_discovery_and_sync(self):
        v_path = Path(self.test_dir) / "Anime_Ep1.mp4"
        sub_en = Path(self.test_dir) / "Anime_Ep1.en.srt"
        sub_ja = Path(self.test_dir) / "Anime_Ep1.ja.ass"

        v_path.write_bytes(b"VIDEO")
        sub_en.write_text("1\n00:00 -> 00:05\nHello")
        sub_ja.write_text("1\n00:00 -> 00:05\nKonichiwa")

        subs = SubtitleManager.find_matching_subtitles(v_path)
        self.assertEqual(len(subs), 2)

        out_dir = Path(self.test_dir) / "Organized"
        synced = SubtitleManager.sync_subtitle_organization(subs, "Anime - S01E01", out_dir, move_file=True)
        self.assertEqual(len(synced), 2)
        self.assertTrue((out_dir / "Anime - S01E01.en.srt").exists())
        self.assertTrue((out_dir / "Anime - S01E01.ja.ass").exists())


class TestRollbackManager(unittest.TestCase):
    """Tests Feature 6: SQLite Operation Journal & 1-Click Rollback."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "journal.db"
        self.rollback_mgr = RollbackManager(db_path=str(self.db_path))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_journal_and_rollback(self):
        src_file = Path(self.test_dir) / "source" / "movie.mp4"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_bytes(b"MOVIE_DATA")

        dst_file = Path(self.test_dir) / "target" / "Movie (2024).mp4"
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_file), str(dst_file))

        session_id = self.rollback_mgr.start_session(str(src_file.parent), str(dst_file.parent), 1)
        self.rollback_mgr.log_operation(session_id, str(src_file), str(dst_file), "move")
        self.rollback_mgr.complete_session(session_id)

        self.assertFalse(src_file.exists())
        self.assertTrue(dst_file.exists())

        # Execute rollback
        success, errors, _ = self.rollback_mgr.rollback_session(session_id)
        self.assertEqual(success, 1)
        self.assertEqual(errors, 0)
        self.assertTrue(src_file.exists())
        self.assertFalse(dst_file.exists())


class TestSecurityValidator(unittest.TestCase):
    """Tests Feature 13: Security, Path Traversal & Windows Reserved Names."""

    def test_sanitize_filename(self):
        dirty = 'My Anime: "Special" <OVA> *2024*?.mp4'
        clean = SecurityValidator.sanitize_filename(dirty)
        self.assertNotIn(":", clean)
        self.assertNotIn('"', clean)
        self.assertNotIn("<", clean)
        self.assertNotIn(">", clean)
        self.assertNotIn("*", clean)
        self.assertNotIn("?", clean)

    def test_reserved_names(self):
        clean_con = SecurityValidator.sanitize_filename("CON.mp4")
        self.assertTrue(clean_con.startswith("Safe_CON"))


class TestEndToEndOrganizer(unittest.TestCase):
    """Tests full pipeline integration with real files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "Source_Anime (2022)"
        self.output_dir = Path(self.test_dir) / "Organized_Anime"
        self.source_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy video file >= 2KB
        self.video_file = self.source_dir / "Episode 1.mp4"
        self.video_file.write_bytes(b"DUMMY_VIDEO_DATA" * 200)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hierarchical_year_and_rename(self):
        config = get_default_config()
        config.source_path = str(self.source_dir)
        config.output_path = str(self.output_dir)
        config.dry_run = False
        config.enable_metadata = False  # Test parser & year detection

        organizer = AnimeFileOrganizer(str(self.source_dir), str(self.output_dir), config=config)
        summary = organizer.scan_and_process()

        self.assertEqual(summary["processed"], 1)
        self.assertEqual(summary["errors"], 0)


if __name__ == "__main__":
    unittest.main()
