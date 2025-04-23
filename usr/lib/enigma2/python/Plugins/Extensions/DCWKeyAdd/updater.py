#############################################################################
#  Add Auto DCW Key And ADD Manual BISS Key Plugin for Enigma2 by @Youchie ##
#  Version: 1.0.5                                                          ##
#  Coded by @Youchie SmartCam Tem (c)2025                                  ##
#  Telegram ID: @Youchie                                                   ##
#  Telegram Channel: Smartcam_1                                            ##
#  github: https://github.com/smcam                                        ##
#  github: https://github.com/Youchie                                      ##
#############################################################################
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from Screens.Screen import Screen
from Components.ProgressBar import ProgressBar
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import sys
import time
import subprocess
import shutil
import json
import socket
import threading
import traceback
from twisted.internet import reactor

PY3 = sys.version_info[0] == 3

if not PY3:
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urllib import urlencode
else:
    from urllib.parse import urlencode

VERSION = "1.0.5"
GITHUB_REPO = "smcam/Auto-DCW-Key-ADD"
PLUGIN_NAME = "DCWKeyAdd"
INSTALL_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd"
BACKUP_PATH = "/tmp/dcwkeyadd_backup"
LOG_FILE = "/tmp/dcwkeyadd_install.log"
MAX_RETRIES = 3
TIMEOUT = 30
CHUNK_SIZE = 8192

class UpdateSystem:

    @staticmethod
    def get_log_locations():
        return [
            "/tmp/dcwkeyadd_install.log",
            "/var/log/dcwkeyadd_install.log",
            os.path.expanduser("~/dcwkeyadd_install.log"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "dcwkeyadd_install.log")
        ]

    @staticmethod
    def log(message, level="INFO"):
        log_success = False
        last_error = None
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"

        print(log_entry)

        for log_file in UpdateSystem.get_log_locations():
            try:
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)

                if log_file == LOG_FILE and os.path.exists(log_file) and os.path.getsize(log_file) > 1*1024*1024:
                    rotated = f"{log_file}.1"
                    if os.path.exists(rotated):
                        os.remove(rotated)
                    os.rename(log_file, rotated)

                with open(log_file, "a") as f:
                    f.write(log_entry + "\n")
                    f.flush()
                log_success = True
                break
            except Exception as e:
                last_error = str(e)
                continue

        if not log_success:
            print(f"ALL LOG LOCATIONS FAILED! Message: {message}")
            if last_error:
                print(f"Last error: {last_error}")

    @staticmethod
    def validate_url(url):
        """Validate GitHub download URL"""
        return (isinstance(url, str) and
                url.startswith('https://github.com/') and
                url.endswith(('.ipk', '.zip')))

    @staticmethod
    def get_file_size(url):
        """Get remote file size"""
        try:
            req = Request(url)
            req.add_header('User-Agent', 'Enigma2-Plugin-Updater')
            with urlopen(req, timeout=10) as response:
                return int(response.headers.get('Content-Length', 0))
        except Exception as e:
            UpdateSystem.log(f"Failed to get file size: {str(e)}", "WARNING")
            return 0

    @staticmethod
    def backup_files():
        try:
            if not os.path.exists(INSTALL_PATH):
                return True

            os.makedirs(BACKUP_PATH, exist_ok=True)
            backed_up = []

            for item in os.listdir(INSTALL_PATH):
                if item.endswith(('.json', '.db', '.conf', '.cfg', '.ini')):
                    src = os.path.join(INSTALL_PATH, item)
                    if os.path.isfile(src):
                        dst = os.path.join(BACKUP_PATH, item)
                        shutil.copy2(src, dst)
                        backed_up.append(item)

            UpdateSystem.log(f"Backed up {len(backed_up)} files: {', '.join(backed_up)}")
            return True
        except Exception as e:
            UpdateSystem.log(f"Backup failed: {traceback.format_exc()}", "ERROR")
            return False

    @staticmethod
    def download_file(url, dest_path, progress_callback=None):
        last_error = None
        socket.setdefaulttimeout(TIMEOUT)

        UpdateSystem.log(f"Starting download from {url} to {dest_path}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = Request(url)
                req.add_header('User-Agent', 'Enigma2-Plugin-Updater')
                req.add_header('Accept', 'application/octet-stream')

                with urlopen(req, timeout=TIMEOUT) as response:
                    if response.getcode() != 200:
                        raise HTTPError(url, response.getcode(),
                                     "Invalid response", response.headers, None)

                    file_size = int(response.headers.get('Content-Length', 0))
                    if file_size == 0:
                        raise ValueError("Empty content")

                    downloaded = 0
                    with open(dest_path, 'wb') as f:
                        while True:
                            chunk = response.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            downloaded += len(chunk)
                            f.write(chunk)
                            if callable(progress_callback):
                                progress = int((downloaded * 100) / file_size)
                                progress_callback(progress, downloaded, file_size)

                    actual_size = os.path.getsize(dest_path)
                    if actual_size != file_size:
                        raise IOError(f"Size mismatch (expected: {file_size}, got: {actual_size})")

                    UpdateSystem.log(f"Download completed successfully (Size: {file_size} bytes)")
                    return True

            except Exception as e:
                last_error = str(e)
                UpdateSystem.log(f"Attempt {attempt} failed: {traceback.format_exc()}", "WARNING")
                if os.path.exists(dest_path):
                    try:
                        os.remove(dest_path)
                    except:
                        pass
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                continue

        UpdateSystem.log(f"All download attempts failed. Last error: {last_error}", "ERROR")
        return False

    @staticmethod
    def install_package(package_path, progress_callback=None):
        try:
            if not os.path.exists(package_path):
                return False, "Package file not found"

            UpdateSystem.log(f"Installing package: {package_path}")

            if callable(progress_callback):
                progress_callback(0, "Starting installation...")

            cmd = f"opkg install --force-overwrite {package_path}"
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            def monitor_installation():
                output_lines = []
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    output_lines.append(line)
                    if "Installing" in line and callable(progress_callback):
                        progress_callback(50, "Installing package...")
                    elif "Configuring" in line and callable(progress_callback):
                        progress_callback(75, "Configuring package...")

                process.wait()

                if callable(progress_callback):
                    progress_callback(100, "Installation complete!")

            monitor_thread = threading.Thread(target=monitor_installation)
            monitor_thread.start()
            monitor_thread.join()

            return_code = process.returncode

            if return_code == 0:
                required_files = ['__init__.py', 'plugin.py']
                missing_files = [
                    f for f in required_files
                    if not os.path.exists(os.path.join(INSTALL_PATH, f))
                ]

                if missing_files:
                    UpdateSystem.log(f"Missing files after installation: {', '.join(missing_files)}", "ERROR")
                    return False, f"Installation verification failed: Missing {', '.join(missing_files)}"

                UpdateSystem.log("Package installed successfully")
                return True, None
            else:
                error_msg = process.stderr.read().strip() or "Unknown opkg error"
                UpdateSystem.log(f"Installation failed with code {return_code}: {error_msg}", "ERROR")
                return False, f"opkg error {return_code}: {error_msg}"

        except Exception as e:
            UpdateSystem.log(f"Installation exception: {traceback.format_exc()}", "ERROR")
            return False, str(e)
        finally:
            if os.path.exists(package_path):
                try:
                    os.remove(package_path)
                    UpdateSystem.log("Temporary package file removed")
                except Exception as e:
                    UpdateSystem.log(f"Failed to remove package file: {str(e)}", "WARNING")

class DownloadScreen(Screen):
    skin = """
    <screen position="center,center" size="600,200" title="Downloading Update" backgroundColor="#2c2f38">
        <widget name="progress" position="20,40" size="560,20" backgroundColor="#6a9dff" borderWidth="2" borderColor="#3a5e89" />
        <widget name="status" position="20,70" size="560,30" font="Regular;22" color="#ffffff" halign="center" />
        <widget name="details" position="20,110" size="560,30" font="Regular;18" color="#f0f0f0" halign="center" />
        <widget name="loading" position="240,150" size="120,30" font="Regular;18" color="#f0f0f0" halign="center">
            <text>{"Downloading..."}</text>
        </widget>
    </screen>
    """

    def __init__(self, session, url, dest_path, callback):
        Screen.__init__(self, session)
        self.session = session
        self.url = url
        self.dest_path = dest_path
        self.callback = callback
        self.active = True
        self.thread = None

        self["progress"] = ProgressBar()
        self["status"] = Label("Preparing download...")
        self["details"] = Label("")

        self["actions"] = ActionMap(
            ["CancelActions", "OkActions", "ColorActions"],
            {
                "cancel": self.cancel,
                "ok": self.ok,
                "red": self.cancel,
                "green": self.ok,
            }, -1
        )

        self.onShown.append(self.start_download)
        self.onClose.append(self.cleanup)
        UpdateSystem.log("DownloadScreen initialized")

    def start_download(self):
        if not UpdateSystem.validate_url(self.url):
            self.error("Invalid download URL")
            return

        file_size = UpdateSystem.get_file_size(self.url)
        if file_size == 0:
            self.error("Could not get file information")
            return

        self["status"].setText("Downloading update...")
        self["details"].setText(f"Size: {file_size//1024} KB")
        self["progress"].setValue(0)

        self.thread = threading.Thread(target=self.perform_download)
        self.thread.start()
        UpdateSystem.log("Download thread started")

    def perform_download(self):
        try:
            UpdateSystem.log(f"Starting download from {self.url}")
            success = UpdateSystem.download_file(
                self.url,
                self.dest_path,
                self.update_progress
            )

            if success and self.active:
                self["status"].setText("Download complete!")
                UpdateSystem.log("Download completed successfully, opening InstallScreen")
                self.session.open(InstallScreen, self.dest_path, self.callback)
                self.close(False)
            elif self.active:
                self.error("Download failed after retries")
        except Exception as e:
            UpdateSystem.log(f"Download error: {traceback.format_exc()}", "ERROR")
            self.error(f"Download error: {str(e)}")

    def update_progress(self, progress, downloaded, total):
        if not self.active:
            return
        self["progress"].setValue(progress)
        self["details"].setText(
            f"{downloaded//1024} KB / {total//1024} KB ({progress}%)"
        )

    def error(self, message):
        UpdateSystem.log(f"Download error: {message}", "ERROR")
        self["status"].setText("Error!")
        self["details"].setText(message)
        self.close(False)

    def ok(self):
        pass

    def cancel(self):
        if self.active:
            UpdateSystem.log("Download cancelled by user", "WARNING")
            self.close(False)

    def cleanup(self):
        self.active = False
        if self.thread and self.thread.is_alive():
            UpdateSystem.log("Waiting for download thread to finish...")
            self.thread.join(1)
        UpdateSystem.log("DownloadScreen cleaned up")

    def close(self, result=True):
        UpdateSystem.log(f"Closing DownloadScreen with result: {result}")
        if self.active:
            if callable(self.callback):
                UpdateSystem.log("Executing download callback")
                self.callback(result)
            self.active = False
        Screen.close(self)

class InstallScreen(Screen):
    skin = """
    <screen position="center,center" size="600,200" title="Installing Update" backgroundColor="#2c2f38">
        <widget name="progress" position="20,40" size="560,20" backgroundColor="#6a9dff" borderWidth="2" borderColor="#3a5e89" />
        <widget name="status" position="20,70" size="560,30" font="Regular;22" color="#ffffff" halign="center" />
        <widget name="details" position="20,110" size="560,30" font="Regular;18" color="#f0f0f0" halign="center" />
        <widget name="loading" position="240,150" size="120,30" font="Regular;18" color="#f0f0f0" halign="center">
            <text>{"Installing..."}</text>
        </widget>
    </screen>
    """

    def __init__(self, session, package_path, callback):
        Screen.__init__(self, session)
        self.session = session
        self.package_path = package_path
        self.callback = callback
        self.active = True
        self.installation_started = False
        self.thread = None

        self["progress"] = ProgressBar()
        self["status"] = Label("Preparing installation...")
        self["details"] = Label("")

        self["actions"] = ActionMap(
            ["CancelActions", "OkActions", "ColorActions"],
            {
                "cancel": self.cancel,
                "ok": self.ok,
                "red": self.cancel,
                "green": self.ok,
            }, -1
        )

        self.onShown.append(self.start_installation)
        self.onClose.append(self.cleanup)
        UpdateSystem.log("InstallScreen initialized")

    def start_installation(self):
        if self.installation_started:
            UpdateSystem.log("Installation already started, skipping.")
            return

        self.installation_started = True
        self["progress"].setValue(0)
        self["status"].setText("Starting installation...")

        self.thread = threading.Thread(target=self.perform_installation)
        self.thread.start()
        UpdateSystem.log("Installation thread started")

    def perform_installation(self):
        try:
            self.update_progress(10, "Preparing update...")
            UpdateSystem.log("Starting update process (without removal)")

            self.update_progress(30, "Updating files...")

            def installation_progress(percent, message):
                self.update_progress(30 + percent // 1.4, message)

            success, error = UpdateSystem.install_package(
                self.package_path,
                installation_progress
            )

            if success and self.active:
                self.update_progress(100, "Installation complete!")
                UpdateSystem.log("Installation completed successfully")

                self.session.openWithCallback(
                    self.restart_confirmation,
                    MessageBox,
                    "Update installed successfully!\n\n"
                    "You need to restart Enigma2 GUI for changes to take effect.\n"
                    "Do you want to restart now?",
                    MessageBox.TYPE_YESNO
                )
            elif self.active:
                raise Exception(error or "Installation failed")

        except Exception as e:
            UpdateSystem.log(f"Installation error: {traceback.format_exc()}", "ERROR")
            self.error(f"Installation error: {str(e)}")

    def update_progress(self, progress, message):
        self["progress"].setValue(progress)
        self["status"].setText(f"{message} ({progress}%)")
        self["details"].setText("")

    def error(self, message):
        UpdateSystem.log(f"Installation failed: {message}", "ERROR")
        self["status"].setText("Installation failed!")
        self["details"].setText(message)
        self.close(False)

    def restart_confirmation(self, answer):
        if answer:
            UpdateSystem.log("User chose to restart Enigma2 (GUI restart)")
            self.restartGUI(answer)
        else:
            UpdateSystem.log("User chose not to restart Enigma2 now")
            self.session.open(
                MessageBox,
                "Please restart Enigma2 GUI later to complete the update.\n"
                "You can do this via the main menu or by pressing\n"
                "POWER button on your remote and selecting 'Restart GUI'",
                MessageBox.TYPE_INFO,
                timeout=7
            )
        self.close(True)

    def restartGUI(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, 3)
            UpdateSystem.log("Enigma2 GUI is restarting...")
        else:
            UpdateSystem.log("Enigma2 GUI restart cancelled.")

    def ok(self):
        pass

    def cancel(self):
        if self.active:
            UpdateSystem.log("Installation cancelled by user", "WARNING")
            self.close(False)

    def cleanup(self):
        self.active = False
        if self.thread and self.thread.is_alive():
            UpdateSystem.log("Waiting for installation thread to finish...")
            self.thread.join(1)
        UpdateSystem.log("InstallScreen cleaned up")

    def close(self, result=True):
        if self.active:
            self.active = False
            UpdateSystem.log(f"Closing InstallScreen with result: {result}")
            if callable(self.callback):
                UpdateSystem.log("Executing installation callback")
                self.callback(result)
        Screen.close(self)

class UpdateManager:

    @staticmethod
    def check_updates(session, manual_check=False):
        """Check for available updates with manual/auto mode"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('User-Agent', 'Enigma2-Plugin-Updater')

            with urlopen(req, timeout=10) as response:
                if response.getcode() != 200:
                    raise HTTPError(url, response.getcode(),
                                 "Invalid response", response.headers, None)

                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', '').replace('v', '')

                if not latest_version:
                    raise ValueError("Invalid version format")

                if latest_version == VERSION:
                    if manual_check:
                        msg = f"You already have the latest version (v{VERSION})"
                        session.open(
                            MessageBox,
                            msg,
                            MessageBox.TYPE_INFO,
                            timeout=5
                        )
                    return False
                else:
                    changelog = data.get('body', 'No changelog available')
                    message = (
                        f"New version v{latest_version} available!\n"
                        f"Current version: v{VERSION}\n\n"
                        f"Changes:\n{changelog}\n\n"
                        "Would you like to update now?"
                    )
                    session.openWithCallback(
                        lambda answer: UpdateManager.start_update(session, data) if answer else None,
                        MessageBox,
                        message,
                        MessageBox.TYPE_YESNO
                    )
                    return True

        except Exception as e:
            error_msg = f"Failed to check updates:\n{str(e)}"
            if manual_check:
                session.open(
                    MessageBox,
                    error_msg,
                    MessageBox.TYPE_ERROR,
                    timeout=10
                )
            return False

    @staticmethod
    def start_update(session, release_data):
        try:
            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith(('.ipk', '.zip')):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                raise Exception("No compatible package found")

            package_path = f"/tmp/{PLUGIN_NAME}_update_{int(time.time())}.ipk"

            def handle_download_result(success):
                if success:
                    session.openWithCallback(
                        lambda result: UpdateManager.install_complete(session, result),
                        InstallScreen,
                        package_path
                    )
                else:
                    session.open(
                        MessageBox,
                        "Download failed!",
                        MessageBox.TYPE_ERROR,
                        timeout=5
                    )

            session.open(
                DownloadScreen,
                download_url,
                package_path,
                handle_download_result
            )

        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            session.open(
                MessageBox,
                error_msg,
                MessageBox.TYPE_ERROR,
                timeout=10
            )

    @staticmethod
    def install_complete(session, success):
        if not success:
            session.open(
                MessageBox,
                "Installation failed!",
                MessageBox.TYPE_ERROR,
                timeout=10
            )
        else:
            session.openWithCallback(
                lambda answer: UpdateManager.handle_restart_confirmation(session, answer),
                MessageBox,
                "Update installed successfully!\n\n"
                "You need to restart Enigma2 GUI for changes to take effect.\n"
                "Do you want to restart now?",
                MessageBox.TYPE_YESNO
            )

    @staticmethod
    def handle_restart_confirmation(session, answer):
        if answer:
            session.open(
                MessageBox,
                "Enigma2 GUI will restart in 3 seconds...",
                MessageBox.TYPE_INFO,
                timeout=3
            )
            reactor.callLater(3, lambda: session.open(TryQuitMainloop, 2))
        else:
            session.open(
                MessageBox,
                "Please restart Enigma2 GUI later to complete the update.\n"
                "You can do this via the main menu or by pressing\n"
                "POWER button on your remote and selecting 'Restart GUI'",
                MessageBox.TYPE_INFO,
                timeout=7
            )