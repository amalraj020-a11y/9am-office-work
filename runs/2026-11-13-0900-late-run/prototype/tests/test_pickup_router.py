import unittest
from src.pickup_router import route_pickup

class PickupRouterTests(unittest.TestCase):
    def test_routes_carmelaram_area(self):
        r=route_pickup({"name":"Anu","phone":"999","area":"Mullur","service":"dry cleaning","pickup_slot":"Tomorrow"})
        self.assertEqual((r.branch,r.route,r.missing_fields),("Carmelaram","standard_pickup_confirmation",[]))
    def test_routes_attibele_area(self):
        r=route_pickup({"name":"Dev","phone":"888","area":"Attibele","service":"ironing","pickup_slot":"Friday"})
        self.assertEqual(r.branch,"Attibele")
    def test_express_requires_review(self):
        r=route_pickup({"name":"Mira","phone":"777","area":"Sarjapur Road","service":"washing and folding","pickup_slot":"Today","notes":"same day express"})
        self.assertEqual((r.priority,r.route),("high","express_availability_review"))
    def test_unknown_area(self):
        r=route_pickup({"area":"Whitefield","service":"dry cleaning"})
        self.assertIn("service_area_confirmation",r.missing_fields)

if __name__ == "__main__": unittest.main()
