#############################################################################
#  Add Auto DCW Key And ADD Manual BISS Key Plugin for Enigma2 by @Youchie ##
#  Version: 1.0.7                                                          ##
#  Coded by @Youchie SmartCam Tem (c)2025                                  ##
#  Telegram ID: @Youchie                                                   ##
#  Telegram Channel: https://t.me/smartcam_team                            ##
#  github: https://github.com/smcam                                        ##
#  github: https://github.com/Youchie                                      ##
#############################################################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from Screens.Screen import Screen
from Components.ProgressBar import ProgressBar
from Components.Label import Label
from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
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

def check_package_manager():
    try:
        if subprocess.call(['which', 'opkg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            return 'opkg'
        elif subprocess.call(['which', 'dpkg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
            return 'dpkg'
        return None
    except:
        return None

def install_required_packages(session=None):
    try:
        import zipfile
        if PY3:
            from urllib.request import urlopen
        else:
            from urllib2 import urlopen
        return True
    except ImportError:
        try:
            package_manager = check_package_manager()
            if not package_manager:
                if session:
                    session.open(MessageBox, "No supported package manager found!", MessageBox.TYPE_ERROR)
                return False

            packages = []
            if PY3:
                packages.extend(['python3-zipfile', 'python3-pycurl'])
            else:
                packages.extend(['python-zipfile', 'python-pycurl'])

            for pkg in packages:
                if package_manager == 'opkg':
                    cmd = ['opkg', 'install', pkg]
                else:
                    cmd = ['apt-get', 'install', '-y', pkg]

                subprocess.call(cmd)

            try:
                import zipfile
                if PY3:
                    from urllib.request import urlopen
                else:
                    from urllib2 import urlopen
                return True
            except ImportError:
                if session:
                    session.open(MessageBox, "Failed to install {}!".format(pkg), MessageBox.TYPE_ERROR)
                return False

        except Exception as e:
            if session:
                session.open(MessageBox, "Installation error: {}".format(e), MessageBox.TYPE_ERROR)
            return False

try:
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urllib import urlencode
except ImportError:
    from urllib.request import urlopen, Request, HTTPError, URLError
    from urllib.parse import urlencode

try:
    from httplib import HTTPException
except ImportError:
    from http.client import HTTPException

try:
    import zipfile
    ZIP_SUPPORT = True
except ImportError:
    ZIP_SUPPORT = False

VERSION = "1.0.7"
GITHUB_REPO = "smcam/Auto-DCW-Key-ADD"
PLUGIN_NAME = "DCWKeyAdd"
INSTALL_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd"
VERSION_FILE = os.path.join(INSTALL_PATH, "version.txt")
BACKUP_PATH = "/tmp/dcwkeyadd_backup"
LOG_FILE = "/tmp/dcwkeyadd_install.log"
MAX_RETRIES = 3
TIMEOUT = 30
CHUNK_SIZE = 8192

class UpdateSystem:
    @staticmethod
    def check_requirements(session=None):
        return install_required_packages(session)

    @staticmethod
    def safe_path_join(*paths):
        path = os.path.join(*paths)
        return os.path.normpath(path)

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
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = "[{}] {}: {}".format(timestamp, level, message)
            
            if not PY3:
                log_entry = log_entry.encode('utf-8', 'replace')
            
            print(log_entry)
            
            for log_file in UpdateSystem.get_log_locations():
                try:
                    log_dir = os.path.dirname(log_file)
                    if log_dir and not os.path.exists(log_dir):
                        os.makedirs(log_dir)
                    
                    mode = "ab" if not PY3 else "a"
                    with open(log_file, mode) as f:
                        f.write(log_entry + (b"\n" if not PY3 else "\n"))
                        f.flush()
                    break
                except (IOError, OSError) as e:
                    continue
        except Exception as e:
            print("CRITICAL LOGGING FAILURE: {}".format(str(e)))

    @staticmethod
    def validate_url(url):
        try:
            if PY3:
                return (isinstance(url, str) and
                        url.startswith('https://github.com/') and
                        url.endswith('.zip'))
            else:
                return (isinstance(url, (str, unicode)) and
                        url.startswith('https://github.com/') and
                        url.endswith('.zip'))
        except Exception as e:
            UpdateSystem.log("URL validation error: {}".format(str(e)), "ERROR")
            return False

    @staticmethod
    def get_file_size(url):
        try:
            if not PY3 and isinstance(url, unicode):
                url = url.encode('utf-8')

            req = Request(url)
            req.add_header('User-Agent', 'Enigma2-Plugin-Updater')
            
            if PY3:
                with urlopen(req, timeout=10) as response:
                    return int(response.headers.get('Content-Length', 0))
            else:
                response = urlopen(req, timeout=10)
                return int(response.info().get('Content-Length', 0))
        except Exception as e:
            UpdateSystem.log("Failed to get file size: {}".format(str(e)), "WARNING")
            return 0

    @staticmethod
    def backup_files():
        try:
            if not os.path.exists(INSTALL_PATH):
                return True

            try:
                os.makedirs(BACKUP_PATH)
            except OSError as e:
                if e.errno != 17:
                    raise

            backed_up = []

            for item in os.listdir(INSTALL_PATH):
                if item.endswith(('.json', '.db', '.conf', '.cfg', '.ini')):
                    src = UpdateSystem.safe_path_join(INSTALL_PATH, item)
                    if os.path.isfile(src):
                        dst = UpdateSystem.safe_path_join(BACKUP_PATH, item)
                        shutil.copy2(src, dst)
                        backed_up.append(item)

            UpdateSystem.log("Backed up {} files: {}".format(len(backed_up), ', '.join(backed_up)))
            return True
        except Exception as e:
            UpdateSystem.log("Backup failed: {}".format(traceback.format_exc()), "ERROR")
            return False

    @staticmethod
    def download_file(url, dest_path, progress_callback=None):
        last_error = None
        socket.setdefaulttimeout(TIMEOUT)

        if not PY3 and isinstance(url, unicode):
            url = url.encode('utf-8')

        UpdateSystem.log("Starting download from {} to {}".format(url, dest_path))

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = Request(url)
                req.add_header('User-Agent', 'Enigma2-Plugin-Updater')
                req.add_header('Accept', 'application/octet-stream')

                response = urlopen(req, timeout=TIMEOUT)
                
                if PY3:
                    file_size = int(response.headers.get('Content-Length', 0))
                else:
                    file_size = int(response.info().get('Content-Length', 0))
                
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
                    raise IOError("Size mismatch (expected: {}, got: {})".format(file_size, actual_size))

                UpdateSystem.log("Download completed successfully (Size: {} bytes)".format(file_size))
                return True

            except Exception as e:
                last_error = str(e)
                UpdateSystem.log("Attempt {} failed: {}".format(attempt, traceback.format_exc()), "WARNING")
                if os.path.exists(dest_path):
                    try:
                        os.remove(dest_path)
                    except:
                        pass
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                continue

        UpdateSystem.log("All download attempts failed. Last error: {}".format(last_error), "ERROR")
        return False

    @staticmethod
    def extract_zip(zip_path, dest_path, progress_callback=None):
        try:
            if not ZIP_SUPPORT:
                return False, "zipfile module not available"

            if not os.path.exists(zip_path):
                return False, "ZIP file not found"

            UpdateSystem.log("Extracting {} to {}".format(zip_path, dest_path))

            if callable(progress_callback):
                progress_callback(0, "Starting extraction...")

            try:
                os.makedirs(dest_path)
            except OSError as e:
                if e.errno != 17:
                    raise

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)
            
                for i, file_info in enumerate(file_list):
                    try:
                        zip_ref.extract(file_info, dest_path)
                    
                        if callable(progress_callback):
                            progress = int((i + 1) * 100 / total_files)
                            progress_callback(progress, "Extracting: {}".format(file_info.filename))
                    except Exception as e:
                        UpdateSystem.log("Failed to extract {}: {}".format(file_info.filename, str(e)), "WARNING")
                        continue

            UpdateSystem.log("Extraction completed successfully")
            return True, None

        except Exception as e:
            UpdateSystem.log("Extraction failed: {}".format(traceback.format_exc()), "ERROR")
            return False, str(e)

    @staticmethod
    def install_from_zip(zip_path, progress_callback=None):
        try:
            if not os.path.exists(zip_path):
                return False, "ZIP file not found"

            UpdateSystem.log("Installing from ZIP: {}".format(zip_path))

            temp_dir = "/tmp/dcwkeyadd_update_extract"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            try:
                os.makedirs(temp_dir)
            except OSError as e:
                if e.errno != 17:
                    raise

            def extraction_progress(percent, message):
                if callable(progress_callback):
                    progress_callback(percent // 2, message)

            success, error = UpdateSystem.extract_zip(zip_path, temp_dir, extraction_progress)
            if not success:
                return False, error

            plugin_content_dir = None
            for root, dirs, files in os.walk(temp_dir):
                if 'plugin.py' in files and '__init__.py' in files:
                    plugin_content_dir = root
                    break

            if not plugin_content_dir:
                return False, "Plugin files not found in ZIP"

            if not UpdateSystem.backup_files():
                return False, "Backup failed"

            try:
                for item in os.listdir(plugin_content_dir):
                    src = os.path.join(plugin_content_dir, item)
                    dest = os.path.join(INSTALL_PATH, item)

                    if os.path.isdir(src):
                        if PY3:
                            shutil.copytree(src, dest, dirs_exist_ok=True)
                        else:
                            if os.path.exists(dest):
                                shutil.rmtree(dest)
                            shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
                
                UpdateSystem.log("Files copied successfully")
            except Exception as e:
                return False, "File copy failed: {}".format(str(e))

            if os.path.exists(BACKUP_PATH):
                for item in os.listdir(BACKUP_PATH):
                    src = os.path.join(BACKUP_PATH, item)
                    dest = os.path.join(INSTALL_PATH, item)
                    shutil.copy2(src, dest)
                UpdateSystem.log("Config files restored")

            return True, None

        except Exception as e:
            UpdateSystem.log("Installation failed: {}".format(traceback.format_exc()), "ERROR")
            return False, str(e)
        finally:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception as e:
                UpdateSystem.log("Cleanup error: {}".format(str(e)), "WARNING")

class DownloadScreen(Screen):
    skin = """
    <screen position="center,center" size="600,200" title="Downloading Update" backgroundColor="#2c2f38">
        <widget name="progress" position="20,40" size="560,20" backgroundColor="#6a9dff" />
        <widget name="status" position="20,70" size="560,30" font="Regular;22" foregroundColor="#ffffff" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
        <widget name="details" position="20,110" size="560,30" font="Regular;18" foregroundColor="#f0f0f0" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
        <widget name="loading" position="240,150" size="120,30" font="Regular;18" foregroundColor="#f0f0f0" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
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
        if not ZIP_SUPPORT:
            self.error("zipfile module not available. Please install zip support first.")
            return

        if not UpdateSystem.validate_url(self.url):
            self.error("Invalid download URL")
            return

        file_size = UpdateSystem.get_file_size(self.url)
        if file_size == 0:
            self.error("Could not get file information")
            return

        self["status"].setText("Downloading update...")
        self["details"].setText("Size: {} KB".format(file_size//1024))
        self["progress"].setValue(0)

        self.thread = threading.Thread(target=self.perform_download)
        self.thread.start()
        UpdateSystem.log("Download thread started")

    def perform_download(self):
        try:
            UpdateSystem.log("Starting download from {}".format(self.url))
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
            UpdateSystem.log("Download error: {}".format(traceback.format_exc()), "ERROR")
            self.error("Download error: {}".format(str(e)))

    def update_progress(self, progress, downloaded, total):
        if not self.active:
            return
        self["progress"].setValue(progress)
        self["details"].setText(
            "{} KB / {} KB ({}%)".format(downloaded//1024, total//1024, progress)
        )

    def error(self, message):
        UpdateSystem.log("Download error: {}".format(message), "ERROR")
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
        UpdateSystem.log("Closing DownloadScreen with result: {}".format(result))
        if self.active:
            if callable(self.callback):
                UpdateSystem.log("Executing download callback")
                self.callback(result)
            self.active = False
        Screen.close(self)

class InstallScreen(Screen):
    skin = """
    <screen position="center,center" size="600,200" title="Installing Update" backgroundColor="#2c2f38">
        <widget name="progress" position="20,40" size="560,20" backgroundColor="#6a9dff" />
        <widget name="status" position="20,70" size="560,30" font="Regular;22" foregroundColor="#ffffff" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
        <widget name="details" position="20,110" size="560,30" font="Regular;18" foregroundColor="#f0f0f0" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
        <widget name="loading" position="240,150" size="120,30" font="Regular;18" foregroundColor="#f0f0f0" halign="center" valign="center" backgroundColor="transparent" transparent="1" />
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
        if not ZIP_SUPPORT:
            self.error("zipfile module not available. Please install zip support first.")
            return

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
            self.update_progress(10, "Preparing ZIP update...")
            UpdateSystem.log("Starting ZIP installation process")

            def installation_progress(percent, message):
                self.update_progress(percent, message)

            success, error = UpdateSystem.install_from_zip(
                self.package_path,
                installation_progress
            )

            if success and self.active:
                self.update_progress(100, "Installation complete!")
                UpdateSystem.log("ZIP installation completed successfully")

                try:
                    with open(VERSION_FILE, "w") as f:
                        f.write(VERSION)
                    UpdateSystem.log("Version file updated: {}".format(VERSION))
                except Exception as e:
                    UpdateSystem.log("Failed to write version file: {}".format(str(e)), "WARNING")

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
            UpdateSystem.log("Installation error: {}".format(traceback.format_exc()), "ERROR")
            self.error("Installation error: {}".format(str(e)))

    def update_progress(self, progress, message):
        self["progress"].setValue(progress)
        self["status"].setText("{} ({}%)".format(message, progress))
        self["details"].setText("")

    def error(self, message):
        UpdateSystem.log("Installation failed: {}".format(message), "ERROR")
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
            UpdateSystem.log("Closing InstallScreen with result: {}".format(result))
            if callable(self.callback):
                UpdateSystem.log("Executing installation callback")
                self.callback(result)
        Screen.close(self)

class UpdateManager:

    @staticmethod
    def check_updates(session, manual_check=False):
        try:
            if not ZIP_SUPPORT:
                session.open(
                    MessageBox,
                    "zipfile module not available. Please install zip support first.",
                    MessageBox.TYPE_ERROR,
                    timeout=10
                )
                return False

            url = "https://api.github.com/repos/{}/releases/latest".format(GITHUB_REPO)
            req = Request(url)
            req.add_header('Accept', 'application/vnd.github.v3+json')
            req.add_header('User-Agent', 'Enigma2-Plugin-Updater')

            response = urlopen(req, timeout=10)
        
            if PY3:
                data = json.loads(response.read().decode('utf-8'))
            else:
                data = json.loads(response.read())

            latest_version = data.get('tag_name', '').replace('v', '')

            if not latest_version:
                raise ValueError("Invalid version format")

            if latest_version == VERSION:
                if manual_check:
                    msg = "You already have the latest version (v{})".format(VERSION)
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
                    "New version v{} available!\n"
                    "Current version: v{}\n\n"
                    "Changes:\n{}\n\n"
                    "Would you like to update now?"
                ).format(latest_version, VERSION, changelog)
                
                session.openWithCallback(
                    lambda answer: UpdateManager.start_update(session, data) if answer else None,
                    MessageBox,
                    message,
                    MessageBox.TYPE_YESNO
                )
                return True

        except Exception as e:
            error_msg = "Failed to check updates:\n{}".format(str(e))
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
            if not ZIP_SUPPORT:
                session.open(
                    MessageBox,
                    "zipfile module not available. Please install zip support first.",
                    MessageBox.TYPE_ERROR,
                    timeout=10
                )
                return

            download_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break

            if not download_url:
                raise Exception("No ZIP package found")

            package_path = "/tmp/{}_update_{}.zip".format(PLUGIN_NAME, int(time.time()))

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
            error_msg = "Update failed: {}".format(str(e))
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
            try:
                if os.path.exists("/tmp/dcwkeyadd_installed_version"):
                    os.remove("/tmp/dcwkeyadd_installed_version")
            except:
                pass
            
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