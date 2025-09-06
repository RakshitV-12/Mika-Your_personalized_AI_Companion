import subprocess
import time
import os

# Path to Animaze executable (update this if installed elsewhere)
animaze_path = r"C:\Users\DeLL\Desktop\2514022168542611426.vrm"

# Step 1: Start Animaze
if os.path.exists(animaze_path):
    try:
        animaze_process = subprocess.Popen(animaze_path)
        print("Starting Animaze...")
        time.sleep(10)  # Wait for Animaze to fully load
    except Exception as e:
        print(f"Error launching Animaze: {e}")
else:
    print("Error: Animaze executable not found. Please check the path.")

# Step 2: Start AI Chatbot (Mika)
mika_script = "mika.py"  # Ensure this script exists in the same folder

if os.path.exists(mika_script):
    try:
        chatbot_process = subprocess.Popen(["python", mika_script])
        print("Mika AI is running...")
    except Exception as e:
        print(f"Error launching Mika AI: {e}")
else:
    print("Error: mika.py not found. Please check the file path.")

# Keep script running to ensure Mika stays active
try:
    chatbot_process.wait()
except KeyboardInterrupt:
    print("Closing Mika AI...")
    chatbot_process.terminate()
