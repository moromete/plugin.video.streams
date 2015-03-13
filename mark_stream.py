import xbmc, xbmcgui
import urllib2
import json
from glob import addon_log

class mark_stream():
  def __init__( self , *args, **kwargs):
    self.ch_id=kwargs.get('ch_id')
    #self.url = "http://streams/channelstatus"
    self.url = "http://streams.magazinmixt.ro/channelstatus"

  def mark_online(self):
    channelData = { "idChannel": self.ch_id,
                    "status":    1,
                    "res":       xbmc.getInfoLabel('VideoPlayer.VideoResolution'),
                    "aspect":    xbmc.getInfoLabel('VideoPlayer.VideoAspect'),
                    "vCodec":    xbmc.getInfoLabel('VideoPlayer.VideoCodec'),
                    "aCodec":    xbmc.getInfoLabel('VideoPlayer.AudioCodec')
                  }
    addon_log(json.dumps(channelData))
    self.send_request(channelData)

  def mark_offline(self):
    channelData = { "idChannel": self.ch_id,
                    "status":    -1,
                  }
    addon_log(json.dumps(channelData))
    self.send_request(channelData)

  def send_request(self, channelData):
    try:
      opener = urllib2.build_opener(urllib2.HTTPHandler)
      request = urllib2.Request(self.url, data=json.dumps(channelData))
      request.add_header('Content-Type', 'application/json')
      request.get_method = lambda: 'PUT'
      response = opener.open(request)
      addon_log('Response :')
      addon_log(response.read())
    except: pass