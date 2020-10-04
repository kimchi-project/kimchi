import utils
from pages.login import WokLoginPage

VIRTUALIZATION_TAB = "//a[@class = 'item virtualizationTab']"
TEMPLATES_TAB = "//a[@href = 'plugins/kimchi/tabs/templates.html']"
ADD_TEMPLATE = "template-add"
ISOS_LIST = "list-local-iso"

class KimchiTemplatePage():

    def __init__(self, browser):
        self.browser = browser
        assert WokLoginPage(browser).login(), "Cannot login to Kimchi"

    def retrieveDefaulTemplates(self):
        # click virtualization Tab
        utils.clickIfElementIsVisibleByXpath(self.browser,
                                             VIRTUALIZATION_TAB)

        # click templates tab
        utils.clickIfElementIsVisibleByXpath(self.browser,
                                             TEMPLATES_TAB)


        # click add template
        utils.clickIfElementIsVisibleById(self.browser,
                                          ADD_TEMPLATE)

        # iterate over default templates
        utils.waitElementIsVisibleById(self.browser,
                                       ISOS_LIST)

        # retrieve info
        info = []
        for template in self.browser.find_elements_by_tag_name("dl"):
            info.append([info.text for info in template.find_elements_by_tag_name("dt")])
        return info
