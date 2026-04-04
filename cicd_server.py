from flask import Flask, request, jsonify
import subprocess
import logging
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def run_command(command, fail_on_error=True):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    logging.info(result.stdout)

    if result.returncode != 0:
        logging.warning(result.stderr)
        if fail_on_error:
            return False

    return True


@app.route("/webhook", methods=["POST"])
def webhook():
    logging.info("🚀 Webhook received. Starting CI/CD pipeline...")

    # 1. Stop old containers (safe)
    run_command(["docker-compose", "down"], fail_on_error=False)

    # 2. Build containers
    if not run_command(["docker-compose", "build"]):
        return jsonify({"status": "Build failed"}), 500

    # 3. Start DB
    logging.info("Starting DB container...")
    run_command(["docker-compose", "up", "-d", "db"], fail_on_error=False)

    logging.info("⏳ Waiting for DB to be ready...")
    time.sleep(10)

    # 4. Run migrations
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "alembic", "upgrade", "head"
    ]):
        return jsonify({"status": "Migration failed"}), 500

    # 5. Start full app
    if not run_command(["docker-compose", "up", "-d"]):
        return jsonify({"status": "App start failed"}), 500

    time.sleep(5)

    # 6. Run unit tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/unit"
    ]):
        return jsonify({"status": "Unit tests failed"}), 200

    # 7. Run integration tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/integration"
    ]):
        return jsonify({"status": "Integration tests failed"}), 200

    logging.info("✅ Deployment successful!")
    return jsonify({"status": "Success"}), 200


if __name__ == "__main__":
    print("Starting CI/CD server...")
    app.run(host="0.0.0.0", port=5000, debug=True)