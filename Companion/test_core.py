import unittest
from core import LaunchGate, valid_website, approved_executable


class CoreTests(unittest.TestCase):
    def test_requires_stable_hold(self):
        g = LaunchGate()
        self.assertFalse(g.update("peace", .95, 0, .9, 1.5, 5))
        self.assertFalse(g.update("peace", .95, 1, .9, 1.5, 5))
        self.assertTrue(g.update("peace", .95, 1.6, .9, 1.5, 5))
        self.assertFalse(g.update("peace", .95, 20, .9, 1.5, 5))

    def test_uncertainty_resets_hold(self):
        g = LaunchGate()
        g.update("peace", .95, 0, .9, 1, 5)
        g.update("peace", .5, 1, .9, 1, 5)
        self.assertFalse(g.update("peace", .95, 2, .9, 1, 5))
        self.assertTrue(g.update("peace", .95, 3, .9, 1, 5))

    def test_cooldown(self):
        g = LaunchGate()
        g.update("peace", 1, 0, .9, 1, 5)
        self.assertTrue(g.update("peace", 1, 1, .9, 1, 5))
        g.update(None, 0, 2, .9, 1, 5)
        g.update("fist", 1, 3, .9, 1, 5)
        self.assertFalse(g.update("fist", 1, 4, .9, 1, 5))
        self.assertTrue(g.update("fist", 1, 6, .9, 1, 5))

    def test_urls(self):
        self.assertTrue(valid_website("https://youtube.com/watch?v=1"))
        for url in ["file:///etc/passwd", "javascript:alert(1)", "http://example.com", "https://", "https://user:pass@example.com"]:
            self.assertFalse(valid_website(url))

    def test_no_arbitrary_executable(self):
        with self.assertRaises(ValueError):
            approved_executable("cmd.exe /c evil")


if __name__ == "__main__":
    unittest.main()