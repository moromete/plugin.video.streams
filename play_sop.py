import xbmc, xbmcgui

import os
import urllib2

import glob
from glob import addon_log, ADDON_PATH, addon, is_exe

##########################################sopcast data
SPSC_BINARY = "sp-sc-auth"

#raspberry pi
QEMU = "qemu-i386"  #for raspberry pi to issue kill command
ARM = False
if(os.uname()[4][:3] == 'arm'):
  ARM = True
##############

if ARM == False :
  SPSC = os.path.join(ADDON_PATH, 'bin/linux_i386/sopcast', SPSC_BINARY)

  #make executables
  is_exe(SPSC)

  ## get system default env PATH
  #pathdirs = os.environ['PATH'].split(os.pathsep)
  ## looking for (the first match) sp-sc-auth binary in the system default path
  #for dir in pathdirs:
  #  if os.path.isdir(dir):
  #    if os.path.isfile(os.path.join(dir,SPSC_BINARY)):
  #      SPSC = os.path.join(dir,SPSC_BINARY)
  #      break
elif ARM == True:
  SOPCAST_ARM_PATH =  addon.getSetting('sopcast_arm_path')
  if(SOPCAST_ARM_PATH == '') :
    SOPCAST_ARM_PATH = os.path.join(ADDON_PATH, 'bin/arm/sopcast')

  #make executables
  is_exe(os.path.join(SOPCAST_ARM_PATH, QEMU))
  is_exe(os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"))

  QEMU_SPSC = [os.path.join(SOPCAST_ARM_PATH, QEMU), os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"), "--library-path", os.path.join(SOPCAST_ARM_PATH, "lib")]
  SPSC = os.path.join(SOPCAST_ARM_PATH, SPSC_BINARY)
  #/storage/sopcast/qemu-i386 /storage/sopcast/lib/ld-linux.so.2 --library-path /storage/sopcast/lib /storage/sopcast/sp-sc-auth 2>&- $1 $2 $3

LOCAL_PORT =  addon.getSetting('local_port')
VIDEO_PORT =  addon.getSetting('video_port')
BUFER_SIZE = int(addon.getSetting('buffer_size'))
##########################################sopcast data

LOCAL_URL = "http://localhost:"+str(VIDEO_PORT)+"/?"

class sop():
  def __init__( self , *args, **kwargs):
    self.player=kwargs.get('player')
    self.listitem=kwargs.get('listitem')
    
    self.cmd = [SPSC, url, str(LOCAL_PORT), str(VIDEO_PORT), "> /dev/null &"]
    if(ARM):
      self.cmd = QEMU_SPSC + cmd

  def start( self ):
    spsc = subprocess.Popen(self.cmd, shell=False, bufsize=BUFER_SIZE, stdin=None, stdout=None, stderr=None)
    self.spsc_pid = spsc.pid

    xbmc.sleep(int(addon.getSetting('wait_time')))

    res=False
    counter=50
    #while counter > 0 and os.path.exists("/proc/"+str(spsc.pid)):
    while counter > 0 and sop_pid_exists():
      xbmc.executebuiltin( "ActivateWindow(busydialog)" )
      xbmc.sleep(400)
      counter -= 1
      try:
        addon_log(LOCAL_URL);
        urllib2.urlopen(LOCAL_URL)
        counter=0
        res=sop_sleep(200 , self.spsc_pid)
        break
      except:pass

    addon_log(res)

  def sop_pid_exists(self):
    try:
      os.kill(self.spsc_pid, 0)
    except OSError:
      return False
    else:
      return True

  # this function will sleep only if the sop is running
  def sop_sleep(self, time):
    counter=0
    increment=200
    #path="/proc/%s" % str(spsc_pid)

    #addon_log('proc exists')
    #addon_log(os.path.exists(path))
    try:
      #while counter < time and spsc_pid>0 and not xbmc.abortRequested and os.path.exists(path):
      while counter < time and self.spsc_pid>0 and not xbmc.abortRequested and self.sop_pid_exists():
        counter += increment
        xbmc.sleep(increment)
    except Exception as inst:
      addon_log(inst)
      if DEBUG == 'true': xbmc.executebuiltin("Notification(%s,%s,%i)" % (str(type(inst)), str(inst), 5))
      return True
    if counter < time: return False
    else: return True


