import unittest
from src.qualify import qualify

class QualificationTests(unittest.TestCase):
    def test_urgent_repair(self):
        result = qualify({"name":"Anu","contact":"9999999999","message":"Urgent broken screen repair in Noida today"})
        self.assertEqual(result.intent, "repair")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.city, "Noida")
        self.assertEqual(result.missing_fields, [])

    def test_missing_fields(self):
        result = qualify({"message":"Please book a technician visit"})
        self.assertEqual(result.intent, "appointment")
        self.assertEqual(result.missing_fields, ["name", "contact", "city"])

    def test_general_enquiry(self):
        result = qualify({"name":"Raj","contact":"8888888888","message":"What services do you offer in Pune?"})
        self.assertEqual(result.intent, "general")
        self.assertEqual(result.city, "Pune")

if __name__ == "__main__":
    unittest.main()
