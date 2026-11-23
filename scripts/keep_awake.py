"""Open the live app in a headless browser and wake it if Streamlit has put it to sleep.

Streamlit Community Cloud sleeps apps after about 12 hours without visitors. A plain
HTTP request does not wake them: a real browser has to load the page and click
"Yes, get this app back up!". Run by .github/workflows/keep-awake.yml during judging.

    python scripts/keep_awake.py https://pump-detective.streamlit.app/
"""

import sys

from playwright.sync_api import sync_playwright

APP_URL = sys.argv[1] if len(sys.argv) > 1 else "https://pump-detective.streamlit.app/"
WAKE_BUTTON = "Yes, get this app back up!"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(8_000)  # let Streamlit decide whether to show the app or the sleep page
        button = page.get_by_role("button", name=WAKE_BUTTON)
        if button.count() > 0:
            print("App was asleep: clicking the wake-up button.")
            button.first.click()
            page.wait_for_timeout(90_000)  # the container needs about a minute to start
            if page.get_by_role("button", name=WAKE_BUTTON).count() > 0:
                browser.close()
                sys.exit("The app is still showing the sleep page after waking. Check it in the Streamlit dashboard.")
            print("Wake-up requested; the app is starting.")
        else:
            print("App is awake.")
        browser.close()


if __name__ == "__main__":
    main()
