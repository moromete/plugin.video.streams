import xbmc, xbmcgui
import urllib2
import json

#import glob
from glob import addon_log, addon
#from default import DISABLE_SCHEDULE, load_active_event

from settings import SETTINGS

if SETTINGS.DISABLE_SCHEDULE != 'true':
  from schedule import load_active_event

class streamplayer(xbmc.Player):
  def __init__( self , *args, **kwargs):
    self.name=kwargs.get('name')
    self.protocol=kwargs.get('protocol')
    self.ch_id=kwargs.get('ch_id')
    self.callback = None
    addon_log('INIT PLAYER')

  def play(self, url, listitem):
    addon.setSetting('player_status', 'play')

    super(streamplayer, self).play(url, listitem)

    self.keep_allive()

  def onPlayBackStarted(self):
    addon_log('START')
    addon_log(xbmc.getInfoLabel('VideoPlayer.VideoCodec'))
    addon_log(xbmc.getInfoLabel('VideoPlayer.AudioCodec'))

    ## this will kill the sopcast if we changed the media
    #if xbmc.Player(xbmc.PLAYER_CORE_AUTO).getPlayingFile() != SETTINGS.LOCAL_URL:
    #  try: stop_spsc(self.spsc_pid)
    #  except: pass
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    #online notif
    self.markOnline()

    if SETTINGS.DISABLE_SCHEDULE!='true':
      #display schedule active event
      active_event = load_active_event(self.name)
      if active_event:
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (active_event, "", 10000))

  def onPlayBackEnded(self):
    addon_log('----------------------->END')

    #xbmc.executebuiltin('Container.Refresh()')
    try:
      if(self.callback != None):
        self.callback()
    except: pass
    addon.setSetting('player_status', 'end')

  def onPlayBackStopped(self):
    addon_log('----------------------->STOP')

    #xbmc.executebuiltin('Container.Refresh()')
    addon_log(self.callback)
    try:
      if(self.callback != None):
        self.callback()
    except: pass
    addon.setSetting('player_status', 'stop')

  def keep_allive(self):
    xbmc.sleep(500)

    #KEEP SCRIPT ALLIVE
    while (addon.getSetting('player_status')=='play'):
      addon_log('ALLIVE')
      xbmc.sleep(500)

    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass

  def markOnline(self):
    try:
      url = "http://streams/channelstatus"
      channelData = { "idChannel": self.ch_id,
                      "status":    1,
                      "res":       xbmc.getInfoLabel('VideoPlayer.VideoResolution'),
                      "aspect":    xbmc.getInfoLabel('VideoPlayer.VideoAspect'),
                      "vCodec":    xbmc.getInfoLabel('VideoPlayer.VideoCodec'),
                      "aCodec":    xbmc.getInfoLabel('VideoPlayer.AudioCodec')
                    }
      addon_log(json.dumps(channelData))
      opener = urllib2.build_opener(urllib2.HTTPHandler)
      request = urllib2.Request(url, data=json.dumps(channelData))
      request.add_header('Content-Type', 'application/json')
      request.get_method = lambda: 'PUT'
      response = opener.open(request)
      addon_log(response.read())
    except: pass
