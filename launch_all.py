# launch_all.py - Launch all Kejafi services including Stage 3
import subprocess
import time
import webbrowser
import sys

def launch():
    print("=" * 60)
    print("🚀 Launching Kejafi Workspace")
    print("=" * 60)
    
    print("\n[1/4] Starting Backend API on port 8000...")
    backend = subprocess.Popen([sys.executable, "backend.py"])
    time.sleep(3)
    
    print("[2/4] Starting Stage 2 (Tokenization) on port 8502...")
    stage2 = subprocess.Popen(["streamlit", "run", "stage2.py", "--server.port", "8502"])
    time.sleep(3)
    
    print("[3/4] Starting Stage 1 (Research) on port 8501...")
    stage1 = subprocess.Popen(["streamlit", "run", "stage1.py", "--server.port", "8501"])
    time.sleep(3)
    
    print("[4/4] Starting Stage 3 (Portfolio Management) on port 8504...")
    stage3 = subprocess.Popen(["streamlit", "run", "stage3.py", "--server.port", "8504"])
    time.sleep(2)
    
    # Open all browsers
    webbrowser.open("http://localhost:8502")  # Stage 2 - Main
    webbrowser.open("http://localhost:8501")  # Stage 1 - Research
    webbrowser.open("http://localhost:8504")  # Stage 3 - Portfolio
    webbrowser.open("http://localhost:8000/docs")  # API Docs
    
    print("\n" + "=" * 60)
    print("✅ All services running!")
    print("   Stage 1 (Research):     http://localhost:8501")
    print("   Stage 2 (Tokenization): http://localhost:8502")
    print("   Stage 3 (Portfolio):    http://localhost:8504")
    print("   API Docs:               http://localhost:8000/docs")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all services...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        backend.terminate()
        stage1.terminate()
        stage2.terminate()
        stage3.terminate()
        print("✅ Done.")

if __name__ == "__main__":
    launch()
