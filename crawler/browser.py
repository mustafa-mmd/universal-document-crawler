from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Browser as PlaywrightBrowser
from playwright.sync_api import sync_playwright

from config import BROWSER_TIMEOUT, HEADLESS, LOG_FOLDER, USER_AGENT


class Browser:
    def __init__(
        self,
        *,
        headless: bool = HEADLESS,
        timeout_ms: int = BROWSER_TIMEOUT,
        javascript_enabled: bool = True,
        browser_type: str = "chromium",
        user_agent: str = USER_AGENT,
        proxy_url: str = "",
    ):
        self.playwright = sync_playwright().start()
        engine = getattr(self.playwright, browser_type, None)
        if engine is None:
            self.playwright.stop()
            raise ValueError(f"Unsupported browser engine: {browser_type}")
        launch_options = {"headless": headless}
        if proxy_url:
            launch_options["proxy"] = {"server": proxy_url}
        self.browser: PlaywrightBrowser = engine.launch(**launch_options)
        self.context = self.browser.new_context(
            accept_downloads=True,
            user_agent=user_agent,
            viewport={"width": 1440, "height": 900},
            java_script_enabled=javascript_enabled,
        )
        self.page = self.context.new_page()
        self.timeout_ms = timeout_ms
        self.page.set_default_timeout(timeout_ms)

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        try:
            self.page.wait_for_load_state("networkidle", timeout=min(self.timeout_ms, 5_000))
        except Exception:
            pass

    def click_and_download(self, selector: str):
        try:
            with self.page.expect_download(timeout=5_000) as info:
                self.page.locator(selector).first.click()
            return info.value
        except Exception:
            return None

    def screenshot(self, filename: str = "debug.png") -> Path:
        path = LOG_FOLDER / filename
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def close(self) -> None:
        for resource in (self.context, self.browser, self.playwright):
            try:
                resource.close() if hasattr(resource, "close") else resource.stop()
            except Exception:
                pass
