import time
from g4f import webdriver
import g4f.debug

g4f.debug.logging = True  # Enable debug logging
driver = webdriver.get_browser()
try:
    driver.get("https://gemini.google.com/app")
    time.sleep(10000)
finally:
    driver.quit()