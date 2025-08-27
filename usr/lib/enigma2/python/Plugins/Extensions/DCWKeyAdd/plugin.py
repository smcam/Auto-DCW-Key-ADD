#############################################################################
#  Add Auto DCW Key And ADD Manual BISS Key Plugin for Enigma2 by @Youchie ##
#  Version: 1.0.8                                                          ##
#  Coded by @Youchie SmartCam Tem (c)2025                                  ##
#  Telegram ID: @Youchie                                                   ##
#  Telegram Channel: https://t.me/smartcam_team                            ##
#  github: https://github.com/smcam                                        ##
#  github: https://github.com/Youchie                                      ##
#############################################################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Standby import TryQuitMainloop
from Plugins.Plugin import PluginDescriptor
from enigma import eServiceCenter, iServiceInformation, getDesktop
from Components.ProgressBar import ProgressBar
from Tools.Directories import fileExists
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.ActionMap import ActionMap
from Components.Sources.FrontendStatus import FrontendStatus
import json
import os
import re
import sys
import time
import signal
import subprocess
import traceback

from .updater import UpdateManager, UpdateSystem

PY3 = sys.version_info[0] == 3

try:
    from urllib2 import urlopen, Request, HTTPError
    from urllib import urlencode
except ImportError:
    from urllib.request import urlopen, Request, HTTPError
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

VERSION = "1.0.8"
GITHUB_REPO = "smcam/Auto-DCW-Key-ADD"
PLUGIN_NAME = "DCWKeyAdd"
INSTALL_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd"
VERSION_FILE = os.path.join(INSTALL_PATH, "version.txt")

class DCWKeyAddPlugin(Screen):
    def getSkin(self):
        try:
            desktopSize = getDesktop(0).size()
            if desktopSize.width() > 1280:
                return """
                <screen position="560,105" size="800,900" title="DCW Key Add">
                    <widget name="title_main" position="0,0" size="799,38" font="Regular;28" halign="center" foregroundColor="#00ff00" backgroundColor="#254f74" transparent="0" zPosition="1" />
                    <widget name="title_author" position="0,42" size="799,35" font="Regular;30" halign="center" foregroundColor="#9f1313" backgroundColor="#000000" zPosition="1" transparent="1" />
                    <widget name="channel_name" position="10,126" size="788,32" font="Regular;26" halign="left" transparent="0" valign="center" backgroundColor="#000000" foregroundColor="#00ffc000" />
                    <widget name="channel_details" position="10,162" size="788,32" font="Regular;24" halign="left" transparent="0" valign="center" backgroundColor="#000000" foregroundColor="#0018b9ce" />
                    <widget name="label" position="3,193" size="796,99" font="Regular; 22" zPosition="5" transparent="0" valign="center" backgroundColor="#000000" />
                    <ePixmap position="683,57" size="110,110" zPosition="5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/Image/DCW_Key.png" alphatest="blend" transparent="1" />
                    <widget name="log" position="0,294" size="799,426" font="Regular;23" foregroundColor="#00ffc000" backgroundColor="#254f74" transparent="0" zPosition="1" />
                    <ePixmap name="red" position="15,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/red.png" transparent="1" alphatest="on" />
                    <ePixmap name="green" position="226,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/green.png" transparent="1" alphatest="on" />
                    <ePixmap name="yellow" position="436,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/yellow.png" transparent="1" alphatest="on" />
                    <ePixmap name="blue" position="643,858" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/blue.png" transparent="1" alphatest="on" />
                    <widget name="button_auto" position="212,817" size="169,43" font="Regular;22" transparent="1" zPosition="2" foregroundColor="#00ff00" halign="center" valign="bottom" />
                    <widget name="button_manual" position="422,817" size="169,43" font="Regular;22" transparent="1" zPosition="2" foregroundColor="#ffff00" halign="center" valign="bottom" />
                    <widget name="button_exit" position="0,817" size="169,43" font="Regular;22" transparent="1" zPosition="2" foregroundColor="#ff0000" halign="center" valign="bottom" />
                    <widget name="button_update" position="629,817" size="169,43" font="Regular;22" transparent="1" zPosition="2" foregroundColor="#0000ff" halign="center" valign="bottom" />
                    <widget name="hint_manual" position="0,749" size="799,25" font="Regular;17" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#ffff00" />
                    <widget name="hint_auto" position="0,776" size="799,25" font="Regular;17" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#00ff00" />
                    <widget name="hint_exit" position="0,802" size="799,25" font="Regular;17" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#ff0000" />
                    <widget name="hint_update" position="0,722" size="799,25" font="Regular;17" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#0000ff" />
                    <widget source="session.Title" render="Label" text="SNR" position="214,105" size="40,21" font="Regular;16" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
                    <widget source="session.Title" render="Label" text="AGC" position="214,80" size="40,21" font="Regular;16" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
                    <widget source="session.FrontendStatus" render="Progress" position="255,87" size="290,8" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/agc.png" zPosition="3" transparent="1">
                        <convert type="FrontendInfo">AGC</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Label" position="547,80" size="72,22" backgroundColor="#000000" transparent="1" zPosition="2" foregroundColor="#00d1d1d1" font="Regular;18" halign="left">
                        <convert type="FrontendInfo">AGC</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Progress" position="255,112" size="290,8" zPosition="3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/snron.png" transparent="1">
                        <convert type="FrontendInfo">SNR</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Label" position="547,105" size="72,22" backgroundColor="#000000" transparent="1" zPosition="2" font="Regular;18" halign="left" foregroundColor="#00d1d1d1" valign="center">
                        <convert type="FrontendInfo">SNR</convert>
                    </widget>
                </screen>
                """
            else:
                return """
                <screen position="center,center" size="600,600" title="DCW Key Add">
                    <widget name="title_main" position="0,0" size="599,30" font="Regular;22" halign="center" foregroundColor="#008000" backgroundColor="#254f74" transparent="0" zPosition="1" />
                    <widget name="title_author" position="0,31" size="599,28" font="Regular;24" halign="center" foregroundColor="#9f1313" backgroundColor="#000000" zPosition="1" transparent="1" />
                    <widget name="channel_name" position="0,108" size="599,28" font="Regular;20" halign="left" transparent="0" valign="center" backgroundColor="#000000" foregroundColor="#00ffc000" />
                    <widget name="channel_details" position="0,136" size="599,26" font="Regular;18" halign="left" transparent="0" valign="center" backgroundColor="#000000" foregroundColor="#0018b9ce" />
                    <widget name="label" position="0,162" size="599,67" font="Regular;16" zPosition="5" transparent="0" valign="center" backgroundColor="#000000" />
                    <ePixmap position="514,62" size="80,80" zPosition="5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/Image/DCW_Key_HD.png" alphatest="blend" transparent="1" />
                    <widget name="log" position="0,231" size="599,203" font="Regular;17" foregroundColor="#00ffc000" backgroundColor="#254f74" transparent="0" zPosition="1" />
                    <ePixmap name="red" position="15,560" size="120,35" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/red.png" transparent="1" alphatest="on" />
                    <ePixmap name="green" position="160,560" size="120,35" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/green.png" transparent="1" alphatest="on" />
                    <ePixmap name="yellow" position="320,560" size="120,35" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/yellow.png" transparent="1" alphatest="on" />
                    <ePixmap name="blue" position="465,560" size="120,35" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/buttons/blue.png" transparent="1" alphatest="on" />
                    <widget name="button_auto" position="160,530" size="120,30" font="Regular;16" transparent="1" zPosition="2" foregroundColor="#008000" halign="center" valign="bottom" />
                    <widget name="button_manual" position="320,530" size="120,30" font="Regular;16" transparent="1" zPosition="2" foregroundColor="#ffff00" halign="center" valign="bottom" />
                    <widget name="button_exit" position="15,530" size="120,30" font="Regular;16" transparent="1" zPosition="2" foregroundColor="#ff0000" halign="center" valign="bottom" />
                    <widget name="button_update" position="465,530" size="120,30" font="Regular;16" transparent="1" zPosition="2" foregroundColor="#0000ff" halign="center" valign="bottom" />
                    <widget name="hint_manual" position="0,460" size="599,22" font="Regular;13" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#ffff00" />
                    <widget name="hint_auto" position="0,484" size="599,22" font="Regular;13" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#008000" />
                    <widget name="hint_exit" position="0,508" size="599,22" font="Regular;13" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#ff0000" />
                    <widget name="hint_update" position="0,435" size="599,22" font="Regular;13" halign="center" backgroundColor="#000000" valign="center" transparent="1" foregroundColor="#0000ff" />
                    <widget source="session.Title" render="Label" text="SNR" position="150,80" size="40,18" font="Regular;14" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
                    <widget source="session.Title" render="Label" text="AGC" position="150,60" size="40,18" font="Regular;14" backgroundColor="#08050505" transparent="1" zPosition="2" halign="left" foregroundColor="#ff3737" />
                    <widget source="session.FrontendStatus" render="Progress" position="190,67" size="220,6" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/agc.png" zPosition="3" transparent="1">
                        <convert type="FrontendInfo">AGC</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Label" position="420,60" size="60,18" backgroundColor="#000000" transparent="1" zPosition="2" foregroundColor="#00d1d1d1" font="Regular;16" halign="left">
                        <convert type="FrontendInfo">AGC</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Progress" position="190,87" size="220,6" zPosition="3" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DCWKeyAdd/frontend/snron.png" transparent="1">
                        <convert type="FrontendInfo">SNR</convert>
                    </widget>
                    <widget source="session.FrontendStatus" render="Label" position="420,80" size="60,18" backgroundColor="#000000" transparent="1" zPosition="2" font="Regular;16" halign="left" foregroundColor="#00d1d1d1" valign="center">
                        <convert type="FrontendInfo">SNR</convert>
                    </widget>
                </screen>
                """
        except Exception as e:
            print("[DCWKeyAdd] Error detecting skin resolution:", str(e))
            return """
            <screen position="center,center" size="600,600" title="DCW Key Add">
                <!-- HD skin content as above -->
            </screen>
            """

    def __init__(self, session):
        self.skin = self.getSkin()
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

        self["log"] = Label("")
        self.log_content = []
        self.log_position = 0
        self["DCW_Key"] = Pixmap()
        self["DCW_Key"].hide()

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "green": self.auto_add,
                "yellow": self.manual_add,
                "red": self.close,
                "blue": self.check_for_updates,
                "cancel": self.close,
                "up": self.log_page_up,
                "down": self.log_page_down,
                "left": self.log_page_up,
                "right": self.log_page_down,
            }
        )

        self.onLayoutFinish.append(self.layoutFinished)
        self.onFirstExecBegin.append(self.auto_check_for_updates)
        self.onShow.append(self.update_channel_info)

    def log_page_up(self):
        if self.log_position > 0:
            self.log_position -= 1
            self.update_log_display()

    def log_page_down(self):
        if self.log_position < len(self.log_content) - 1:
            self.log_position += 1
            self.update_log_display()

    def update_log_display(self):
        if self.log_content:
            self["log"].setText(self.log_content[self.log_position])
       
    def layoutFinished(self):
        self["DCW_Key"].show()

    def get_satellite_position(self):
        try:
            service = self.session.nav.getCurrentService()
            if service:
                feinfo = service.frontendInfo()
                if feinfo:
                    frontendData = feinfo.getAll(True)
                    if frontendData:
                        orbital_position = frontendData.get("orbital_position", 0)
                        if orbital_position > 1800:
                            orbital_position = 3600 - orbital_position
                            direction = "W"
                        else:
                            direction = "E"
                        return u"{:.1f}\u00B0{}".format(orbital_position / 10.0, direction)
        except:
            pass
        return "N/A"

    def get_channel_transponder_info(self):
        try:
            service = self.session.nav.getCurrentService()
            if service:
                feinfo = service.frontendInfo()
                if feinfo:
                    frontendData = feinfo.getAll(True)
                    if frontendData:
                        frequency = frontendData.get("frequency", 0)
                        freq_mhz = frequency // 1000 if frequency else 0
                        
                        polarization = "V" if frontendData.get("vertical", 0) else "H"
                        
                        symbol_rate = frontendData.get("symbol_rate", 0)
                        sr_kbps = symbol_rate // 1000 if symbol_rate else 0
                        
                        modulation = frontendData.get("modulation", 0)
                        mod_map = {
                            0: "Auto", 1: "QPSK", 2: "8PSK", 3: "16QAM",
                            4: "32QAM", 5: "64QAM", 6: "128QAM", 7: "256QAM"
                        }
                        mod_str = mod_map.get(modulation, str(modulation))
                        
                        system = frontendData.get("system", 0)
                        sys_str = "DVB-S" if system == 0 else "DVB-S2"
                        
                        return {
                            'frequency': freq_mhz,
                            'polarization': polarization,
                            'symbol_rate': sr_kbps,
                            'modulation': mod_str,
                            'system': sys_str
                        }
        except:
            pass
        return None

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
                            sr_kbps = "{} Ks/s".format(symbol_rate / 1000) if symbol_rate else "N/A"
                            
                            self["channel_name"].setText(channel_name)
                            self["channel_details"].setText(
                                "Freq: {} | Pol: {} | FEC: {} | SR: {}".format(
                                    freq_mhz, polarization, fec_str, sr_kbps
                                )
                            )
                            return
        
        except Exception as e:
            self.log_message("Error getting channel info: {}".format(str(e)))
        
        self["channel_name"].setText("Channel info not available")
        self["channel_details"].setText("")

    def auto_check_for_updates(self):
        try:
            if os.path.exists("/tmp/dcwkeyadd_installed_version"):
                try:
                    with open("/tmp/dcwkeyadd_installed_version", "r") as f:
                        pending_version = f.read().strip()
                        if pending_version == VERSION:
                            os.remove("/tmp/dcwkeyadd_installed_version")
                            return
                except:
                    pass
                
            UpdateManager.check_updates(self.session, manual_check=False)
        except Exception as e:
            self.log_message("Auto-update error: {}".format(str(e)))

    def check_for_updates(self):
        try:
            if not ZIP_SUPPORT:
                self.show_error("zipfile module not available. Please install zip support first.")
                return

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
                self.log_message("New update available")
            else:
                self.log_message("No updates available")

        except Exception as e:
            self.show_error("Update check failed: {}".format(str(e)))

    def log_message(self, message):
        self.log_content.append(message)
        if len(self.log_content) > 10:
            self.log_content.pop(0)
        self.log_position = len(self.log_content) - 1
        full_log = "\n".join(self.log_content)
        self["log"].setText(full_log)

    def get_emulator_info(self):
        try:
            patterns = ["ncam", "oscam"]
            emu_info = {}

            for pid in os.listdir('/proc'):
                if pid.isdigit():
                    cmdline_path = "/proc/{}/cmdline".format(pid)
                    if os.path.exists(cmdline_path):
                        try:
                            with open(cmdline_path, "r") as f:
                                cmdline = f.read().replace('\x00', ' ').strip()
                                for pattern in patterns:
                                    regex = r'\b{}[\w\-.]*\b'.format(pattern)
                                    if re.search(regex, cmdline, re.IGNORECASE):
                                        emu_exe = os.path.basename(cmdline.split()[0])
                                        emu_type = "ncam" if "ncam" in emu_exe.lower() else "oscam"
                                        
                                        config_dir = None
                                        for arg in cmdline.split():
                                            if arg.startswith("-c") or arg.startswith("--config"):
                                                if "=" in arg:
                                                    config_dir = arg.split("=")[1]
                                                else:
                                                    idx = cmdline.split().index(arg)
                                                    if idx + 1 < len(cmdline.split()):
                                                        config_dir = cmdline.split()[idx + 1]
                                                break
                                        
                                        if not config_dir:
                                            config_file = self.find_config("{}.conf".format(emu_type))
                                            if config_file:
                                                config_dir = os.path.dirname(config_file)
                                        
                                        emu_info = {
                                            'name': emu_exe,
                                            'path': cmdline.split()[0],
                                            'type': emu_type,
                                            'config_dir': config_dir or "/etc/tuxbox/config/"
                                        }
                                        return emu_info
                        except Exception as e:
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
        config_dir = emu_info.get('config_dir', "/etc/tuxbox/config/")

        try:
            self.log_message("[INFO] Restarting {} ({}) with config dir: {}".format(
                emu_type, emu_name, config_dir))

            try:
                if PY3:
                    pid = subprocess.check_output(["pidof", emu_name]).decode().strip()
                else:
                    pid = subprocess.check_output(["pidof", emu_name]).strip()

                if pid:
                    try:
                        os.kill(int(pid), signal.SIGHUP)
                        time.sleep(3)
                        if self.get_emulator_info():
                            self.log_message("[SUCCESS] {} restarted with SIGHUP".format(emu_name))
                            return True
                    except:
                        pass
            except:
                pass

            kill_cmd = "killall -9 {}".format(emu_name)
            start_cmd = "{} -b -c {}".format(emu_path, config_dir)

            subprocess.call(kill_cmd, shell=True)
            time.sleep(2)
            subprocess.call(start_cmd, shell=True)
            time.sleep(3)

            if self.get_emulator_info():
                self.log_message("[SUCCESS] {} restarted successfully with config dir: {}".format(
                    emu_name, config_dir))
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
            channel_name = info.getName().replace(" ", "_")
            current_date = time.strftime("%Y-%m-%d")
            current_time = time.strftime("%H:%M")
            
            feinfo = service.frontendInfo()
            frontendData = feinfo.getAll(True)
            orbital_position = frontendData.get("orbital_position", 0)
            if orbital_position > 1800:
                orbital_position = 3600 - orbital_position
                direction = "W"
            else:
                direction = "E"
            sat_pos = u"{:.1f}\u00B0{}".format(orbital_position / 10.0, direction)

            frequency = frontendData.get("frequency", 0)
            freq_mhz = frequency // 1000 if frequency else 0
            polarization = "V" if frontendData.get("vertical", 0) else "H"
            symbol_rate = frontendData.get("symbol_rate", 0)
            sr_kbps = symbol_rate // 1000 if symbol_rate else 0
            
            fec = frontendData.get("fec_inner", 0)
            fec_mapping = {
                0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4",
                4: "5/6", 5: "7/8", 6: "8/9", 7: "3/5",
                8: "4/5", 9: "9/10", 15: "None"
            }
            fec_str = fec_mapping.get(fec, str(fec))
            
            modulation = frontendData.get("modulation", 0)
            mod_map = {
                0: "Auto", 1: "QPSK", 2: "8PSK", 3: "16QAM",
                4: "32QAM", 5: "64QAM", 6: "128QAM", 7: "256QAM"
            }
            mod_str = mod_map.get(modulation, str(modulation))
            
            system = frontendData.get("system", 0)
            system_str = "DVB-S2" if system == 1 else "DVB-S"

            if sid in [None, -1] or vpid in [None, -1]:
                self.show_error("Could not get SID/VPID")
                return

            sid_part = "{:04X}".format(sid)
            vpid_part = "{:04X}".format(vpid)
            biss_line = "F {}{} 00000000 {} ;# {} -({})-{}-{}-{}-{}-{} {}-Added: {} @ {} - By Auto DCW Plugin\n".format(
                sid_part, vpid_part, key,
                channel_name,
                sat_pos,
                freq_mhz,
                polarization,
                sr_kbps,
                fec_str,
                mod_str,
                system_str,
                current_date,
                current_time
            )

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
        config_dir = emu_info.get('config_dir', "/etc/tuxbox/config/")
        config_file = os.path.join(config_dir, "{}.dvbapi".format(emu_type))

        try:
            service = self.session.nav.getCurrentService()
            info = service and service.info()
            channel_name = info.getName().replace(" ", "_") if info else "Unknown"
            current_date = time.strftime("%Y-%m-%d")
            current_time = time.strftime("%H:%M")
            
            feinfo = service.frontendInfo()
            frontendData = feinfo.getAll(True)
            orbital_position = frontendData.get("orbital_position", 0)
            if orbital_position > 1800:
                orbital_position = 3600 - orbital_position
                direction = "W"
            else:
                direction = "E"
            sat_pos = u"{:.1f}\u00B0{}".format(orbital_position / 10.0, direction)

            frequency = frontendData.get("frequency", 0)
            freq_mhz = frequency // 1000 if frequency else 0
            polarization = "V" if frontendData.get("vertical", 0) else "H"
            symbol_rate = frontendData.get("symbol_rate", 0)
            sr_kbps = symbol_rate // 1000 if symbol_rate else 0
            
            fec = frontendData.get("fec_inner", 0)
            fec_mapping = {
                0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4",
                4: "5/6", 5: "7/8", 6: "8/9", 7: "3/5",
                8: "4/5", 9: "9/10", 15: "None"
            }
            fec_str = fec_mapping.get(fec, str(fec))
            
            modulation = frontendData.get("modulation", 0)
            mod_map = {
                0: "Auto", 1: "QPSK", 2: "8PSK", 3: "16QAM",
                4: "32QAM", 5: "64QAM", 6: "128QAM", 7: "256QAM"
            }
            mod_str = mod_map.get(modulation, str(modulation))
            
            system = frontendData.get("system", 0)
            system_str = "DVB-S2" if system == 1 else "DVB-S"

            try:
                sid_int = int(sid, 16) if isinstance(sid, str) and sid else int(sid)
                sid_hex = "{:04X}".format(sid_int)
            except:
                sid_hex = sid

            if caid in ["0000", "00000000", "FFFF", "0001"]:
                
                new_line = "A: ::{} 2600:000000:1FFF ;# {} -({})-{}-{}-{}-{}-{} {}-Added: {} @ {} - Mapping ADD Non-Standard BISS By Auto DCW Plugin".format(
                    sid_hex,
                    channel_name,
                    sat_pos,
                    freq_mhz,
                    polarization,
                    sr_kbps,
                    fec_str,
                    mod_str,
                    system_str,
                    current_date,
                    current_time
                )
                pattern = r"^A:\s*::{}\s".format(sid_hex)
            else:
                try:
                    caid_int = int(caid, 16) if isinstance(caid, str) and caid else int(caid)
                    caid_hex = "{:04X}".format(caid_int)
                except:
                    caid_hex = caid
                
                new_line = "A: {}:000000:{} 2600:000000 ;# {} -({})-{}-{}-{}-{}-{} {}-Added: {} @ {} - Mapping ADD By Auto DCW Plugin".format(
                    caid_hex, sid_hex,
                    channel_name,
                    sat_pos,
                    freq_mhz,
                    polarization,
                    sr_kbps,
                    fec_str,
                    mod_str,
                    system_str,
                    current_date,
                    current_time
                )
                pattern = r"^A:\s*{}:000000:{}".format(caid_hex, sid_hex)

            updated = False
            new_content = []
            file_exists = os.path.exists(config_file)

            if file_exists:
                if PY3:
                    with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.readlines()
                else:
                    with open(config_file, "r") as f:
                        content = f.readlines()
                
                for line in content:
                    if re.match(pattern, line.strip()):
                        updated = True
                        continue
                    if line.strip():
                        new_content.append(line.rstrip())

            if updated:
                self.log_message("Updating existing mapping for CAID: {} SID: {}".format(caid, sid))
            else:
                self.log_message("Adding new mapping for CAID: {} SID: {}".format(caid, sid))

            new_content.append(new_line)

            if PY3:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_content))
                    f.write("\n")
            else:
                with open(config_file, "w") as f:
                    f.write("\n".join(new_content))
                    f.write("\n")

            return True

        except Exception as e:
            self.log_message("[ERROR] write_dvbapi: {}".format(str(e)))
            return False

    def write_softcam(self, line):
        emu_info = self.get_emulator_info()
        if not emu_info:
            return False

        config_dir = emu_info.get('config_dir', "/etc/tuxbox/config/")
        path = os.path.join(config_dir, "SoftCam.Key")

        try:
            sid_vpid = line.split()[1]

            updated = False
            new_content = []
            needs_newline = False

            if os.path.exists(path):
                if PY3:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.readlines()
                else:
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
                self.log_message("Updating existing key for SID/VPID: {}".format(sid_vpid))
            else:
                self.log_message("Adding new key for SID/VPID: {}".format(sid_vpid))

            if needs_newline:
                new_content.append("\n")
            new_content.append(line.rstrip() + "\n")

            if PY3:
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(new_content)
            else:
                with open(path, "w") as f:
                    f.writelines(new_content)

            return True

        except Exception as e:
            self.log_message("[ERROR] write_softcam: {}".format(str(e)))
            return False

    def find_config(self, filename):
        keywords = ['oscam', 'ncam']
        priority_paths = [
            "/etc/tuxbox/config/",
            "/var/tuxbox/config/",
            "/usr/keys/",
            "/var/keys/",
            "/etc/keys/",
            "/usr/local/etc/",
            "/etc/enigma2/"
        ]

        emu_info = self.get_emulator_info()
        if emu_info and emu_info.get('config_dir'):
            test_path = os.path.join(emu_info['config_dir'], filename)
            if os.path.exists(test_path):
                return test_path

        for path in priority_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                return full_path

        search_roots = ["/etc", "/usr", "/var"]
        writable_path = None

        for base in search_roots:
            for root, dirs, files in os.walk(base):
                if any(keyword in root.lower() for keyword in keywords):
                    full_path = os.path.join(root, filename)
                    if filename in files:
                        return full_path
                    elif os.access(root, os.W_OK) and writable_path is None:
                        writable_path = full_path

        if writable_path:
            return writable_path

        self.log_message("[ERROR] {} Not found in any valid OSCam Or NCam path".format(filename))
        return None

    def show_message(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_INFO, timeout=5).show()

    def show_error(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_ERROR, timeout=5).show()

    def show_warning(self, msg):
        MessageBox(self.session, msg, MessageBox.TYPE_WARNING, timeout=5).show()

def check_python_version():
    if sys.version_info[0] == 2 and sys.version_info[1] < 7:
        raise RuntimeError("Python 2.7 or newer required")
    elif sys.version_info[0] == 3 and sys.version_info[1] < 6:
        raise RuntimeError("Python 3.6 or newer recommended")

def main(session, **kwargs):
    try:
        if not UpdateSystem.check_requirements(session):
            msg = "Required packages not installed!\nPlease install manually:\n"
            if sys.version_info[0] == 2:
                msg += "For Python 2: python-zipfile, python-pycurl"
            else:
                msg += "For Python 3: python3-zipfile, python3-pycurl"
            
            session.open(
                MessageBox,
                msg,
                MessageBox.TYPE_ERROR
            )
            return

        session.open(DCWKeyAddPlugin)
    except Exception as e:
        error_msg = "Plugin error: %s" % str(e)
        session.open(
            MessageBox,
            error_msg,
            MessageBox.TYPE_ERROR
        )

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
