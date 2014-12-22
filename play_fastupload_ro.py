import xbmc, xbmcgui
import os, os.path, re
import glob
from glob import addon_log, Downloader, message, addon
from settings import SETTINGS

def grab_fu_stream(name, url):
  
  
  try:
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    response = opener.open(url)
    source_txt = response.read()
  except Exception as inst:
    source_txt = ""
  
  #temp = os.path.join(SETTINGS.ADDON_PATH,"temp.htm")
  #Downloader(url, temp, addon.getLocalizedString(30065), name)  #Downloading page for parsing stream url
  #f = open(temp)
  #source_txt = f.read()
  #f.close()
  #os.remove(temp)

  #addon_log(url)
  #addon_log(source_txt)

  match=re.compile('\'file\':\s*\'(http:\/\/[\w\W]+?\.\w+)\'').search(source_txt)
  if match:
    stream_url = match.group(1)
    addon_log(stream_url)
    return stream_url

  return None