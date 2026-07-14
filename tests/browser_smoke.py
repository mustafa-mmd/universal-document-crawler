"""Opt-in browser smoke test for a running local UDC Pro frontend."""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from playwright.sync_api import expect, sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    project_name = f"Browser smoke {uuid4().hex[:8]}"
    console_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: console_errors.append(str(error)))

        page.goto(f"{args.base_url}/dashboard", wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Good to see you.", level=2)).to_be_visible()
        expect(page.get_by_text("API 0.7.0 connected")).to_be_visible()

        expected_routes = {
            "/crawler": "Start a precise crawl",
            "/jobs": "Crawl operations",
            "/documents": "Your document library",
            "/projects": "Projects",
            "/analytics": "Document intelligence at a glance",
            "/logs": "Runtime logs",
            "/docs": "Learn UDC Pro",
            "/settings": "Crawler settings",
        }
        for route, heading in expected_routes.items():
            page.goto(f"{args.base_url}{route}", wait_until="domcontentloaded")
            expect(page.get_by_role("heading", name=heading, exact=True, level=2)).to_be_visible()
            assert page.locator("[data-nextjs-dialog]").count() == 0

        page.goto(f"{args.base_url}/documents", wait_until="domcontentloaded")
        clear_library = page.get_by_role("button", name="Clear library")
        expect(clear_library).to_be_visible()
        if clear_library.is_enabled():
            clear_library.click()
            expect(page.get_by_text("All original files will remain untouched in their PC folders.", exact=False)).to_be_visible()
            page.get_by_role("button", name="Cancel", exact=True).click()

        page.goto(f"{args.base_url}/projects", wait_until="domcontentloaded")
        page.get_by_role("button", name="New project").click()
        page.get_by_label("Project name").fill(project_name)
        page.get_by_label("Description").fill("Created and removed by the browser smoke test")
        page.get_by_role("button", name="Create project", exact=True).click()
        expect(page.get_by_role("heading", name=project_name, level=3)).to_be_visible()
        project_card = page.get_by_role("heading", name=project_name, level=3).locator("xpath=ancestor::div[contains(@class,'rounded-xl')]")
        project_card.get_by_role("link", name="Open project").click()
        expect(page.get_by_role("heading", name=project_name, level=2)).to_be_visible()

        page.goto(f"{args.base_url}/projects", wait_until="domcontentloaded")
        page.get_by_label(f"Delete {project_name}").click()
        page.get_by_label(f"Confirm deletion of {project_name}").click()
        expect(page.get_by_role("heading", name=project_name, level=3)).to_have_count(0)

        page.goto(f"{args.base_url}/docs/quick-start", wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Quick start", exact=True, level=2)).to_be_visible()
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=args.screenshot, full_page=True)
        browser.close()

    if console_errors:
        raise AssertionError("Browser console errors:\n" + "\n".join(console_errors))
    print("Browser smoke test passed: routes, API status, project CRUD, docs, and console.")


if __name__ == "__main__":
    main()
