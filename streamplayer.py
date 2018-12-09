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
    addon_log('INIT PLAYER')

  def play(self, url, listitem):
    #addon.setSetting('player_status', 'play')
    self.player_status = 'play';

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
    ch = Channels();
    ch.markStream(chId = self.ch_id, status=Channel.STATUS_ONLINE) #online

    self.stream_online = True

    # if SETTINGS.DISABLE_SCHEDULE!='true':
    #   #display schedule active event
    #   epgObj = epg()
    #   active_event = epgObj.load_active_event(self.name)
    #   if active_event:
    #     active_event = active_event.encode('utf8')
    #     xbmc.executebuiltin("Notification(%s,%s,%i)" % (active_event, "", 10000))

  def onPlayBackEnded(self):
    addon_log('----------------------->END')
    addon_log(self.stream_online);

    #xbmc.executebuiltin('Container.Refresh()')
    try:
      if(self.callback != None):
        self.callback()
    except: pass

    if(self.stream_online!=True) :
      #online notif
      ch = Channels();
      ch.markStream(chId = self.ch_id, status=Channel.STATUS_OFFLINE) #offline
      self.stream_online = False

    #addon.setSetting('player_status', 'end')
    self.player_status = 'end';

  def onPlayBackStopped(self):
    addon_log('----------------------->STOP')
    addon_log(self.stream_online);

    #xbmc.executebuiltin('Container.Refresh()')
    addon_log(self.callback)
    try:
      if(self.callback != None):
        self.callback()
    except: pass

    #online notif
    if(self.stream_online!=True) :
      ch = Channels();
      ch.markStream(chId = self.ch_id, status=Channel.STATUS_OFFLINE)  #offline
      self.stream_online = False
      xbmc.executebuiltin( "Dialog.Close(busydialog)" )
      if SETTINGS.NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "",1))  #Channel is offline

    #addon.setSetting('player_status', 'stop')
    xbmc.Player().stop()


  def keep_allive(self):
    xbmc.sleep(500)

    #KEEP SCRIPT ALLIVE
    #while (addon.getSetting('player_status')=='play'):
    while (self.player_status=='play'):
      addon_log('ALLIVE')
      xbmc.sleep(500)

    #try: xbmc.executebuiltin("Dialog.Close(all,true)")
    #except: pass
