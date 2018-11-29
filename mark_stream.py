import xbmc, xbmcgui
import urllib2
import json
from common import addon_log
from settings import SETTINGS
from urlparse import urlparse

from resources.streams.channel import Channel

class mark_stream():
  def __init__( self , *args, **kwargs):
    self.ch_id=kwargs.get('ch_id')
    #o = urlparse(SETTINGS.CHAN_LIST_URL)
    #self.url = o.scheme+'://'+o.netloc+"/channelstatus"
    #addon_log(self.url)

  def mark_online(self):
    ch = Channel()
    ch.findOne(self.ch_id)
    ch.setStatus(2)
    xbmc.executebuiltin("Container.Refresh")
    # channelData = { "idChannel": self.ch_id,
    #                 "status":    1,
    #                 "res":       xbmc.getInfoLabel('VideoPlayer.VideoResolution'),
    #                 "aspect":    xbmc.getInfoLabel('VideoPlayer.VideoAspect'),
    #                 "vCodec":    xbmc.getInfoLabel('VideoPlayer.VideoCodec'),
    #                 "aCodec":    xbmc.getInfoLabel('VideoPlayer.AudioCodec')
    #               }
    # addon_log(json.dumps(channelData))
    #self.send_request(channelData)
    
    
  def mark_offline(self):
    ch = Channel()
    ch.findOne(self.ch_id)
    ch.setStatus(1)
    xbmc.executebuiltin("Container.Refresh")
    # channelData = { "idChannel": self.ch_id,
    #                 "status":    -1,
    #               }
    # addon_log(json.dumps(channelData))
    #self.send_request(channelData)

  # def send_request(self, channelData):
  #   try:
  #     opener = urllib2.build_opener(urllib2.HTTPHandler)
  #     request = urllib2.Request(self.url, data=json.dumps(channelData))
  #     request.add_header('Content-Type', 'application/json')
  #     request.get_method = lambda: 'PUT'
  #     response = opener.open(request)
  #     addon_log('Response :')
  #     addon_log(response.read())
  #   except Exception as inst:
  #     addon_log(inst)