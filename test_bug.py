import os
import imp
from neutron.manager import NeutronManager
from oslo.config import cfg
from neutron.api import extensions
from neutron.version import version_info
from unittest2 import TestCase, TestSuite, TextTestRunner, TestLoader

def setup_test():
    cfg.CONF(args=['--config-file=/etc/neutron/neutron.conf'], project='neutron', version='%%prog %s' % version_info.release_string())
    plugin = NeutronManager.get_plugin()


def _load_all_extensions_from_path(self, path):
    for f in os.listdir(path):
        try:
            mod_name, file_ext = os.path.splitext(os.path.split(f)[-1])
            ext_path = os.path.join(path, f)
            if file_ext.lower() == '.py' and not mod_name.startswith('_'):
                mod = imp.load_source(mod_name, ext_path)
                ext_name = mod_name[0].upper() + mod_name[1:]
                new_ext_class = getattr(mod, ext_name, None)
                if not new_ext_class:
                    continue
                new_ext = new_ext_class()
                self.add_extension(new_ext)
        except Exception as exception:
            raise exception

class TestExtensionManager(TestCase):

    def setUp(self):
        setup_test()
        super(TestExtensionManager, self).setUp()

    def test_extension_manager(self):
        ext_mgr = extensions.PluginAwareExtensionManager(extensions.get_extensions_path(),
                                                         NeutronManager.get_service_plugins())
        self.assertTrue('topology' in ext_mgr.extensions)

    def test_extension_support(self):
        extensions.PluginAwareExtensionManager._load_all_extensions_from_path = _load_all_extensions_from_path

        ext_mgr = extensions.PluginAwareExtensionManager(extensions.get_extensions_path(),
                                                         NeutronManager.get_service_plugins())
        self.assertTrue('topology' not in ext_mgr.extensions)


if __name__ == "__main__":
    suite = TestLoader().loadTestsFromTestCase(TestExtensionManager)
    TextTestRunner(verbosity=2).run(suite)

