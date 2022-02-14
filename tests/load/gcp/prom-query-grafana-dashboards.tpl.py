#!/usr/bin/env python3

from splinter import Browser
import time

"""
Login and open a grafana dashboard using a headless browser instance.
"""


def login(browser):
    # assuming current page has user and password fields
    browser.fill('user', 'admin')
    # browser.fill('password', "password")
    browser.fill('password', "${GRAFANA_ADMIN_PASSWORD}")
    # Find and click the 'login' button
    button = browser.find_by_text("Log in")[0]
    button.click()


def click_dashboard_name(browser, name: str):
    # assuming current page is the "manage dashboards" page
    dashboards = browser.find_by_text(name)
    dashboard = dashboards[0]
    dashboard.click()


interval = ${REFRESH_INTERVAL}


def main():
    while True:
        print("Opening up a browser instance...")
        browser = Browser('firefox', incognito=True, headless=True)

        browser.visit("${GRAFANA_URL}/dashboards")
        # browser.visit("http://127.0.0.1:8080/grafana/dashboards")
            login(browser)
        click_dashboard_name(browser, "sre mock 6 panels - rates")
        # time.sleep(10)
        time.sleep(2 * interval)
        browser.quit()

        print("Sleeping until interval elapses...")
        time.sleep(max(0, 5 * 60 - 2 * interval))  # do this every 5 minutes


if __name__ == "__main__":
    main()
