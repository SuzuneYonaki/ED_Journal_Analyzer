import unittest
from unittest.mock import MagicMock, patch
import json

from app.parser.journal_parser import (
    JournalParser,
    resolve_ggg_variant_name_by_lang,
    get_app_language
)
from app.services.tts_service import tts_service


class TestTTSLanguageAndVariables(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor
        self.parser = JournalParser(db_conn=self.mock_db)
        self.parser.is_live = True
        self.parser.current_star_system = "Synuefe AA-A b1"

    def test_resolve_ggg_variant_name_by_lang(self):
        # Japanese to English
        self.assertEqual(
            resolve_ggg_variant_name_by_lang("スダルスキー・クラス1 ガスジャイアント", lang="en"),
            "Sudarsky Class I Gas Giant"
        )
        self.assertEqual(
            resolve_ggg_variant_name_by_lang("水生生命保有ガスジャイアント", lang="en"),
            "Gas Giant with Water-based Life"
        )
        # English to Japanese
        self.assertEqual(
            resolve_ggg_variant_name_by_lang("Sudarsky Class II Gas Giant", lang="ja"),
            "スダルスキー・クラス2 ガスジャイアント"
        )
        # Key to English and Japanese
        self.assertEqual(
            resolve_ggg_variant_name_by_lang("sudarsky_class_iii", lang="en"),
            "Sudarsky Class III Gas Giant"
        )
        self.assertEqual(
            resolve_ggg_variant_name_by_lang("sudarsky_class_iii", lang="ja"),
            "スダルスキー・クラス3 ガスジャイアント"
        )

    @patch("app.parser.journal_parser.get_app_language", return_value="ja")
    @patch("app.parser.journal_parser.get_high_bio_tts_config")
    @patch("app.services.tts_service.tts_service.enqueue_speak")
    def test_high_bio_alert_ja_variables(self, mock_enqueue, mock_cfg, mock_lang):
        mock_cfg.return_value = {
            "enabled": True,
            "engine": "voicevox",
            "mode": "both",
            "threshold": 40_000_000,
            "threshold_type": "bonus",
            "text": "{body}、生体シグナル{bio_count}件。推定額{value}クレジットです。"
        }
        predictions = [
            {"species_name": "Stratum Tectonicas", "base_value": 19_000_000, "first_discovery_value": 95_000_000},
            {"species_name": "Tubus Soritis", "base_value": 2_000_000, "first_discovery_value": 10_000_000}
        ]

        res = self.parser._check_and_trigger_high_bio_alert(
            sys_addr=12345,
            body_id=3,
            body_name="Synuefe AA-A b1 3 a",
            bio_predictions=predictions,
            bio_signals=2
        )
        self.assertTrue(res)
        mock_enqueue.assert_called_once()
        spoken_text = mock_enqueue.call_args[0][0]
        self.assertIn("Synuefe AA-A b1 3 a", spoken_text)
        self.assertIn("生体シグナル2件", spoken_text)
        self.assertIn("105.0M", spoken_text)

    @patch("app.parser.journal_parser.get_app_language", return_value="en")
    @patch("app.parser.journal_parser.get_high_bio_tts_config")
    @patch("app.services.tts_service.tts_service.enqueue_speak")
    def test_high_bio_alert_en_default_and_variables(self, mock_enqueue, mock_cfg, mock_lang):
        # Default text in Japanese cfg should automatically translate to English default
        mock_cfg.return_value = {
            "enabled": True,
            "engine": "voicevox",
            "mode": "both",
            "threshold": 40_000_000,
            "threshold_type": "bonus",
            "text": "{body}、生体シグナル{bio_count}件。推定額{value}クレジットです。"
        }
        predictions = [
            {"species_name": "Stratum Tectonicas", "base_value": 19_000_000, "first_discovery_value": 95_000_000}
        ]

        res = self.parser._check_and_trigger_high_bio_alert(
            sys_addr=12345,
            body_id=4,
            body_name="Synuefe AA-A b1 4 a",
            bio_predictions=predictions,
            bio_signals=1
        )
        self.assertTrue(res)
        mock_enqueue.assert_called_once()
        spoken_text = mock_enqueue.call_args[0][0]
        # Should be English default: "{body}, {bio_count} biological signals detected. Estimated value {value} credits."
        self.assertEqual(
            spoken_text,
            "Synuefe AA-A b1 4 a, 1 biological signals detected. Estimated value 95.0M credits."
        )

    @patch("app.parser.journal_parser.get_app_language", return_value="en")
    @patch("app.parser.journal_parser.get_high_bio_tts_config")
    @patch("app.services.tts_service.tts_service.enqueue_speak")
    def test_high_bio_alert_en_custom_order(self, mock_enqueue, mock_cfg, mock_lang):
        mock_cfg.return_value = {
            "enabled": True,
            "engine": "voicevox",
            "mode": "both",
            "threshold": 40_000_000,
            "threshold_type": "bonus",
            "text": "{system}: {body} worth {value} with {signals} signals."
        }
        predictions = [
            {"species_name": "Stratum Tectonicas", "base_value": 19_000_000, "first_discovery_value": 95_000_000}
        ]

        res = self.parser._check_and_trigger_high_bio_alert(
            sys_addr=12345,
            body_id=5,
            body_name="Synuefe AA-A b1 5 a",
            bio_predictions=predictions,
            bio_signals=3
        )
        self.assertTrue(res)
        mock_enqueue.assert_called_once()
        spoken_text = mock_enqueue.call_args[0][0]
        self.assertEqual(
            spoken_text,
            "Synuefe AA-A b1: Synuefe AA-A b1 5 a worth 95.0M with 3 signals."
        )

    @patch("app.parser.journal_parser.get_app_language", return_value="en")
    @patch("app.parser.journal_parser.is_ggg_tts_enabled", return_value=True)
    @patch("app.parser.journal_parser.get_ggg_tts_config")
    @patch("app.services.tts_service.tts_service.enqueue_speak")
    def test_ggg_alert_en_and_variant(self, mock_enqueue, mock_cfg, mock_enabled, mock_lang):
        mock_cfg.return_value = {
            "enabled": True,
            "confirmed_enabled": True,
            "engine": "voicevox",
            "mode": "both",
            "confirmed_text": "{body}はグリーンガスジャイアント、目視確認を推奨。種別は、{variant}です。"
        }

        res = self.parser._check_and_trigger_ggg_alert(
            sys_addr=12345,
            body_name="Col 285 Sector AB-C b1 2",
            is_confirmed=True,
            variant_name="スダルスキー・クラス1 ガスジャイアント"
        )
        self.assertTrue(res)
        mock_enqueue.assert_called_once()
        spoken_text = mock_enqueue.call_args[0][0]
        self.assertEqual(
            spoken_text,
            "Col 285 Sector AB-C b1 2 is a Green Gas Giant, visual confirmation recommended. Type is Sudarsky Class I Gas Giant."
        )


if __name__ == "__main__":
    unittest.main()
