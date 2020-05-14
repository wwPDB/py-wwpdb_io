import unittest

from wwpdb.io.locator.ReleasePathInfo import ReleasePathInfo


class ReleasePathInfoTests(unittest.TestCase):
    def setUp(self):
        self.RPI = ReleasePathInfo()

    def test_for_release(self):
        ret = self.RPI.get_for_release_path()
        self.assertIsNotNone(ret)

    def test_for_release_added(self):
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_added_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue('added' in ret)

    def test_for_release_added_previous(self):
        rel_path = self.RPI.get_for_release_path()
        ret = self.RPI.get_previous_added_path()
        self.assertIsNotNone(ret)
        self.assertNotEqual(ret, rel_path)
        self.assertTrue('added' in ret)
        self.assertTrue(self.RPI.previous_folder_name in ret)


if __name__ == '__main__':
    unittest.main()
