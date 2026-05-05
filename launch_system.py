import subprocess
import time
import sys

print("🚀 Launching Federated Enterprise Network...")

# 1. Start Server
server_process = subprocess.Popen([sys.executable, "server.py"])
print("⏳ Waiting 10 seconds for the Server to fully wake up...")
time.sleep(10) # Crucial: gives the CPU time to open the port

# 2. Start Clients
print("📡 Spinning up Secure Edge Node 1...")
client1 = subprocess.Popen([sys.executable, "edge_device.py"])
time.sleep(5) # Stagger the client starts

print("📡 Spinning up Secure Edge Node 2...")
client2 = subprocess.Popen([sys.executable, "edge_device.py"])

print("\n✅ Network is running. Leave this terminal open until training completes.")

try:
    server_process.wait()
    client1.wait()
    client2.wait()
except KeyboardInterrupt:
    print("\n🛑 Shutting down network...")
    server_process.kill()
    client1.kill()
    client2.kill()