import xbmc, xbmcgui

import os
import urllib2
import subprocess

import glob
from common import addon_log, addon, is_exe
from settings import SETTINGS
from resources.streams.channels import Channels
from resources.streams.channel import Channel

class sopcast():
  def __init__( self , *args, **kwargs):
    self.player=kwargs.get('player')
    self.listitem=kwargs.get('listitem')

    url=kwargs.get('url')
    self.sopurl = url
    
    self.cmd = SETTINGS.SPSC + \
               [ url, str(SETTINGS.LOCAL_PORT), str(SETTINGS.VIDEO_PORT), 
                "> /dev/null &"
               ]
    print(self.cmd)
    
  def start( self ):
    if xbmc.getCondVisibility('System.Platform.Android'):
      xbmc.executebuiltin('XBMC.StartAndroidActivity("com.devaward.soptohttp","android.intent.action.VIEW","",'+self.sopurl+')')
    else:
      try:
        # addon_log(self.cmd)
        self.spsc = subprocess.Popen(self.cmd, shell=False, bufsize=SETTINGS.BUFER_SIZE, stdin=None, stdout=None, stderr=None, preexec_fn=lambda: os.nice(-20))
        # if(SETTINGS.ARM):
        #   self.spsc = subprocess.Popen(self.cmd, shell=False, bufsize=SETTINGS.BUFER_SIZE, stdin=None, stdout=None, stderr=None)
        # else:
        #   env = os.environ
        #   env['LD_LIBRARY_PATH'] = SETTINGS.SPSC_LIB
        #   addon_log(self.cmd)
        #   self.spsc = subprocess.Popen(self.cmd, shell=False, bufsize=SETTINGS.BUFER_SIZE, stdin=None, stdout=None, stderr=None, env=env)
        
        self.spsc_pid = self.spsc.pid
        xbmc.sleep(500)
        res=False
        mensagemprogresso = xbmcgui.DialogProgress()
        ret = mensagemprogresso.create(addon.getLocalizedString(30411))
        mensagemprogresso.update(0)
        counter = 55
        while counter > 0 and self.sop_pid_exists():
          if mensagemprogresso.iscanceled(): 
              mensagemprogresso.close()
              break        
          counter -= 1
          percent = int((1 - (counter / 55.0)) * 100)
          secs_left = str(counter)
          mensagemprogresso.update(percent, "[COLOR yellow]"+self.player.name+"[/COLOR]", addon.getLocalizedString(30410) + str(secs_left))
          xbmc.sleep(500)
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
          mensagemprogresso.close()
          self.player.callback = self.stop_spsc
          self.player.play(SETTINGS.LOCAL_URL, self.listitem)
          xbmc.sleep(500)
          self.start()

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
          ch = Channels();
          ch.markStream(chId = self.player.ch_id, status=Channel.STATUS_OFFLINE) #offline

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
    counter = 0
    increment = 3000
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
