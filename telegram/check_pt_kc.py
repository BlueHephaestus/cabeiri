# Generated by Selenium IDE
#import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from telegram_utils import notify

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from utils.loop_utils import persistent


interval=60

@persistent(interval=interval)
def main():
    prev_time = 0
    while True:

        options = ChromeOptions()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        #driver = webdriver.Chrome()
        vars = {}

        driver.get("https://www.fluidbody.net/appointments")
        driver.execute_script("window.scrollTo(0, 50)")
        time.sleep(1.5)

        #driver.set_window_size(3834, 2031)
        driver.switch_to.frame(0)
        driver.find_element(By.CSS_SELECTOR, ".select-item-box:nth-child(3) .btn").click()
        # Wait for animation
        time.sleep(1.5)

        # get # of weeks for nearest appt
        try:
            earliest_time = driver.find_element(By.XPATH, "//*[@id='dates-and-times']/fieldset[1]").text
            earliest_time = earliest_time.replace(", Continue », Recurring...","")
            week_n = int(earliest_time.split(" ")[1])
        except:
            week_n = 0
            earliest_time = None

            try:
                # Get it from the string itself if possible, in this case
                if earliest_time is not None:
                    datestr = earliest_time.split("\n")[1]
                    week_n = int(datestr.split(" ")[1])
                    print(week_n)
            except:
                week_n = 0

        if prev_time == 0 and earliest_time is not None:
            msg = "Initialising Bot, Current Opening for KC Physical Therapy: \n" + ", ".join(earliest_time.split("\n"))
            print(msg)
            notify(msg)
            prev_time = earliest_time

        if week_n <= 2 and prev_time != earliest_time and earliest_time is not None:
            # within x weeks of today, that's close enough for us to notify of new opening
            # also don't repeat as long as the opening is available.
            msg = "New Opening for KC Physical Therapy: \n" + ", ".join(earliest_time.split("\n"))
            print(msg)
            notify(msg)
            prev_time = earliest_time
        driver.quit()

        #finally: driver.quit()

        time.sleep(interval)

if __name__ == "__main__":
    main()
