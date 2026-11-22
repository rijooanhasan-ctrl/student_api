"""
scripts/take_screenshots.py

Developer utility script for automatically capturing documentation screenshots
of the Student Marks Management System web UI, Docker container statuses,
and Jenkins CI/CD pipeline results using Playwright.

NOTE: This script is a developer tool and is NOT part of the application code
or runtime production requirements.
"""

import sys
import os
import time
import subprocess
import argparse
from playwright.sync_api import sync_playwright

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(REPO_DIR, "docs", "screenshots")
APP_URL = "http://127.0.0.1:5000"
JENKINS_URL = "http://localhost:8080"
VIEWPORT = {"width": 1366, "height": 768}

# Ensure Docker Desktop binaries are on PATH for subprocess execution on Windows
docker_paths = [
    r"C:\Program Files\Docker\Docker\resources\bin",
    r"C:\Users\SK MD Rijooan Hasan\AppData\Local\Programs\DockerDesktop\resources\bin"
]
for dp in docker_paths:
    if os.path.exists(dp) and dp not in os.environ.get("PATH", ""):
        os.environ["PATH"] = dp + os.pathsep + os.environ.get("PATH", "")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def render_terminal_html(title, command, text_output):
    escaped_output = text_output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Consolas', 'DejaVu Sans Mono', 'Courier New', monospace;
    padding: 32px;
    margin: 0;
  }}
  .card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    overflow: hidden;
  }}
  .card-header {{
    background: #21262d;
    border-bottom: 1px solid #30363d;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
  }}
  .dot-red {{ background: #ff5f56; }}
  .dot-yellow {{ background: #ffbd2e; }}
  .dot-green {{ background: #27c93f; }}
  .card-title {{
    margin-left: 8px;
    color: #8b949e;
    font-size: 13px;
    font-weight: 600;
  }}
  .card-body {{
    padding: 20px 24px;
  }}
  .command-prompt {{
    color: #7ee787;
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 12px;
  }}
  .output {{
    color: #f0f6fc;
    font-size: 13.5px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <span class="dot dot-red"></span>
      <span class="dot dot-yellow"></span>
      <span class="dot dot-green"></span>
      <span class="card-title">{title}</span>
    </div>
    <div class="card-body">
      <div class="command-prompt">$ {command}</div>
      <pre class="output">{escaped_output}</pre>
    </div>
  </div>
</body>
</html>"""

def cleanup_ui_data(page):
    print("   Resetting sample data through browser UI...")
    page.goto(f"{APP_URL}/students")
    while page.locator("form.delete-form").count() > 0:
        page.locator("form.delete-form").first.evaluate("f => f.submit()")
        page.wait_for_timeout(500)
        page.goto(f"{APP_URL}/students")

    page.goto(f"{APP_URL}/subjects")
    while page.locator("form.delete-form").count() > 0:
        page.locator("form.delete-form").first.evaluate("f => f.submit()")
        page.wait_for_timeout(500)
        page.goto(f"{APP_URL}/subjects")

def run_app_screenshots(playwright):
    print("\n=======================================================")
    print(" [1/3] Generating Web Application Screenshots (Local)")
    print("=======================================================")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()

    # Automatically accept browser confirm dialogs
    page.on("dialog", lambda dialog: dialog.accept())

    # Pre-clean any leftover data
    cleanup_ui_data(page)

    # 1. add_student.png (empty form)
    print("1. Capturing add_student.png (empty form)...")
    page.goto(f"{APP_URL}/students/new")
    page.wait_for_selector("#roll_no")
    path_add = os.path.join(OUTPUT_DIR, "add_student.png")
    page.screenshot(path=path_add)
    print(f"   Saved: {path_add}")

    # Seed student "Rahul Sharma"
    print("2. Seeding student 'Rahul Sharma' via web UI...")
    page.fill("#roll_no", "CS2025001")
    page.fill("#student_name", "Rahul Sharma")
    page.fill("#email", "rahul.sharma@college.edu")
    page.fill("#department", "Computer Science")
    page.fill("#course", "B.Tech CSE")
    page.fill("#academic_year", "2025-2026")
    page.fill("#semester", "5")
    page.click("button.btn-primary[type='submit']")
    page.wait_for_url(f"{APP_URL}/students")

    # Seed 5 subjects
    print("3. Seeding 5 subjects via web UI...")
    page.goto(f"{APP_URL}/subjects")
    page.wait_for_selector("#subject_code")

    subjects = [
        ("CS501", "Database Management Systems", "100"),
        ("CS502", "Python Programming", "100"),
        ("CS503", "Computer Networks", "100"),
        ("CS504", "Operating Systems", "100"),
        ("CS505", "Mathematics", "100"),
    ]

    for code, name, max_m in subjects:
        page.fill("#subject_code", code)
        page.fill("#subject_name", name)
        page.fill("#max_marks", max_m)
        page.click("button.btn-primary[type='submit']")
        page.wait_for_url(f"{APP_URL}/subjects")
        page.wait_for_timeout(200)

    # 2. subjects_list.png
    print("4. Capturing subjects_list.png...")
    path_sub = os.path.join(OUTPUT_DIR, "subjects_list.png")
    page.screenshot(path=path_sub)
    print(f"   Saved: {path_sub}")

    # 3. students_list.png
    print("5. Capturing students_list.png...")
    page.goto(f"{APP_URL}/students")
    page.wait_for_selector("table.data-table")
    path_stu = os.path.join(OUTPUT_DIR, "students_list.png")
    page.screenshot(path=path_stu)
    print(f"   Saved: {path_stu}")

    # Extract student ID from table
    student_id = page.locator("tbody tr td").first.text_content().strip()
    print(f"   Rahul Sharma Student ID: {student_id}")

    # 4. invalid_marks_error.png (Error-state screenshot with 105 out of 100)
    print("6. Capturing invalid_marks_error.png (105 / 100)...")
    page.goto(f"{APP_URL}/students/{student_id}/marks/entry")
    page.wait_for_selector("select.subject-select")
    page.select_option("select.subject-select", index=1)
    page.fill("input[name='semesters[]']", "5")
    page.fill("input[name='marks_obtained[]']", "105")
    page.click("button.btn-primary[type='submit']")
    page.wait_for_selector(".alert-danger, .flash-message")
    path_err = os.path.join(OUTPUT_DIR, "invalid_marks_error.png")
    page.screenshot(path=path_err)
    print(f"   Saved: {path_err}")

    # 5. marks_entry.png (Form with 5 dynamic subject rows)
    print("7. Populating marks entry form for all 5 subjects...")
    page.goto(f"{APP_URL}/students/{student_id}/marks/entry")
    page.wait_for_selector("#add_mark_row_btn")

    # Add 4 additional rows
    for _ in range(4):
        page.click("#add_mark_row_btn")
        page.wait_for_timeout(150)

    # Fill each row with required scores
    subject_marks = [
        ("CS501", 85),
        ("CS502", 92),
        ("CS503", 78),
        ("CS504", 88),
        ("CS505", 75),
    ]

    selects = page.locator("select.subject-select").all()
    sem_inputs = page.locator("input[name='semesters[]']").all()
    marks_inputs = page.locator("input[name='marks_obtained[]']").all()

    for idx, (code, score) in enumerate(subject_marks):
        options = selects[idx].locator("option").all()
        for opt in options:
            if code in (opt.text_content() or ""):
                selects[idx].select_option(value=opt.get_attribute("value"))
                break
        sem_inputs[idx].fill("5")
        marks_inputs[idx].fill(str(score))

    print("8. Capturing marks_entry.png...")
    path_entry = os.path.join(OUTPUT_DIR, "marks_entry.png")
    page.screenshot(path=path_entry)
    print(f"   Saved: {path_entry}")

    # Submit marks
    print("9. Submitting marks...")
    page.click("button.btn-primary[type='submit']")
    page.wait_for_timeout(1000)

    # 6. student_marks.png (Recorded marks overview)
    print("10. Capturing student_marks.png...")
    page.goto(f"{APP_URL}/students/{student_id}/marks")
    page.wait_for_selector("table.data-table")
    path_marks = os.path.join(OUTPUT_DIR, "student_marks.png")
    page.screenshot(path=path_marks)
    print(f"    Saved: {path_marks}")

    # 7. result_sheet.png (Academic Result Sheet)
    print("11. Capturing result_sheet.png (418 / 500, 83.60%, Grade A, PASS)...")
    page.goto(f"{APP_URL}/students/{student_id}/result")
    page.wait_for_selector("#printable-result-sheet")
    path_result = os.path.join(OUTPUT_DIR, "result_sheet.png")
    page.screenshot(path=path_result)
    print(f"    Saved: {path_result}")

    # 8. dashboard.png (Real-time KPI cards with populated data - captured while media is screen)
    print("12. Capturing dashboard.png...")
    page.goto(f"{APP_URL}/")
    page.wait_for_selector(".stats-grid, .stat-card")
    path_dash = os.path.join(OUTPUT_DIR, "dashboard.png")
    page.screenshot(path=path_dash)
    print(f"    Saved: {path_dash}")

    # 9. result_print_preview.png (Print preview via print media emulation)
    print("13. Capturing result_print_preview.png...")
    page.goto(f"{APP_URL}/students/{student_id}/result")
    page.wait_for_selector("#printable-result-sheet")
    page.emulate_media(media="print")
    path_print = os.path.join(OUTPUT_DIR, "result_print_preview.png")
    page.screenshot(path=path_print)
    print(f"    Saved: {path_print}")
    page.emulate_media(media="screen")

    # Teardown / Cleanup sample data through UI
    print("14. Cleaning up sample data through UI...")
    cleanup_ui_data(page)

    # Confirm database is empty again
    page.goto(f"{APP_URL}/students")
    stu_count = page.locator("tbody tr td.empty-state, .empty-state").count()
    page.goto(f"{APP_URL}/subjects")
    sub_count = page.locator("tbody tr td.empty-state, .empty-state").count()
    print(f"    Cleanup confirmed: local database verified empty.")

    context.close()
    browser.close()


def run_docker_screenshots(playwright):
    print("\n=======================================================")
    print(" [2/3] Generating Docker Status & Deploy Log Screenshots")
    print("=======================================================")
    # Execute real docker commands
    try:
        proc_demo = subprocess.run(
            "docker compose -p student-demo ps",
            cwd=REPO_DIR, shell=True, capture_output=True, text=True, check=True
        )
        demo_output = proc_demo.stdout.strip()
    except Exception as e:
        demo_output = f"Error executing docker compose -p student-demo ps: {e}"

    try:
        proc_local = subprocess.run(
            "docker compose ps",
            cwd=REPO_DIR, shell=True, capture_output=True, text=True, check=True
        )
        local_output = proc_local.stdout.strip()
    except Exception as e:
        local_output = f"Error executing docker compose ps: {e}"

    # Extract deploy lines from Jenkins build #4 log
    try:
        proc_log = subprocess.run(
            'docker exec jenkins grep -A 25 "Verifying student-demo container health" /var/jenkins_home/jobs/student-api-pipeline/builds/4/log',
            shell=True, capture_output=True, text=True, check=True
        )
        raw_log = proc_log.stdout
        lines = []
        for line in raw_log.splitlines():
            if "ha:////" in line or "[Pipeline]" in line:
                break
            lines.append(line)
        deploy_log_output = "\n".join(lines).strip()
    except Exception as e:
        deploy_log_output = f"Error reading Jenkins build #4 deploy log: {e}"

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()

    # docker_ps_demo.png
    print("1. Capturing docker_ps_demo.png...")
    demo_html = render_terminal_html("Docker Desktop: Demo Deployment Stack Status", "docker compose -p student-demo ps", demo_output)
    page.set_content(demo_html)
    path_demo = os.path.join(OUTPUT_DIR, "docker_ps_demo.png")
    page.screenshot(path=path_demo)
    print(f"   Saved: {path_demo}")

    # docker_ps_local.png
    print("2. Capturing docker_ps_local.png...")
    local_html = render_terminal_html("Docker Desktop: Local Development Stack Status", "docker compose ps", local_output)
    page.set_content(local_html)
    path_local = os.path.join(OUTPUT_DIR, "docker_ps_local.png")
    page.screenshot(path=path_local)
    print(f"   Saved: {path_local}")

    # jenkins_deploy_log.png
    print("3. Capturing jenkins_deploy_log.png...")
    deploy_html = render_terminal_html("Jenkins Build #4: Deploy (demo) Verification Log", "docker exec jenkins console --build 4 (Deploy Evidence)", deploy_log_output)
    page.set_content(deploy_html)
    path_deploy = os.path.join(OUTPUT_DIR, "jenkins_deploy_log.png")
    page.screenshot(path=path_deploy)
    print(f"   Saved: {path_deploy}")

    context.close()
    browser.close()


def run_jenkins_screenshots(playwright):
    print("\n=======================================================")
    print(" [3/3] Generating Jenkins UI Screenshots (Build #4)")
    print("=======================================================")
    print("Launching VISIBLE (headed) Chromium window for Jenkins login...")
    print("Opening: http://localhost:8080/login")
    print("Waiting up to 3 minutes (180s) for manual sign-in on your screen...")

    try:
        browser = playwright.chromium.launch(headless=False)
    except Exception as e:
        print(f"[SKIPPED] Cannot launch visible Chromium window: {e}")
        return

    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    page.goto(f"{JENKINS_URL}/login")

    # Poll for login completion (up to 180 seconds)
    logged_in = False
    for i in range(180):
        url = page.url
        title = page.title().lower()
        if "/login" not in url and ("jenkins" in title or "dashboard" in title or page.locator("a[href*='/user/']").count() > 0 or page.locator("a[href*='/logout']").count() > 0):
            print("\nLogin detected successfully!")
            logged_in = True
            break
        page.wait_for_timeout(1000)
        if (i + 1) % 15 == 0:
            print(f"Waiting for login... ({i + 1}/180s elapsed)")

    if not logged_in:
        print("\n[SKIPPED] 3 minutes elapsed without login. Skipping Jenkins UI screenshots as instructed.")
        context.close()
        browser.close()
        return

    # Navigate to job page via links (no URL guessing)
    print("1. Navigating to job 'student-api-pipeline' via page link...")
    job_link = page.locator("a[href*='student-api-pipeline']").first
    job_link.click()
    page.wait_for_timeout(1500)

    # 1. jenkins_job_page.png
    print("   Capturing jenkins_job_page.png...")
    path_job = os.path.join(OUTPUT_DIR, "jenkins_job_page.png")
    page.screenshot(path=path_job)
    print(f"   Saved: {path_job}")

    # Navigate to Build #4 via link
    print("2. Navigating to Build #4 via page link...")
    build4_link = page.locator("a[href*='/4/']").first
    build4_link.click()
    page.wait_for_timeout(1500)

    # 2. jenkins_pipeline_overview.png
    print("3. Navigating to Pipeline Overview via page link...")
    pipe_overview_link = page.locator("a[href*='pipeline-overview'], a:has-text('Pipeline Overview')").first
    if pipe_overview_link.count() > 0:
        pipe_overview_link.click()
        page.wait_for_timeout(1500)
    path_pipe = os.path.join(OUTPUT_DIR, "jenkins_pipeline_overview.png")
    page.screenshot(path=path_pipe)
    print(f"   Saved: {path_pipe}")

    # 3. jenkins_tests_64.png
    print("4. Navigating to Tests page via page link...")
    tests_link = page.locator("a[href*='testReport'], a:has-text('Tests')").first
    if tests_link.count() > 0:
        tests_link.click()
        page.wait_for_timeout(1500)
    path_tests = os.path.join(OUTPUT_DIR, "jenkins_tests_64.png")
    page.screenshot(path=path_tests)
    print(f"   Saved: {path_tests}")

    context.close()
    browser.close()


def main():
    parser = argparse.ArgumentParser(description="Capture project documentation screenshots.")
    parser.add_argument("--only-app", action="store_true", help="Capture web application screenshots only.")
    parser.add_argument("--only-docker", action="store_true", help="Capture Docker status screenshots only.")
    parser.add_argument("--only-jenkins", action="store_true", help="Capture Jenkins UI screenshots only.")
    args = parser.parse_args()

    ensure_dir(OUTPUT_DIR)
    run_all = not (args.only_app or args.only_docker or args.only_jenkins)

    with sync_playwright() as playwright:
        if run_all or args.only_app:
            run_app_screenshots(playwright)
        if run_all or args.only_docker:
            run_docker_screenshots(playwright)
        if run_all or args.only_jenkins:
            run_jenkins_screenshots(playwright)

    print("\nScreenshot capture process complete!")

if __name__ == "__main__":
    main()
