import unittest
import os
from os.path import join, dirname, abspath, exists, isdir, normpath
from shutil import copy, rmtree
from os import remove, listdir
import string
import filecmp
import sys
sys.path.insert(0, '..')
from builder import BuilderManager
from builder.minisetting import Setting
import time

def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


class  ServicesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.setting = Setting()
        cls.setting['LOG_ENABLED'] = False
        cls.setting['DATA_DIR'] = join(dirname(dirname(abspath(__file__))), "docs")
        cls.setting['PUBLISH_DIR'] = join(dirname(dirname(abspath(__file__))), "share")
        cls.builder_manager = BuilderManager(cls.setting)
        cls.test_data_dir = join(dirname(abspath(__file__)), "test_data")
        cls.dst_dir = dirname(dirname(abspath(__file__)))
    
    def test_1_get_empty_service_list(self):
        # test 1 get empty services list
        build_services, publish_services = self.builder_manager.get_services_list()
        self.assertFalse(build_services)
        self.assertFalse(publish_services)

    def test_2_init_services(self):
        copy(join(self.test_data_dir, "database.json"), join(self.dst_dir, "database.json"))
        build_services, publish_services = self.builder_manager.get_services_list()
        self.assertIn("note", build_services)
        self.assertIn("note", publish_services)
        self.assertIn("yocto-docs", build_services)
        self.assertIn("yocto-docs", publish_services)
        self.builder_manager.init()
        self.assertTrue(exists(join(self.setting['DATA_DIR'], 'note', '.git')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'note')))
        self.assertTrue(exists(join(self.setting['DATA_DIR'], 'yocto-docs', '.git')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs')))

    def test_3_build_service(self):
        self.assertTrue(self.builder_manager.build_service('note'))
        self.assertTrue(exists(join(self.setting['DATA_DIR'], 'note', '_build', 'html')))
        self.assertTrue(self.builder_manager.build_service('yocto-docs'))
        self.assertTrue(exists(join(self.setting['DATA_DIR'], 'yocto-docs', 'build')))
    
    def test_4_publish_service(self):
        self.assertTrue(self.builder_manager.publish_service('note'))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'note', 'index.html')))
        self.assertTrue(self.builder_manager.publish_service('yocto-docs'))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'adt-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'brief-yoctoprojectqs.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'bsp-guide.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'dev-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'kernel-dev.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'overview-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'profile-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'ref-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'sdk-manual.html')))
        self.assertTrue(exists(join(self.setting['PUBLISH_DIR'], 'yocto-docs', 'toaster-manual.html')))

    @classmethod
    def tearDownClass(cls):
        if exists(join(cls.dst_dir, "database.json")):
            remove(join(cls.dst_dir, "database.json"))
        for dirs in [cls.setting['DATA_DIR'], cls.setting['PUBLISH_DIR']]:
            if exists(dirs):
                rmtree(dirs, onerror=onerror)

if __name__ == '__main__':
    unittest.main()
