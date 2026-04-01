import subprocess

def run():
    subprocess.run(["alembic", "downgrade", "base"], check=True)
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Database reset complete.")

if __name__ == "__main__":
    run()