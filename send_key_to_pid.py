import time
import AppKit
import Quartz

# -------- CONFIG --------
KEY_SEQUENCE = [18, 19, 20]  # 1, 2, 3
DELAY = 1.0
APP_NAME = "Artix"
# ------------------------

def find_artix_app():
    workspace = AppKit.NSWorkspace.sharedWorkspace()
    apps = workspace.runningApplications()

    for app in apps:
        if app.localizedName() and APP_NAME.lower() in app.localizedName().lower():
            return app
    return None


def send_key(keycode):
    # Key down
    event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)

    # Small press duration
    time.sleep(0.05)

    # Key up
    event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


def main():
    app = find_artix_app()

    if not app:
        print("❌ Artix Launcher not found.")
        return

    pid = app.processIdentifier()
    print(f"✅ Found Artix Launcher (PID: {pid})")

    print("Sending combo: 1 → 2 → 3")

    for key in KEY_SEQUENCE:
        send_key(key)
        time.sleep(DELAY)

    print("Done.")


if __name__ == "__main__":
    main()