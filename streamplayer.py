import xbmc, xbmcgui
from mark_stream import mark_stream

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
    mark = mark_stream(ch_id=self.ch_id)
    mark.mark_online()
    self.stream_online = True

    if SETTINGS.DISABLE_SCHEDULE!='true':
      #display schedule active event
      active_event = load_active_event(self.name)
      if active_event:
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (active_event, "", 10000))

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
      mark = mark_stream(ch_id=self.ch_id)
      mark.mark_offline()
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
      mark = mark_stream(ch_id=self.ch_id)
      mark.mark_offline()
      self.stream_online = False
      xbmc.executebuiltin( "Dialog.Close(busydialog)" )
      if SETTINGS.NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "",1))  #Channel is offline

    #addon.setSetting('player_status', 'stop')
    self.player_status = 'stop';

  def keep_allive(self):
    xbmc.sleep(500)

    #KEEP SCRIPT ALLIVE
    #while (addon.getSetting('player_status')=='play'):
    while (self.player_status=='play'):
      addon_log('ALLIVE')
      xbmc.sleep(500)

    #try: xbmc.executebuiltin("Dialog.Close(all,true)")
    #except: pass