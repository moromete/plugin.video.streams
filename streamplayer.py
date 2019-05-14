import xbmc, xbmcgui

#import glob
from common import addon_log, addon
#from default import DISABLE_SCHEDULE, load_active_event

from settings import SETTINGS
from resources.streams.channels import Channels
from resources.streams.channel import Channel

# if SETTINGS.DISABLE_SCHEDULE != 'true':
#   from schedule import epg

class streamplayer(xbmc.Player):
  def __init__( self , *args, **kwargs):
    self.name=kwargs.get('name')
    self.protocol=kwargs.get('protocol')
    self.ch_id=kwargs.get('ch_id')
    self.callback = None

    self.stream_online = None
    self.player_status = None
    # addon_log('INIT PLAYER')

  def play(self, url, listitem):
    self.player_status = 'play';
    super(streamplayer, self).play(url, listitem)
    self.keep_allive()

  def onPlayBackStarted(self):
    addon_log('-----------------------------> START PLAY')
 
    # if SETTINGS.DISABLE_SCHEDULE!='true':
    #   #display schedule active event
    #   epgObj = epg()
    #   active_event = epgObj.load_active_event(self.name)
    #   if active_event:
    #     active_event = active_event.encode('utf8')
    #     xbmc.executebuiltin("Notification(%s,%s,%i)" % (active_event, "", 10000))

  def onPlayBackEnded(self):
    addon_log('----------------------->END')
    self.player_status = 'end';

    try:
      if(self.callback != None):
        self.callback()
    except: pass

    if(self.stream_online!=True) :
      self.isOffline()

  def onPlayBackStopped(self):
    addon_log('----------------------->STOP')
    self.player_status = 'stop';

    # addon_log(self.callback)
    try:
      if(self.callback != None):
        self.callback()
    except: pass

    #online notif
    if(self.stream_online!=True) :
      self.isOffline()

  def isOffline(self):
    ch = Channels();
    ch.markStream(chId = self.ch_id, status=Channel.STATUS_OFFLINE)  #offline
    self.stream_online = False
    xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "",1))  #Channel is offline

  def keep_allive(self):
    xbmc.sleep(500)

    #KEEP SCRIPT ALLIVE
    while (self.player_status=='play'):
      if(self.stream_online == None):
        
        vc = xbmc.getInfoLabel('VideoPlayer.VideoCodec')
        ac = xbmc.getInfoLabel('VideoPlayer.AudioCodec')
        if(ac or vc):
          #online notif
          addon_log('mark online')
          ch = Channels();
          ch.markStream(chId = self.ch_id, status=Channel.STATUS_ONLINE) #online
          self.stream_online = True
      
      addon_log('ALLIVE')
      xbmc.sleep(500)