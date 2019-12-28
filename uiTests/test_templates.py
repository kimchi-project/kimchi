import unittest

from utils import getBrowser
from pages.kimchi_project.templates import KimchiTemplatePage

EXPECTED_TEMPLATES = [['Fedora', '29', 'Not Available'],
                      ['Ubuntu', '14.04.6', 'Not Available'],
                      ['Ubuntu', '14.10', 'Not Available'],
                      ['Ubuntu', '15.04', 'Not Available'],
                      ['Ubuntu', '15.10', 'Not Available'],
                      ['Ubuntu', '16.04.06', 'Not Available'],
                      ['Gentoo', '20140826', 'Not Available'],
                      ['Gentoo', '20160514', 'Not Available']
]

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

