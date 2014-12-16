import xbmc, xbmcgui
import os, os.path, re
import glob
import urllib2
from glob import addon_log, Downloader, message, addon

from settings import SETTINGS

def grab_vk_stream(name, url):
  addon_log("play vk")
  temp = os.path.join(SETTINGS.ADDON_PATH,"temp.htm")
  addon_log(url)

  try:
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    response = opener.open(url)
    source_txt = response.read()
  except Exception as inst:
    source_txt = ""

  #Downloader(url, temp, addon.getLocalizedString(30065), name)  #Downloading page for parsing stream url
  #f = open(temp)
  #source_txt = f.read()
  #f.close()
  #os.remove(temp)

  #addon_log(source_txt)
  match=re.compile('url720=(http:\/\/[\w\W]+?.mp4?[\w\W]+?)&').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log('720 = '+stream_url)
    return stream_url

  match=re.compile('url480=(http:\/\/[\w\W]+?.mp4?[\w\W]+?)&').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log('480 = '+stream_url)
    return stream_url

  match=re.compile('url360=(http:\/\/[\w\W]+?.mp4?[\w\W]+?)&').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log('360 = '+stream_url)
    return stream_url

  match=re.compile('url240=(http:\/\/[\w\W]+?.mp4?[\w\W]+?)&').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log('240 = '+stream_url)
    return stream_url

  return None