from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions

class ChromedriverProvider(ToolProvider):
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            uri=credentials.get("chromedriver_uri")
            options = ChromiumOptions()
            options.binary_location = "chrome-linux64/chrome"
            driver = webdriver.Remote(command_executor=uri, options=options)
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
