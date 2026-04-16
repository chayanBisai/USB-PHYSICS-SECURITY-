import os
import time
import ctypes
import random
import smtplib
import subprocess
from email.message import EmailMessage

# =========================
# CONFIGURATION
# =========================
SENDER_EMAIL = "yourprojectmail@gmail.com"
SENDER_APP_PASSWORD = "your_16_char_app_password"
RECEIVER_EMAIL = "yourreceiveremail@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

CHECK_INTERVAL = 3  # seconds

# =========================
# WINDOWS USB DETECTION
# =========================
DRIVE_REMOVABLE = 2

def get_removable_drives():
    """Return a set of removable drive letters like {'E:\\', 'F:\\'}"""
    drives = set()
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if bitmask & 1:
            drive = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            if drive_type == DRIVE_REMOVABLE:
                drives.add(drive)
        bitmask >>= 1

    return drives

# =========================
# OTP FUNCTIONS
# =========================
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(otp, detected_drive):
    """Send OTP to receiver email"""
    msg = EmailMessage()
    msg["Subject"] = "USB Security OTP Verification"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(
        f"A USB device was detected on {detected_drive}.\n\n"
        f"Your OTP is: {otp}\n\n"
        f"Enter this OTP to authorize USB access."
    )

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)
        print(f"[INFO] OTP sent to {RECEIVER_EMAIL}")
        return True
    except Exception as e:
        print("[ERROR] Failed to send email:", e)
        return False

# =========================
# BLOCK / DISMOUNT USB
# =========================
def block_usb_drive(drive):
    """
    Attempt to dismount/block the USB drive.
    Requires administrator privileges.
    """
    try:
        print(f"[ALERT] Blocking USB drive: {drive}")
        subprocess.run(
            ["mountvol", drive, "/p"],
            check=True,
            shell=True
        )
        print(f"[SUCCESS] USB drive {drive} blocked/dismounted.")
    except Exception as e:
        print(f"[ERROR] Could not block {drive}. Run as Administrator.")
        print("Details:", e)

# =========================
# AUTHORIZATION PROCESS
# =========================
def authorize_usb(drive):
    otp = generate_otp()
    email_sent = send_otp_email(otp, drive)

    if not email_sent:
        print("[WARNING] Email not sent. Blocking for safety.")
        block_usb_drive(drive)
        return

    user_otp = input("Enter the OTP sent to your email: ").strip()

    if user_otp == otp:
        print("[SUCCESS] Correct OTP. USB authorized.")
    else:
        print("[FAIL] Wrong OTP. Unauthorized USB detected.")
        block_usb_drive(drive)

# =========================
# MAIN MONITOR LOOP
# =========================
def main():
    print("USB Physical Security System Started...")
    print("Waiting for USB insertion...\n")

    known_drives = get_removable_drives()

    while True:
        time.sleep(CHECK_INTERVAL)
        current_drives = get_removable_drives()

        new_drives = current_drives - known_drives
        removed_drives = known_drives - current_drives

        for drive in new_drives:
            print(f"[DETECTED] New USB drive inserted: {drive}")
            authorize_usb(drive)

        for drive in removed_drives:
            print(f"[INFO] USB drive removed: {drive}")

        known_drives = current_drives

if __name__ == "__main__":
    main()
