"""
install.py — Install all service dependencies
Run: python install.py
"""
import subprocess, sys, pathlib

services = ["knowledge-base", "tutor-service", "gateway", "user-service"]
base = pathlib.Path(__file__).parent

for svc in services:
    req = base / svc / "requirements.txt"
    print(f"\n📦 Installing {svc} dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=True)

print("\n✅ All dependencies installed!")
print("   Next: python knowledge-base/ingester.py  (add to Pinecone)")
print("   Then: python start.py")
