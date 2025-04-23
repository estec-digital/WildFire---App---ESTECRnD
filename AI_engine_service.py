import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import os
import sys
import io
import ctypes  # For admin check

# Force stdout and stderr to use UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


class AIEngineService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AIEngineService"
    _svc_display_name_ = "AI Engine Service"
    _svc_description_ = "This service runs the AI engine script."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("AI Engine service is starting...")

        script_path = "D:\\ChayRungProject\\FireDetector\\main.py"
        config_path = "D:\\ChayRungProject\\FireDetector\\input.json"  # default config path
        python_exe = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"

        stdout_path = "D:\\ChayRungProject\\FireDetector\\Logs\\AI_ENGINE_service_stdout.log"
        stderr_path = "D:\\ChayRungProject\\FireDetector\\Logs\\AI_ENGINE_service_stderr.log"

        with open(stdout_path, "a", encoding="utf-8") as out, \
             open(stderr_path, "a", encoding="utf-8") as err:

            subprocess.Popen(
                [python_exe, script_path, f"config={config_path}"],
                stdout=out,
                stderr=err,
                bufsize=1,
                universal_newlines=True
            )

        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


# Utility: Ensure service runs as LocalSystem after install
def ensure_local_system(service_name):
    try:
        os.system(f'sc config {service_name} obj= "LocalSystem" password= ""')
        print(f"[✔] '{service_name}' is now set to run as LocalSystem (Admin Privilege).")
    except Exception as e:
        print(f"[✘] Failed to configure LocalSystem: {e}")


# Check if run as Administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def disable_quick_edit():
    if sys.platform == "win32":
        import msvcrt
        kernel32 = ctypes.windll.kernel32
        hStdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(hStdin, ctypes.byref(mode))
        new_mode = mode.value & ~0x0040  # Disable ENABLE_QUICK_EDIT_MODE
        kernel32.SetConsoleMode(hStdin, new_mode)

if __name__ == '__main__':
    disable_quick_edit()
    if not is_admin():
        print("[!] Please run this script as Administrator to install or modify the service.")
        sys.exit(1)

    if len(sys.argv) == 2 and sys.argv[1].lower() == "install":
        win32serviceutil.HandleCommandLine(AIEngineService)
        ensure_local_system("AIEngineService")
    else:
        win32serviceutil.HandleCommandLine(AIEngineService)
