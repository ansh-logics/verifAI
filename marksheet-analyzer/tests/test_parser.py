from __future__ import annotations

import unittest

from app.services.extractor import MarksheetExtractor
from app.services.parser import parse_marksheet_text


SAMPLE_MARKSHEET_TEXT = """
Institute Code & Name : (230 ) DRONACHARYA GROUP OF INSTITUTIONS,GAUTAM BUDDH NAGAR
Course Code & Name : (04) B.TECH Branch Code & Name : (153) COMPUTER SCIENCE
RollNo : 2302301530010 EnrollmentNo : 230230153017216
Name : ANSH BHATT Hindi Name : अंश भट्ट
Father's Name : KRISHNA CHANDRA Gender : M
Session : 2023-24(REGULAR) Semesters : 1,2 Result : PCP Marks : 1062/1800 COP : BAS103 Audit 1 : Cleared
Semester : 1 Even/Odd : Odd
Result Status : CP( 1) SGPA : 5.14
Date of Declaration : 25/06/24
Code Name Type Internal External Back Paper Grade
BAS102 Engineering Chemistry Theory 20 25 -- D
Session : 2025-26(BACK) Semesters : 1,2 Result : PWG Marks : 1069/1800 Audit 1 : Cleared
Semester : 1 Even/Odd : Odd
Result Status : CP(1) SGPA : 5.14
Date of Declaration : 26-02-26
Code Name Type Internal External Back Paper Grade
BAS102 Engineering Chemistry Theory 20 25 -- D
Session : 2025-26(REGULAR) Semesters : 5 Result : Marks : 627/900 COP : Audit 2 : Cleared
Semester : 5 Even/Odd : Odd
Result Status : CP( 0) SGPA : 6.74
Date of Declaration : 16/02/26
Code Name Type Internal External Back Paper Grade
BCS501 Database Management System Theory 21 34 -- C
"""


class MarksheetParserTests(unittest.TestCase):
    def test_parse_and_cgpa_latest_attempt(self) -> None:
        student, attempts, warnings = parse_marksheet_text(SAMPLE_MARKSHEET_TEXT)
        self.assertEqual(student.roll_no, "2302301530010")
        self.assertGreaterEqual(len(attempts), 3)

        extractor = MarksheetExtractor()
        response = extractor.build_response(student=student, attempts=attempts, warnings=warnings)

        self.assertAlmostEqual(response.cgpa_computed or 0.0, 5.94, places=2)
        self.assertEqual(response.last_semester_number, 5)
        self.assertAlmostEqual(response.last_semester_sgpa or 0.0, 6.74, places=2)
        self.assertEqual(response.candidate.roll_no, "2302301530010")
        self.assertEqual(response.backlog.has_active_backlog, False)
        self.assertEqual(response.backlog.active_backlog_codes, [])
        self.assertGreaterEqual(response.validation.parser_confidence, 60)


if __name__ == "__main__":
    unittest.main()
