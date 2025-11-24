from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions


class ChromedriverProvider(ToolProvider):

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        driver = None
        try:
            uri = credentials.get("chromedriver_uri")
            if not uri:
                raise ToolProviderCredentialValidationError(
                    "chromedriver_uri is required."
                )

            # driver = webdriver.Remote(command_executor=uri, options=ChromiumOptions())
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
        finally:
            # Ensure the validation session is always closed.
            if driver:
                driver.quit()
