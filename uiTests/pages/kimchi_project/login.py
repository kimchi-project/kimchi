import logging
import os
import utils

# locators by ID
USERNAME = "username"
PASSWORD = "password"
LOGIN_BUTTON = "btn-login"
LOGIN_BAR = "user-login"

# environment variables
ENV_USER = "KIMCHI_USERNAME"
ENV_PASS = "KIMCHI_PASSWORD"
ENV_PORT = "KIMCHI_PORT"
ENV_HOST = "KIMCHI_HOST"


class KimchiLoginPage():
    """
    Page object to Login

    Expect environment variables:
    KIMCHI_USERNAME: username for the host
    KIMCHI_PASSWORD: password for the host
    KIMCHI_HOST: host for kimchi
    KIMCHI_PORT: port for kimchi
    """

    def __init__(self, browser):
        self.browser = browser

        # assert envs
        assert ENV_USER in os.environ, f"{ENV_USER} is a required environment var"
        assert ENV_PASS in os.environ, f"{ENV_PASS} is a required environment var"
        assert ENV_HOST in os.environ, f"{ENV_HOST} is a required environment var"

        # get values
        host = os.environ[ENV_HOST]
        port = os.environ.get(ENV_PORT) or "8001"
        self.user = os.environ[ENV_USER]
        self.password = os.environ[ENV_PASS]

        self.browser.get(f"https://{host}:{port}/login.html")

    def login(self):
        # fill user and password
        utils.fillTextIfElementIsVisibleById(self.browser,
                                             USERNAME,
                                             self.user)
        utils.fillTextIfElementIsVisibleById(self.browser,
                                             PASSWORD,
                                             self.password)

        # press login
        utils.clickIfElementIsVisibleById(self.browser, LOGIN_BUTTON)

        # login bar not found: return error
        if utils.waitElementIsVisibleById(self.browser, LOGIN_BAR) == False:
            logging.error(f"Invalid credentials")
            return False
        return True
