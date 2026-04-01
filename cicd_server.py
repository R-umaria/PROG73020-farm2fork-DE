from flask import Flask, request, jsonify
import subprocess
import logging
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def run_command(command):
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        return False


@app.route("/webhook", methods=["POST"])
def webhook():
    logging.info("Webhook received. Starting CI/CD pipeline...")

    # 1. Build
    if not run_command(["docker-compose", "build"]):
        return jsonify({"status": "Build failed"}), 500

    # 2. Start DB
    if not run_command(["docker-compose", "up", "-d", "db"]):
        return jsonify({"status": "DB failed"}), 500

    time.sleep(5)

    # 3. Run migrations
    if not run_command([
        "docker-compose", "exec", "app",
        "alembic", "upgrade", "head"
    ]):
        logging.error("Migration failed")
        return jsonify({"status": "Migration failed"}), 200

    # 4. Unit tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/unit"
    ]):
        logging.error("Unit tests failed")
        return jsonify({"status": "Unit tests failed"}), 200

    # 5. Integration tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/integration"
    ]):
        logging.error("Integration tests failed")
        return jsonify({"status": "Integration tests failed"}), 200

    # 6. Deploy
    if not run_command(["docker-compose", "up", "-d"]):
        return jsonify({"status": "Deploy failed"}), 500

    return jsonify({"status": "Deployment successful"}), 200


if __name__ == "__main__":
    print("Starting CI/CD server...")
    app.run(host="0.0.0.0", port=5000, debug=True)