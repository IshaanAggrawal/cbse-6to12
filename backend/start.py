"""
Start all CBSE Tutor services locally (development mode).
Run: python start.py
"""

import subprocess
import sys
import time
import os
from pathlib import Path

BASE = Path(__file__).parent

services = [
    {
        "name": "Knowledge Base",
        "cwd": BASE / "knowledge-base",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"],
    },
    {
        "name": "Tutor Service",
        "cwd": BASE / "tutor-service",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"],
    },
    {
        "name": "User Service",
        "cwd": BASE / "user-service",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"],
    },
    {
        "name": "API Gateway",
        "cwd": BASE / "gateway",
        "cmd": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    },
]

procs = []

print("🚀 Starting CBSE AI Tutor services...\n")

for svc in services:
    print(f"  ▸ Starting {svc['name']} ...")
    p = subprocess.Popen(
        svc["cmd"],
        cwd=str(svc["cwd"]),
        env={**os.environ},
    )
    procs.append(p)
    time.sleep(1.5)  # stagger startup

print("\n✅ All services started!")
print("   Gateway:        http://localhost:8000")
print("   Tutor Service:  http://localhost:8001")
print("   User Service:   http://localhost:8002")
print("   Knowledge Base: http://localhost:8003")
print("\n📚 Open frontend/index.html in your browser")
print("   Press Ctrl+C to stop all services\n")

try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping all services...")
    for p in procs:
        p.terminate()
    print("Done.")
