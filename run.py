import subprocess
import webbrowser
import time

print("Starting router API...")

subprocess.Popen([
    "uvicorn",
    "router.server:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000"
])

time.sleep(3)

print("Starting Open WebUI...")

subprocess.Popen([
    "open-webui",
    "serve"
])

time.sleep(5)

print("Opening browser...")

webbrowser.open("http://localhost:8080")