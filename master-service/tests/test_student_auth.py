from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.student import router as student_router
from app.database.database import get_db
from app.database.models import Student


class StudentAuthApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.SessionLocal = sessionmaker(bind=cls.engine, class_=Session, autocommit=False, autoflush=False)
        Student.__table__.create(bind=cls.engine, checkfirst=True)

    @classmethod
    def tearDownClass(cls) -> None:
        Student.__table__.drop(bind=cls.engine, checkfirst=True)

    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(student_router)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)

        with self.SessionLocal() as db:
            db.query(Student).delete()
            db.commit()

    def _register(self, *, email: str, password: str = "StrongPass123") -> dict:
        payload = {
            "name": "Ansh",
            "email": email,
            "password": password,
            "phone": "9999999999",
        }
        response = self.client.post("/student/register", json=payload)
        return {"status": response.status_code, "json": response.json()}

    def test_register_success(self) -> None:
        result = self._register(email="ansh@test.com")
        self.assertEqual(result["status"], 200)
        self.assertTrue(result["json"]["success"])
        self.assertGreater(result["json"]["student_id"], 0)

    def test_duplicate_email_rejected(self) -> None:
        self._register(email="ansh@test.com")
        result = self._register(email="ansh@test.com")
        self.assertEqual(result["status"], 409)
        detail = result["json"]["detail"]
        self.assertEqual(detail["code"], "duplicate_email")
        self.assertIn("student_id", detail)

    def test_login_with_email_success(self) -> None:
        self._register(email="ansh@test.com")
        response = self.client.post(
            "/student/login",
            json={"identifier": "ansh@test.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["access_token"])
        self.assertEqual(body["email"], "ansh@test.com")

    def test_login_with_roll_no_success_after_roll_update(self) -> None:
        register_result = self._register(email="ansh@test.com")
        student_id = register_result["json"]["student_id"]
        with self.SessionLocal() as db:
            student = db.query(Student).filter(Student.id == student_id).one()
            student.roll_no = "AKTU001"
            db.commit()

        response = self.client.post(
            "/student/login",
            json={"identifier": "AKTU001", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["access_token"])
        self.assertEqual(body["roll_no"], "AKTU001")

    def test_login_invalid_password(self) -> None:
        self._register(email="ansh@test.com")
        response = self.client.post(
            "/student/login",
            json={"identifier": "ansh@test.com", "password": "WrongPass123"},
        )
        self.assertEqual(response.status_code, 401)

    def test_roll_no_index_and_uniqueness_declared(self) -> None:
        columns = Student.__table__.c
        self.assertTrue(columns.roll_no.index)
        self.assertTrue(columns.roll_no.unique)


if __name__ == "__main__":
    unittest.main()
