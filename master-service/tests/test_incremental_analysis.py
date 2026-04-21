from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.master_service import analyze_student_profile_incremental


class IncrementalAnalysisTests(unittest.IsolatedAsyncioTestCase):
    async def test_resume_only_change_reuses_existing_coding_and_marksheet(self) -> None:
        with (
            patch("app.services.master_service.call_resume_analyzer", new=AsyncMock(return_value=({"name": "New", "branch": "CSE"}, None))),
            patch("app.services.master_service.call_marksheet_analyzer", new=AsyncMock()) as marksheet_mock,
            patch("app.services.master_service.call_coding_analyzer", new=AsyncMock()) as coding_mock,
            patch("app.services.master_service.upload_resume_to_cloudinary", new=AsyncMock(return_value="https://cdn/new.pdf")),
            patch(
                "app.services.master_service.normalize_master_output",
                side_effect=lambda **kwargs: kwargs,
            ),
        ):
            out = await analyze_student_profile_incremental(
                existing_resume_data={"name": "Old", "branch": "ECE"},
                existing_marksheet_data={"candidate": {"name": "Old Candidate"}},
                existing_coding_data={"github": {"repos": 10}, "leetcode": {"total_solved": 300}, "coding_persona": "advanced"},
                resume_file=b"resume",
                resume_filename="resume.pdf",
                resume_content_type="application/pdf",
                marksheet_file=None,
                marksheet_filename=None,
                marksheet_content_type=None,
                resume_changed=True,
                marksheet_changed=False,
                coding_changed=False,
                branch="AIML",
                github="gh",
                leetcode="lc",
                existing_resume_url="https://cdn/old.pdf",
            )

        self.assertEqual(out["resume"]["name"], "New")
        self.assertEqual(out["marksheet"]["candidate"]["name"], "Old Candidate")
        self.assertEqual(out["coding"]["github"]["repos"], 10)
        self.assertEqual(out["coding"]["leetcode"]["total_solved"], 300)
        self.assertEqual(out["coding"]["coding_persona"], "advanced")
        self.assertEqual(out["resume_url"], "https://cdn/new.pdf")
        marksheet_mock.assert_not_awaited()
        coding_mock.assert_not_awaited()

    async def test_coding_only_change_reuses_existing_resume_and_marksheet(self) -> None:
        with (
            patch("app.services.master_service.call_resume_analyzer", new=AsyncMock()) as resume_mock,
            patch("app.services.master_service.call_marksheet_analyzer", new=AsyncMock()) as marksheet_mock,
            patch(
                "app.services.master_service.call_coding_analyzer",
                new=AsyncMock(return_value=({"github": {"repos": 99}, "leetcode": {"total_solved": 500}, "coding_persona": "expert"}, None)),
            ),
            patch(
                "app.services.master_service.normalize_master_output",
                side_effect=lambda **kwargs: kwargs,
            ),
        ):
            out = await analyze_student_profile_incremental(
                existing_resume_data={"name": "Old Resume", "branch": "CSE"},
                existing_marksheet_data={"candidate": {"name": "Old Candidate"}},
                existing_coding_data={"github": {"repos": 10}, "leetcode": {"total_solved": 300}, "coding_persona": "advanced"},
                resume_file=None,
                resume_filename=None,
                resume_content_type=None,
                marksheet_file=None,
                marksheet_filename=None,
                marksheet_content_type=None,
                resume_changed=False,
                marksheet_changed=False,
                coding_changed=True,
                branch="CSE",
                github="gh",
                leetcode="lc",
                existing_resume_url="https://cdn/old.pdf",
            )

        self.assertEqual(out["resume"]["name"], "Old Resume")
        self.assertEqual(out["marksheet"]["candidate"]["name"], "Old Candidate")
        self.assertEqual(out["coding"]["github"]["repos"], 99)
        self.assertEqual(out["coding"]["leetcode"]["total_solved"], 500)
        self.assertEqual(out["resume_url"], "https://cdn/old.pdf")
        resume_mock.assert_not_awaited()
        marksheet_mock.assert_not_awaited()

    async def test_two_source_change_merges_new_and_old_payloads(self) -> None:
        with (
            patch("app.services.master_service.call_resume_analyzer", new=AsyncMock(return_value=({"name": "New Resume"}, None))),
            patch("app.services.master_service.call_marksheet_analyzer", new=AsyncMock(return_value=({"candidate": {"name": "New Candidate", "class_name": "X", "roll_no": "R1"}}, None))),
            patch("app.services.master_service.call_coding_analyzer", new=AsyncMock()) as coding_mock,
            patch("app.services.master_service.upload_resume_to_cloudinary", new=AsyncMock(return_value="https://cdn/new.pdf")),
            patch(
                "app.services.master_service.normalize_master_output",
                side_effect=lambda **kwargs: kwargs,
            ),
        ):
            out = await analyze_student_profile_incremental(
                existing_resume_data={"name": "Old Resume", "branch": "CSE"},
                existing_marksheet_data={"candidate": {"name": "Old Candidate", "class_name": "X", "roll_no": "R0"}},
                existing_coding_data={"github": {"repos": 10}, "leetcode": {"total_solved": 300}, "coding_persona": "advanced"},
                resume_file=b"resume",
                resume_filename="resume.pdf",
                resume_content_type="application/pdf",
                marksheet_file=b"marksheet",
                marksheet_filename="marksheet.pdf",
                marksheet_content_type="application/pdf",
                resume_changed=True,
                marksheet_changed=True,
                coding_changed=False,
                branch="IT",
                github="gh",
                leetcode="lc",
                existing_resume_url="https://cdn/old.pdf",
            )

        self.assertEqual(out["resume"]["name"], "New Resume")
        self.assertEqual(out["marksheet"]["candidate"]["name"], "New Candidate")
        self.assertEqual(out["coding"]["github"]["repos"], 10)
        self.assertEqual(out["coding"]["coding_persona"], "advanced")
        self.assertEqual(out["resume_url"], "https://cdn/new.pdf")
        coding_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
