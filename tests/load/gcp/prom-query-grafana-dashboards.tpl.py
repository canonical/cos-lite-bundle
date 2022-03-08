#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import urllib.request

from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions

"""
Login and open a grafana dashboard using a headless browser instance.
"""


interval = ${REFRESH_INTERVAL}  # grafana refresh interval that matches prometheus scrape interval
period = 5 * 60  # reload entire dashboard every 5 minutes


def get_next_sleep_duration() -> float:
    """Calculates the remaining inter-reload sleep duration.

    This is needed in order to have all browser instances more or less synced with each other to
    query grafana server at roughly the same time.
    """
    def get_next_multiple(num, multiple):
        return num + (multiple - (num % multiple))

    tic = time.time()
    toc = get_next_multiple(tic, period)
    return toc - tic


def sleep_until_interval_elapses():
    sleep_duration = get_next_sleep_duration()
    print(f"Sleeping until interval elapses ({sleep_duration:.1f} sec)...", flush=True)
    time.sleep(sleep_duration)


def main():
    options = FirefoxOptions()
    options.headless = True
    # TODO add incognito?

    try:
        executable_path = GeckoDriverManager().install()
        # executable_path = ChromeDriverManager().install()
    except Exception as e:
        print(f"Exception '{type(e)}' raised: {str(e)}")
        time.sleep(5)
        # systemd will restart the process
        return

    GRAFANA_ADMIN_PASSWORD = urllib.request.urlopen("${COS_URL}:8081/helper/grafana/password", data=None, timeout=10.0).read().decode()

    while True:
        try:
            print("Opening up a browser instance...", flush=True)
            service = FirefoxService(executable_path)
            with webdriver.Firefox(service=service, options=options) as driver:
                driver.get("${GRAFANA_URL}/dashboards")

                # wait for login page to load
                print("Logging in...", flush=True)
                user = WebDriverWait(driver, timeout=30).until(
                    lambda d: d.find_element(By.NAME, "user"))
                password = WebDriverWait(driver, timeout=30).until(
                    lambda d: d.find_element(By.NAME, "password"))
                log_in = WebDriverWait(driver, timeout=30).until(
                    lambda d: d.find_element(By.XPATH, "//*[text()='Log in']"))

                user.send_keys("admin")
                password.send_keys(GRAFANA_ADMIN_PASSWORD)
                log_in.click()

                print("Opening dashboard...", flush=True)
                dashboard = WebDriverWait(driver, timeout=120).until(
                    lambda d: d.find_element(By.XPATH, "//*[text()='sre mock 6 panels - rates']"))
                dashboard.click()

                print("'Looking' at dashboard...", flush=True)
                time.sleep(2 * interval)

        except Exception as e:
            print(f"Exception '{type(e)}' raised: {str(e)}")
            print("Waiting for delay to elapse before next iteration", flush=True)

        sleep_until_interval_elapses()


if __name__ == "__main__":
    main()
