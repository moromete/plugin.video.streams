import xbmc, xbmcgui, xbmcaddon
import urllib, urllib2

addon = xbmcaddon.Addon('plugin.video.streams')
ADDON_VERSION = addon.getAddonInfo('version')
ADDON_PATH= addon.getAddonInfo('path')
DEBUG = addon.getSetting('debug')

def addon_log(string):
  if DEBUG == 'true':
    xbmc.log("[plugin.video.streams-%s]: %s" %(ADDON_VERSION, string))
    
def Downloader(url,dest,description,heading):
  dp = xbmcgui.DialogProgress()
  dp.create(heading,description,url)
  dp.update(0)
  urllib.urlretrieve(url,dest,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,dp))
  
def _pbhook(numblocks, blocksize, filesize,dp=None):
  try:
    percent = int((int(numblocks)*int(blocksize)*100)/int(filesize))
    dp.update(percent)
  except:
    percent = 100
    dp.update(percent)
  if dp.iscanceled(): 
    #raise KeyboardInterrupt
    dp.close()
    
def message(title, message):
  dialog = xbmcgui.Dialog()
  dialog.ok(title, message)