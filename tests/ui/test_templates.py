import unittest

from utils import getBrowser
from pages.templates import KimchiTemplatePage
EXPECTED_TEMPLATES = [['Debian', '10', 'Not Available'],
                      ['Fedora', '30', 'Not Available'],
                      ['Fedora', '31', 'Not Available'],
                      ['Opensuse', '15.1', 'Not Available'],
                      ['Ubuntu', '19.04', 'Not Available'],
                      ['Ubuntu', '19.10', 'Not Available']
]



VIRTUALIZATION_TAB = "//a[@class = 'item virtualizationTab']"
TEMPLATES_TAB = "//a[@href = 'plugins/kimchi/tabs/templates.html']"
ADD_TEMPLATE = "template-add"
ISOS_LIST = "list-local-iso"


class TestTemplate(unittest.TestCase):

    def setUp(self):
        self.browser = getBrowser()
        self.templatePage = KimchiTemplatePage(self.browser)

    def test_default_templates(self):
        templates = self.templatePage.retrieveDefaulTemplates()

        # assert templates
        for template in templates:
            assert template in EXPECTED_TEMPLATES, f"{template} not found"

    def tearDown(self):
        self.browser.close()

