import socket
try:
    print("Testing connection to Google...")
    host = socket.gethostbyname("www.googleapis.com")
    print(f"✅ Success! Google IP is: {host}")
except Exception as e:
    print(f"❌ Failed: {e}")