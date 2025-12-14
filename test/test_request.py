import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase2.request import Request, WAITING, ASSIGNED, PICKED, DELIVERED, EXPIRED
from phase2.point import Point

class TestRequestInit(unittest.TestCase):
    """Test Request initialization and attributes."""

    def test_minimal_init(self):
        """Request initializes with correct defaults."""
        req = Request(id=1, pickup=Point(1, 2), dropoff=Point(3, 4), creation_time=5)
        self.assertEqual(req.id, 1)
        self.assertEqual(req.pickup, Point(1, 2))
        self.assertEqual(req.dropoff, Point(3, 4))
        self.assertEqual(req.creation_time, 5)
        self.assertEqual(req.status, WAITING)
        self.assertIsNone(req.assigned_driver_id)
        self.assertEqual(req.wait_time, 0)

    def test_repr(self):
        """__repr__ returns a string with id and status."""
        req = Request(id=2, pickup=Point(0, 0), dropoff=Point(1, 1), creation_time=0)
        s = repr(req)
        self.assertIn("id=2", s)
        self.assertIn("status=WAITING", s)

class TestRequestStatusTransitions(unittest.TestCase):
    """Test status transitions and error handling."""

    def setUp(self):
        self.req = Request(id=1, pickup=Point(0, 0), dropoff=Point(1, 1), creation_time=10)

    def test_is_active(self):
        """Active for WAITING, ASSIGNED, PICKED; not for DELIVERED, EXPIRED."""
        self.assertTrue(self.req.is_active())
        self.req.status = ASSIGNED
        self.assertTrue(self.req.is_active())
        self.req.status = PICKED
        self.assertTrue(self.req.is_active())
        self.req.status = DELIVERED
        self.assertFalse(self.req.is_active())
        self.req.status = EXPIRED
        self.assertFalse(self.req.is_active())

    def test_mark_assigned_from_waiting(self):
        """Can assign from WAITING."""
        self.req.mark_assigned(42)
        self.assertEqual(self.req.status, ASSIGNED)
        self.assertEqual(self.req.assigned_driver_id, 42)

    def test_mark_assigned_from_assigned(self):
        """Can assign again from ASSIGNED."""
        self.req.status = ASSIGNED
        self.req.mark_assigned(99)
        self.assertEqual(self.req.status, ASSIGNED)
        self.assertEqual(self.req.assigned_driver_id, 99)

    def test_mark_assigned_invalid_status(self):
        """Cannot assign from PICKED/DELIVERED/EXPIRED."""
        for status in [PICKED, DELIVERED, EXPIRED]:
            self.req.status = status
            with self.assertRaises(ValueError):
                self.req.mark_assigned(1)

    def test_mark_picked_from_assigned(self):
        """Can pick from ASSIGNED."""
        self.req.status = ASSIGNED
        self.req.mark_picked(15)
        self.assertEqual(self.req.status, PICKED)
        self.assertEqual(self.req.wait_time, 5)

    def test_mark_picked_from_picked(self):
        """Can pick again from PICKED."""
        self.req.status = PICKED
        self.req.mark_picked(20)
        self.assertEqual(self.req.status, PICKED)
        self.assertEqual(self.req.wait_time, 10)

    def test_mark_picked_invalid_status(self):
        """Cannot pick from WAITING/DELIVERED/EXPIRED."""
        for status in [WAITING, DELIVERED, EXPIRED]:
            self.req.status = status
            with self.assertRaises(ValueError):
                self.req.mark_picked(20)

    def test_mark_delivered_from_picked(self):
        """Can deliver from PICKED."""
        self.req.status = PICKED
        self.req.mark_delivered(25)
        self.assertEqual(self.req.status, DELIVERED)
        self.assertEqual(self.req.wait_time, 15)

    def test_mark_delivered_from_delivered(self):
        """Can deliver again from DELIVERED."""
        self.req.status = DELIVERED
        self.req.mark_delivered(30)
        self.assertEqual(self.req.status, DELIVERED)
        self.assertEqual(self.req.wait_time, 20)

    def test_mark_delivered_invalid_status(self):
        """Cannot deliver from WAITING/ASSIGNED/EXPIRED."""
        for status in [WAITING, ASSIGNED, EXPIRED]:
            self.req.status = status
            with self.assertRaises(ValueError):
                self.req.mark_delivered(30)

    def test_mark_expired_from_active(self):
        """Can expire from WAITING/ASSIGNED/PICKED."""
        for status in [WAITING, ASSIGNED, PICKED]:
            self.req.status = status
            self.req.mark_expired(50)
            self.assertEqual(self.req.status, EXPIRED)
            self.assertEqual(self.req.wait_time, 40)

    def test_mark_expired_invalid_status(self):
        """Cannot expire from DELIVERED/EXPIRED."""
        for status in [DELIVERED, EXPIRED]:
            self.req.status = status
            with self.assertRaises(ValueError):
                self.req.mark_expired(60)

class TestRequestWaitTime(unittest.TestCase):
    """Test wait_time updating logic."""

    def setUp(self):
        self.req = Request(id=1, pickup=Point(0, 0), dropoff=Point(1, 1), creation_time=5)

    def test_update_wait_waiting(self):
        """Updates wait_time in WAITING status."""
        self.req.status = WAITING
        self.req.update_wait(10)
        self.assertEqual(self.req.wait_time, 5)

    def test_update_wait_assigned(self):
        """Updates wait_time in ASSIGNED status."""
        self.req.status = ASSIGNED
        self.req.update_wait(12)
        self.assertEqual(self.req.wait_time, 7)

    def test_update_wait_other_statuses(self):
        """No effect in PICKED/DELIVERED/EXPIRED."""
        for status in [PICKED, DELIVERED, EXPIRED]:
            self.req.status = status
            self.req.wait_time = 42
            self.req.update_wait(100)
            self.assertEqual(self.req.wait_time, 42)

if __name__ == '__main__':
    unittest.main()
