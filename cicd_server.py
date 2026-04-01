from flask import Flask, request, jsonify
import subprocess
import logging
import sys

print("CI/CD server file loaded...")

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def run_command(command):
    logging.info(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            shell=True   # ✅ IMPORTANT for Windows
        )
        logging.info(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        logging.error("Command failed!")
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
        return jsonify({"status": "DB startup failed"}), 500

    # 3. Unit Tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/unit"
    ]):
        logging.error("Unit tests failed")
        return jsonify({"status": "Unit tests failed"}), 200

    # 4. Integration Tests
    if not run_command([
        "docker-compose", "run", "--rm", "app",
        "pytest", "tests/integration"
    ]):
        logging.error("Integration tests failed")
        return jsonify({"status": "Integration tests failed"}), 200

    # 5. Deploy
    if not run_command(["docker-compose", "up", "-d"]):
        return jsonify({"status": "Deployment failed"}), 500

    logging.info("Deployment successful!")
    return jsonify({"status": "Deployment successful"}), 200


@app.route("/", methods=["GET"])
def home():
    return "CI/CD Server Running"


if __name__ == "__main__":
    print("Starting CI/CD server...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print("ERROR STARTING SERVER:", e)
        sys.exit(1)