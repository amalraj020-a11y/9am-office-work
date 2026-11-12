import unittest

from src.triage import triage_booking


class BookingTriageTests(unittest.TestCase):
    def test_complete_plumbing_booking(self):
        result = triage_booking({
            "name": "Anu",
            "mobile": "9999999999",
            "email": "anu@example.test",
            "city": "Pune",
            "preferred_time": "Tomorrow morning",
            "message": "Plumber needed for a leaking pipe",
        })
        self.assertEqual(result.service, "plumbing")
        self.assertEqual(result.route, "availability_review")
        self.assertEqual(result.missing_fields, [])

    def test_urgent_request(self):
        result = triage_booking({
            "name": "Dev",
            "mobile": "8888888888",
            "email": "dev@example.test",
            "city": "Noida",
            "preferred_time": "Today",
            "message": "Emergency electrician needed immediately",
        })
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.route, "urgent_review")
        self.assertGreaterEqual(result.priority_score, 80)

    def test_missing_information(self):
        result = triage_booking({"message": "Need home cleaning"})
        self.assertEqual(result.service, "cleaning")
        self.assertEqual(result.route, "request_missing_information")
        self.assertEqual(result.missing_fields, ["name", "mobile", "email", "city", "preferred_time"])

    def test_unknown_service_requests_details(self):
        result = triage_booking({
            "name": "Mira",
            "mobile": "7777777777",
            "email": "mira@example.test",
            "city": "Delhi",
            "preferred_time": "Friday",
            "message": "I need help at home",
        })
        self.assertIn("service_details", result.missing_fields)


if __name__ == "__main__":
    unittest.main()
