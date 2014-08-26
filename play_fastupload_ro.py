import xbmc, xbmcgui
import os, os.path, re
import glob
from glob import addon_log, ADDON_PATH, Downloader, message, addon

def grab_fu_stream(name, url):
  temp = os.path.join(ADDON_PATH,"temp.htm")
  Downloader(url, temp, addon.getLocalizedString(30065), name)  #Downloading page for parsing stream url
  f = open(temp)
  source_txt = f.read()
  f.close()
  os.remove(temp)
  
  #addon_log(url)
  #addon_log(source_txt)
  
  match=re.compile('\'file\':\s*\'(http:\/\/[\w\W]+?\.\w+)\'').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log(stream_url)  
    return stream_url
  
  return None