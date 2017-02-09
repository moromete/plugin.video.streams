import xbmc, xbmcgui

import os
import urllib2
import subprocess

import glob
from common import addon_log, addon, is_exe
from settings import SETTINGS
from mark_stream import mark_stream

class sopcast():
  def __init__( self , *args, **kwargs):
    self.player=kwargs.get('player')
    self.listitem=kwargs.get('listitem')

    url=kwargs.get('url')
    self.cmd = [SETTINGS.SPSC, url, str(SETTINGS.LOCAL_PORT), str(SETTINGS.VIDEO_PORT), "> /dev/null &"]
    if(SETTINGS.ARM):
      self.cmd = SETTINGS.QEMU_SPSC + self.cmd

  def start( self ):
    try:
      if(SETTINGS.ARM):
        self.spsc = subprocess.Popen(self.cmd, shell=False, bufsize=SETTINGS.BUFER_SIZE, stdin=None, stdout=None, stderr=None)
      else:
        env = os.environ
        env['LD_LIBRARY_PATH'] = SETTINGS.SPSC_LIB
        self.spsc = subprocess.Popen(self.cmd, shell=False, bufsize=SETTINGS.BUFER_SIZE, stdin=None, stdout=None, stderr=None, env=env)

      self.spsc_pid = self.spsc.pid

      xbmc.sleep(int(addon.getSetting('wait_time')))

      res=False
      counter=50
      #while counter > 0 and os.path.exists("/proc/"+str(spsc.pid)):
      while counter > 0 and self.sop_pid_exists():
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        xbmc.sleep(400)
        counter -= 1
        try:
          addon_log(SETTINGS.LOCAL_URL);
          urllib2.urlopen(SETTINGS.LOCAL_URL)
          counter=0
          res=self.sop_sleep(200)
          break
        except Exception as inst:
          addon_log(inst)

      addon_log(res)
      offline = None
      if res:

        #START PLAY
        self.player.callback = self.stop_spsc
        self.player.play(SETTINGS.LOCAL_URL, self.listitem)

      elif not self.sop_pid_exists():
        try: xbmc.executebuiltin("Dialog.Close(all,true)")
        except: pass
        try:
          urllib2.urlopen(SETTINGS.TEST_URL)
          if SETTINGS.NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "",1))  #Channel is offline
          offline = True
        except:
          if SETTINGS.NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30058), "",1)) #Network is offline
      elif SETTINGS.NOTIFY_OFFLINE == "true":
        try: xbmc.executebuiltin("Dialog.Close(all,true)")
        except: pass
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30059), "", 1)) #Channel initialization failed
        offline = True
        try: self.stop_spsc()
        except: pass
      
      if offline:
        mark = mark_stream(ch_id=self.player.ch_id)
        mark.mark_offline()

    except Exception as inst:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30060), str(type(inst)),str(inst),"")
      addon_log(str(inst))
      try:
        stop_spsc()
      except: pass
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass

  def sop_pid_exists(self):
    if(self.spsc.poll() == None): #A None value indicates that the process hasn't terminated yet
      return True
    else:
      return False
    #try:
    #  self.spsc.poll() #avoid zombie process (A None value indicates that the process hasn't terminated yet)
    #  os.kill(self.spsc_pid, 0)
    #except OSError:
    #  return False
    #else:
    #  return True

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
      DEBUG = addon.getSetting('debug')
      if DEBUG == 'true': xbmc.executebuiltin("Notification(%s,%s,%i)" % (str(type(inst)), str(inst), 5))
      return True
    if counter < time: return False
    else: return True

  def stop_spsc( self ):
    if(self.spsc_pid != None) :
      addon_log('KILL PID = '+str(self.spsc_pid))
      os.kill(self.spsc_pid, 9)
    else :
      addon_log('KILL ALL SOPCAST')
      if(ARM) :
        os.system("killall -9 "+SETTINGS.QEMU)
      else :
        os.system("killall -9 "+SETTINGS.SPSC_BINARY)
