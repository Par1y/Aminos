import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_options = Options()
chrome_options.binary_location = "chrome-linux64/chrome"
service = Service(executable_path='chromedriver-linux64/chromedriver', service_args=['--allowed-ips='])
service.start()
print(service.service_url)
driver = webdriver.Remote(command_executor=service.service_url, options=chrome_options)
driver.get('http://www.google.com/')
time.sleep(114514) # Let the user actually see something!
driver.quit()