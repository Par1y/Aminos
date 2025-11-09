import ast
import base64
import json
from collections.abc import Generator
from typing import Any, Tuple

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chromium.options import ChromiumOptions

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.invocations.storage import StorageInvocationError

class ChromedriverTool(Tool):
    _session_key = "chrome_session"

    def _get_driver(self) -> Tuple[WebDriver | None, str | None]:
        """
        得到一个可操作的 WebDriver， 若有已存储的 session 则恢复状态
        """
        uri = self.runtime.credentials.get("chromedriver_uri")
        if not uri:
            return None, "Error: chromedriver_uri is not configured."

        options_str = self.runtime.credentials.get("chromedriver_options", "")
        chrome_options = self._parse_options(options_str)

        # 尝试恢复 session
        if self.session.storage.exist(self._session_key):
            session_id = self.session.storage.get(self._session_key).decode()
            driver = None
            try:
                # 连接副作用，必定会产生一个新的 session
                driver = webdriver.Remote(command_executor=uri, options=chrome_options)
                zombie_session_id = driver.session_id

                # 恢复 session 状态
                driver.session_id = session_id
                driver.title  # session 存活验证

                # 验证成功，杀掉连接产生的僵尸 session
                try:
                    driver.session_id = zombie_session_id
                    driver.close()
                    # 恢复原本存在的 session
                    driver.session_id = session_id
                except Exception:
                    pass  # 错误不管，达到 timeout 会清理
                
                return driver, None # 成功恢复状态，这里就返回了

            except Exception:
                # 恢复 session 状态失败， 可能是浏览器已经关掉了而缓存还在等等
                if driver and 'zombie_session_id' in locals():
                    try:
                        driver.session_id = zombie_session_id
                        driver.close()
                    except Exception:
                        pass # 还是不用管，等 timeout
                
                # 删掉无用的 session_id
                try:
                    self.session.storage.delete(self._session_key)
                except StorageInvocationError:
                    pass
        
        # session 恢复失败或者没有，就新建一个浏览器
        try:
            driver = webdriver.Remote(command_executor=uri, options=chrome_options)
            self.session.storage.set(self._session_key, driver.session_id.encode())
            return driver, None
        except Exception as e:
            return None, f"Error: Failed to create a new session: {e}"

    def _execute_cdp(self, driver: WebDriver, command: str) -> Tuple[str | bytes | None, str | None]:
        """
        执行 CDP 指令
        """
        try:
            cmd_json = json.loads(command)
        except json.JSONDecodeError as e:
            return None, f"invalid json format: {e}"

        cmd = cmd_json.get("cmd")
        if not cmd or not isinstance(cmd, str):
            return None, "'cmd' key is missing or not a string"

        args = cmd_json.get("args", {})

        try:
            result = driver.execute_cdp_cmd(cmd, args)

            if cmd == "Page.captureScreenshot" and 'data' in result:
                return base64.b64decode(result['data']), None
            
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, ensure_ascii=False), None
            
            return str(result), None
        except Exception as e:
            return None, f"Command '{cmd}' execution failed: {e}"

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        插件执行入口
        """
        driver, error = self._get_driver()

        if error:
            yield self.create_text_message(error)
            return
        
        command = tool_parameters.get("command")
        if not command:
            yield self.create_text_message("Error: 'command' parameter is required.")
            return

        result, error = self._execute_cdp(driver, command)

        if error:
            yield self.create_text_message(error)
            return

        if isinstance(result, str):
            yield self.create_text_message(result)
        elif isinstance(result, bytes):
            yield self.create_blob_message(blob=result, meta={"mime_type": "image/png"})
        else:
            yield self.create_text_message("Command executed successfully with no output.")

    def _parse_options(self, options_str: str) -> ChromiumOptions:
        """
        把 Options 字符串变成真正的 Options
        """
        options = ChromiumOptions()
        if not options_str:
            return options
        try:
            tree = ast.parse(f"dict({options_str})")
            for keyword in tree.body[0].value.keywords:
                option_name = keyword.arg
                option_value = ast.literal_eval(keyword.value)
                if hasattr(options, option_name):
                    setattr(options, option_name, option_value)
                elif option_name == "extensions":
                    for ext in option_value:
                        options.add_extension(ext)
                elif option_name == "experimental_options":
                    for key, value in option_value.items():
                        options.add_experimental_option(key, value)
        except (SyntaxError, ValueError):
            for arg in options_str.split():
                options.add_argument(arg)
        return options
