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
from Components.ScrollLabel import ScrollLabel
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Standby import TryQuitMainloop
from Plugins.Plugin import PluginDescriptor
from enigma import eServiceCenter, iServiceInformation
from Components.ProgressBar import ProgressBar
from Tools.Directories import fileExists
from urllib.request import Request, urlopen
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.ActionMap import ActionMap
from urllib.error import HTTPError
from Components.Sources.FrontendStatus import FrontendStatus
import json
import os
import re
import sys
import time
import signal
import subprocess

from .updater import UpdateManager, UpdateSystem

PY3 = sys.version_info[0] == 3

try:
    from urllib2 import urlopen, Request, HTTPError
    from urllib import urlencode
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
    from urllib.parse import urlencode

VERSION = "1.0.5"
GITHUB_REPO = "smcam/Auto-DCW-Key-ADD"
PLUGIN_NAME = "DCWKeyAdd"
INSTALL_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd"

class DCWKeyAddPlugin(Screen):
    skin = """
    <screen position="560,105" size="800,900" title="DCW Key Add">
        <widget name="title_main" position="0,0" size="799,38" font="Regular; 28" halign="center" foregroundColor="green" text="Add BISS Key And Auto ADD MAP CAID To DVBAPI" backgroundColor="#254f74" transparent="0" zPosition="1" />
        <widget name="title_author" position="0,42" size="799,35" font="Regular;30" halign="center" foregroundColor="un9f1313" text="By : Youchie" backgroundColor="black" zPosition="1" transparent="1" />
        <widget name="channel_name" position="10,126" size="788,32" font="Regular; 26" halign="left" transparent="0" valign="center" backgroundColor="black" foregroundColor="#00ffc000" />
        <widget name="channel_details" position="10,162" size="788,32" font="Regular; 24" halign="left" transparent="0" valign="center" backgroundColor="black" foregroundColor="#0018b9ce" />
        <widget name="label" position="3,193" size="796,99" font="Regular; 25" zPosition="5" transparent="0" valign="center" backgroundColor="black" />
        <ePixmap position="683,57" size="110,110" zPosition="5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/Image/DCW_Key.png" alphatest="blend" transparent="1" />
        <widget name="log" position="0,294" size="799,426" font="Regular;23" foregroundColor="#00ffc000" transparent="0" scrollbarMode="showOnDemand" scrollbarWidth="7" scrollbarSliderBorderWidth="0" scrollbarKeepGapColor="1" scrollbarGap="5" scrollbarSliderForegroundColor="#FF6600" scrollbarSliderBorderColor="background" zPosition="1" backgroundColor="#254f74" />
        <ePixmap name="red" position="15,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/red.png" transparent="1" alphatest="on" />
        <ePixmap name="green" position="226,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/green.png" transparent="1" alphatest="on" />
        <ePixmap name="yellow" position="436,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/yellow.png" transparent="1" alphatest="on" />
        <ePixmap name="blue" position="643,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/blue.png" transparent="1" alphatest="on" />
        <widget name="button_auto" position="212,817" size="169,43" font="Regular; 22" transparent="1" zPosition="2" foregroundColor="green" halign="center" valign="bottom" />
        <widget name="button_manual" position="422,817" size="169,43" font="Regular; 22" transparent="1" zPosition="2" foregroundColor="yellow" halign="center" valign="bottom" />
        <widget name="button_exit" position="0,817" size="169,43" font="Regular; 22" transparent="1" zPosition="2" foregroundColor="red" halign="center" valign="bottom" />
        <widget name="button_update" position="629,817" size="169,43" font="Regular; 22" transparent="1" zPosition="2" foregroundColor="blue" halign="center" valign="bottom" />
        <widget name="hint_manual" position="0,749" size="799,25" font="Regular; 17" halign="center" backgroundColor="black" valign="center" transparent="1" foregroundColor="yellow" />
        <widget name="hint_auto" position="0,776" size="799,25" font="Regular; 17" halign="center" backgroundColor="black" valign="center" transparent="1" foregroundColor="green" />
        <widget name="hint_exit" position="0,802" size="799,25" font="Regular; 17" halign="center" backgroundColor="black" valign="center" transparent="1" foregroundColor="red" />
        <widget name="hint_update" position="0,722" size="799,25" font="Regular; 17" halign="center" backgroundColor="black" valign="center" transparent="1" foregroundColor="blue" />
        <eLabel text="SNR" position="214,105" size="40,21" font="Regular; 16" borderWidth="1" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
        <eLabel text="AGC" position="214,80" size="40,21" font="Regular; 16" borderWidth="1" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
        <eLabel backgroundColor="#33333a" position="255,113" size="290,6" foregroundColor="#33333a" />
        <widget source="session.FrontendStatus" render="Progress" position="255,87" size="290,8" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/agc.png" zPosition="3" transparent="1">
        <convert type="FrontendInfo">AGC</convert>
        </widget>
        <widget source="session.FrontendStatus" render="Label" borderWidth="1" position="547,80" size="72,22" backgroundColor="black" transparent="1" zPosition="2" foregroundColor="#00d1d1d1" font="Regular; 18" halign="left">
        <convert type="FrontendInfo">AGC</convert>
        </widget>
        <eLabel backgroundColor="#33333a" position="255,88" size="290,6" foregroundColor="#33333a" />
        <widget source="session.FrontendStatus" render="Progress" position="255,112" size="290,8" zPosition="3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/snron.png" transparent="1">
        <convert type="FrontendInfo">SNR</convert>
        </widget>
        <widget source="session.FrontendStatus" render="Label" position="547,105" size="72,22" borderWidth="1" backgroundColor="black" transparent="1" zPosition="2" font="Regular; 18" halign="left" foregroundColor="#00d1d1d1" valign="center">
        <convert type="FrontendInfo">SNR</convert>
        </widget>
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle("Auto DCW Key Add v{}".format(VERSION))

        self["channel_name"] = Label("")
        self["channel_details"] = Label("")
        
        self["frontendStatus"] = FrontendStatus()     
        
        self["title_main"] = Label("Add BISS Key And Auto ADD MAP CAID To DVBAPI")
        self["title_author"] = Label("By : Youchie")
        self["label"] = Label("Select Key Addition Method:")

        self["button_auto"] = Button("Auto (DVBAPI)")
        self["button_manual"] = Button("Manual (BISS)")
        self["button_exit"] = Button("Exit")
        self["button_update"] = Button("Check Update")

        self["hint_auto"] = Label("Press GREEN Key For Auto (DVBAPI): Only use this if the CW doesn't change (Freeze CW)")
        self["hint_manual"] = Label("Press YELLOW Key For ADD Manual BISS Key")
        self["hint_update"] = Label("Press BLUE Key To Check Update")
        self["hint_exit"] = Label("Press RED Key To Exit Plugin")

        self["log"] = ScrollLabel("")
        self["DCW_Key"] = Pixmap()
        self["DCW_Key"].hide()

        self["log"].scrollUp = lambda: self["log"].pageUp()
        self["log"].scrollDown = lambda: self["log"].pageDown()

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "green": self.auto_add,
                "yellow": self.manual_add,
                "red": self.close,
                "blue": self.check_for_updates,
                "cancel": self.close,
                "up": self["log"].scrollUp,
                "down": self["log"].scrollDown,
                "left": self["log"].scrollUp,
                "right": self["log"].scrollDown
            }
        )

        self.onLayoutFinish.append(self.layoutFinished)
        self.onFirstExecBegin.append(self.auto_check_for_updates)
        self.onShow.append(self.update_channel_info)

    def layoutFinished(self):
        self["DCW_Key"].show()

    def update_channel_info(self):
        try:
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    channel_name = info.getName()
                    feinfo = service.frontendInfo()
                    if feinfo:
                        frontendData = feinfo.getAll(True)
                        if frontendData:
                            frequency = frontendData.get("frequency", 0)
                            freq_mhz = "{:.3f} MHz".format(frequency / 1000) if frequency else "N/A"
                            
                            polarization = "V" if frontendData.get("vertical", 0) else "H"
                            
                            fec = frontendData.get("fec_inner", 0)
                            fec_mapping = {
                                0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4",
                                4: "5/6", 5: "7/8", 6: "8/9", 7: "3/5",
                                8: "4/5", 9: "9/10", 15: "None"
                            }
                            fec_str = fec_mapping.get(fec, str(fec))
                            
                            symbol_rate = frontendData.get("symbol_rate", 0)
                            sr_kbps = "{} Ks/s".format(symbol_rate // 1000) if symbol_rate else "N/A"
                            
                            self["channel_name"].setText(channel_name)
                            self["channel_details"].setText(
                                f"Freq: {freq_mhz} | Pol: {polarization} | FEC: {fec_str} | SR: {sr_kbps}"
                            )
                            return
        
        except Exception as e:
            self.log_message(f"Error getting channel info: {str(e)}")
        
        self["channel_name"].setText("Channel info not available")
        self["channel_details"].setText("")

    def auto_check_for_updates(self):
        try:
            if os.path.exists("/tmp/dcwkeyadd_installed_version"):
                return
                
            UpdateManager.check_updates(self.session, manual_check=False)
        except Exception as e:
            self.log_message(f"Auto-update error: {str(e)}")

    def check_for_updates(self):
        try:
            if os.path.exists("/tmp/dcwkeyadd_installed_version"):
                with open("/tmp/dcwkeyadd_installed_version", "r") as f:
                    pending_version = f.read().strip()
                    if pending_version == VERSION:
                        self.session.open(
                            MessageBox,
                            "Update already installed!\nPlease Restart Enigma2 to Complete Update.",
                            MessageBox.TYPE_INFO,
                            timeout=5
                        )
                        return

            if UpdateManager.check_updates(self.session, manual_check=True):
                self.log_message("New Update available")
            else:
                self.log_message("No updates available")

        except Exception as e:
            self.show_error(f"Update check failed: {str(e)}")

    def log_message(self, message):
        current_text = self["log"].getText()
        new_text = "{}\n{}".format(current_text, message)
        self["log"].setText(new_text)
        self["log"].lastPage()

    def get_emulator_info(self):
        try:
            patterns = ["ncam", "oscam"]
            emu_info = {}

            for pattern in patterns:
                try:
                    if PY3:
                        output = subprocess.check_output(["pgrep", "-f", pattern]).decode().strip()
                    else:
                        output = subprocess.check_output(["pgrep", "-f", pattern]).strip()

                    if output:
                        pids = output.split('\n')
                        for pid in pids:
                            cmdline_path = "/proc/{}/cmdline".format(pid)
                            if os.path.exists(cmdline_path):
                                with open(cmdline_path, "r") as f:
                                    cmdline = f.read().replace('\x00', ' ').strip()
                                    if pattern in cmdline.lower():
                                        emu_name = os.path.basename(cmdline.split()[0])
                                        emu_type = "ncam" if "ncam" in emu_name.lower() else "oscam"
                                        emu_info = {
                                            'name': emu_name,
                                            'path': cmdline.split()[0],
                                            'type': emu_type
                                        }
                                        return emu_info
                except subprocess.CalledProcessError:
                    continue

            return None
        except Exception as e:
            self.log_message("[ERROR] Emulator detection failed: {}".format(str(e)))
            return None

    def restart_emulator(self):
        emu_info = self.get_emulator_info()
        if not emu_info:
            self.log_message("[ERROR] No running emulator found")
            return False

        emu_name = emu_info['name']
        emu_path = emu_info['path']
        emu_type = emu_info['type']

        try:
            self.log_message("[INFO] Restarting {} ({})...".format(emu_type, emu_name))

            try:
                if PY3:
                    pid = subprocess.check_output(["pidof", emu_name]).decode().strip()
                else:
                    pid = subprocess.check_output(["pidof", emu_name]).strip()

                if pid:
                    os.kill(int(pid), signal.SIGHUP)
                    time.sleep(3)
                    if self.get_emulator_info():
                        self.log_message("[SUCCESS] {} restarted with SIGHUP".format(emu_name))
                        return True
            except:
                pass

            kill_cmd = "killall -9 {}".format(emu_name)
            start_cmd = "{} -b".format(emu_path)

            subprocess.call(kill_cmd, shell=True)
            time.sleep(2)
            subprocess.call(start_cmd, shell=True)
            time.sleep(3)

            if self.get_emulator_info():
                self.log_message("[SUCCESS] {} restarted successfully".format(emu_name))
                return True
            
            self.log_message("[ERROR] {} still not running".format(emu_name))
            return False

        except Exception as e:
            self.log_message("[EXCEPTION] Restart failed: {}".format(str(e)))
            return False

    def auto_add(self):
        self["label"].setText("Checking channel encryption...")
        self.log_message("Checking channel encryption...")
        self.update_channel_info()
        
        try:
            service = self.session.nav.getCurrentService()
            if service is None:
                self.show_error("No active service!\nPlease tune to a channel first.")
                return

            info = service.info()
            if info is None:
                self.show_error("Could not get service info")
                return

            caids = info.getInfoObject(iServiceInformation.sCAIDs)
            if not caids:
                caid = info.getInfo(iServiceInformation.sCAID)
                if caid in [None, -1]:
                    self.show_error("Channel is not encrypted\nor CAID not available")
                    return
                caids = [caid]

            sid = info.getInfo(iServiceInformation.sSID)
            if sid in [None, -1]:
                self.show_error("Could not get SID")
                return

            caid = "{:04X}".format(caids[0])
            sid = "{:04X}".format(sid)

            self["label"].setText("Found encrypted channel\nCAID: {}\nSID: {}".format(caid, sid))
            self.log_message("Found encrypted channel\nCAID: {}\nSID: {}".format(caid, sid))

            if self.write_dvbapi(caid, sid):
                if self.restart_emulator():
                    self.show_message("Key added successfully!\nCAID: {}\nSID: {}".format(caid, sid))
                else:
                    self.show_warning("Key added but emulator not restarted")
            else:
                self.show_error("Failed to write to dvbapi file")

        except Exception as e:
            self.show_error("Error in auto_add: {}".format(str(e)))
            self.log_message("Error in auto_add: {}".format(str(e)))

    def manual_add(self):
        try:
            self.session.openWithCallback(self.keyboard_callback,
                VirtualKeyBoard,
                title="Enter EXACTLY 16 character BISS Key (0-9,A-F):",
                text="")
        except Exception as e:
            self.show_error("Failed to open keyboard: {}".format(str(e)))
            self.log_message("Failed to open keyboard: {}".format(str(e)))

    def keyboard_callback(self, key):
        if key is None:
            return

        key = key.upper().strip()
        key = key.replace(" ", "")

        if len(key) != 16:
            error_msg = ""
            if len(key) < 16:
                error_msg = "Key is too short! ({}/16 chars)\nNeed {} more characters.".format(len(key), 16-len(key))
            else:
                error_msg = "Key is too long! ({}/16 chars)\nRemove {} characters.".format(len(key), len(key)-16)

            self.show_error(error_msg)
            self.log_message("Invalid key length: {}".format(error_msg))

            self.session.openWithCallback(self.keyboard_callback,
                VirtualKeyBoard,
                title="Enter EXACTLY 16 chars (0-9,A-F):\n" + error_msg,
                text=key)
            return

        if not all(c in "0123456789ABCDEF" for c in key):
            self.show_error("Invalid characters!\nOnly 0-9 and A-F are allowed.")
            self.log_message("Invalid characters in key: {}".format(key))

            self.session.openWithCallback(self.keyboard_callback,
                VirtualKeyBoard,
                title="Enter 16 HEX chars (0-9,A-F):\nInvalid characters!",
                text=key)
            return

        self["label"].setText("Processing BISS key...")
        self.log_message("Valid BISS key entered: {}".format(key))

        try:
            service = self.session.nav.getCurrentService()
            info = service and service.info()
            if not info:
                self.show_error("Could not get service info")
                return

            sid = info.getInfo(iServiceInformation.sSID)
            vpid = info.getInfo(iServiceInformation.sVideoPID)

            if sid in [None, -1] or vpid in [None, -1]:
                self.show_error("Could not get SID/VPID")
                return

            sid_part = "{:04X}".format(sid)
            vpid_part = "{:04X}".format(vpid)
            biss_line = "F {}{} 00000000 {} ;# Key ADD By Auto DCW Plugin (@Youchie)\n".format(sid_part, vpid_part, key)

            if self.write_softcam(biss_line):
                if self.restart_emulator():
                    self.show_message("BISS key added!\nSID: {}\nVPID: {}".format(sid_part, vpid_part))
                else:
                    self.show_warning("Key added but emulator not restarted")
            else:
                self.show_error("Failed to write to SoftCam.Key")

        except Exception as e:
            self.show_error("Error processing key: {}".format(str(e)))
            self.log_message("Error in keyboard_callback: {}".format(str(e)))

    def write_dvbapi(self, caid, sid):
        emu_info = self.get_emulator_info()
        if not emu_info:
            return False

        emu_type = emu_info['type']
        config_file = "{}.dvbapi".format(emu_type)

        try:
            path = self.find_config(config_file)
            if not path:
                return False

            new_line = "A: {}:000000:{} 2600:000000 ;# ADD By Auto DCW Plugin (@Youchie)\n".format(caid, sid)

            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read()
                    if new_line.strip() in content:
                        return True
                    needs_newline = not content.endswith('\n')
            else:
                needs_newline = False

            with open(path, "a") as f:
                if needs_newline:
                    f.write("\n")
                f.write(new_line)
            return True
        except Exception as e:
            self.log_message("[ERROR] write_dvbapi: {}".format(str(e)))
            return False

    def write_softcam(self, line):
        try:
            path = self.find_config("SoftCam.Key")
            if not path:
                return False

            sid_vpid = line.split()[1]

            updated = False
            new_content = []
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.readlines()
                    needs_newline = not content[-1].endswith('\n') if content else False
                    for l in content:
                        if l.strip().startswith("F") and sid_vpid in l:
                            updated = True
                            continue
                        if l.strip():
                            new_content.append(l.rstrip() + "\n")

            if updated:
                self.log_message(f"Updating existing key for SID/VPID: {sid_vpid}")
            else:
                self.log_message(f"Adding new key for SID/VPID: {sid_vpid}")

            if needs_newline:
                new_content.append("\n")
            new_content.append(line.rstrip() + "\n")

            with open(path, "w") as f:
                f.writelines(new_content)

            return True
        except Exception as e:
            self.log_message("[ERROR] write_softcam: {}".format(str(e)))
            return False

    def find_config(self, filename):
        paths = [
            "/etc/tuxbox/config/",
            "/var/keys/",
            "/usr/keys/",
            "/etc/keys/",
            "/usr/local/etc/",
            "/etc/enigma2/"
        ]
        for p in paths:
            full_path = os.path.join(p, filename)
            if os.path.exists(full_path):
                return full_path
            if os.access(p, os.W_OK):
                return full_path
        self.log_message("[ERROR] {} not found in any path".format(filename))
        return None

    def show_message(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_INFO, timeout=5).show()

    def show_error(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_ERROR, timeout=5).show()

    def show_warning(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_WARNING, timeout=5).show()

def main(session, **kwargs):
    session.open(DCWKeyAddPlugin)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Auto DCW Key ADD",
            description="Auto DCW Key And ADD Manual BISS Key v{}".format(VERSION),
            where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU],
            fnc=main,
            icon="plugin.png"
        )
    ]