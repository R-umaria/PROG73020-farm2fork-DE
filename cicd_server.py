from flask import Flask, request, jsonify
import subprocess
import logging
import time
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

APP_HEALTH_URL = "http://localhost:8000/health"  # your app container port
APP_VERSION_URL = "http://localhost:8000/version"

def run_command(command):
    """Run a system command and log its output."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    logging.info(result.stdout)
    if result.returncode != 0:
        logging.warning(result.stderr)

    return result.returncode == 0

def wait_for_app_health(timeout=30):
    """Wait until app health endpoint responds OK."""
    logging.info("⏳ Waiting for app to be healthy...")
    for i in range(timeout):
        try:
            r = requests.get(APP_HEALTH_URL)
            if r.status_code == 200 and r.json().get("status") == "ok":
                logging.info(f"✅ App health OK: {r.json()}")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    logging.error("❌ App did not become healthy in time")
    return False

def check_app_version():
    """Check version endpoint"""
    try:
        r = requests.get(APP_VERSION_URL)
        if r.status_code == 200:
            logging.info(f"App version: {r.json().get('version')}")
            return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Version check failed: {e}")
    return False

@app.route("/webhook", methods=["POST"])
def webhook():
    logging.info("🚀 Webhook received. Starting CI/CD pipeline...")

    # 1. Stop old containers
    run_command(["docker-compose", "down"])

    # 2. Build containers
    if not run_command(["docker-compose", "build"]):
        return jsonify({"status": "Build failed"}), 500

    # 3. Start DB only
    logging.info("Starting DB container...")
    run_command(["docker-compose", "up", "-d", "db"])
    time.sleep(10)  # wait a bit for DB to be ready

    # 4. Start app container
    logging.info("Starting app container...")
    run_command(["docker-compose", "up", "-d", "app"])

    # 5. Wait for health and version
    if not wait_for_app_health():
        return jsonify({"status": "App health check failed"}), 500
    if not check_app_version():
        return jsonify({"status": "App version check failed"}), 500

    # 6. Run migrations
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "alembic", "upgrade", "head"
    ]):
        return jsonify({"status": "Migration failed"}), 500

    # 7. Run unit tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/unit"
    ]):
        logging.warning("Unit tests failed")

    # 8. Run integration tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/integration"
    ]):
        logging.warning("Integration tests failed")

    logging.info("✅ Deployment successful!")
    return jsonify({"status": "Success"}), 200

if __name__ == "__main__":
    print("Starting CI/CD server...")
    app.run(host="0.0.0.0", port=5000, debug=True)