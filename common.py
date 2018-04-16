import xbmc, xbmcgui, xbmcaddon
import urllib, urllib2
import os, stat
import tarfile

addon = xbmcaddon.Addon('plugin.video.streams')
addonpath = addon.getAddonInfo('path')
filespath = xbmc.translatePath(addon.getAddonInfo('profile'))

def addon_log(string):
  DEBUG = addon.getSetting('debug')
  ADDON_VERSION = addon.getAddonInfo('version')
  if DEBUG == 'true':
    if isinstance(string, unicode):
      string = string.encode('utf-8')
    xbmc.log("[plugin.video.streams-%s]: %s" %(ADDON_VERSION, string))


def Downloader(url,dest,description,heading):
  dp = xbmcgui.DialogProgress()
  dp.create(heading,description,url)
  dp.update(0)

  urllib.urlretrieve(url,dest,lambda nb, bs, fs, url=url: _pbhook(nb,bs,fs,dp))

def _pbhook(numblocks, blocksize, filesize, dp=None):
  try:
    percent = int((int(numblocks)*int(blocksize)*100)/int(filesize))
    dp.update(percent)
  except:
    percent = 100
    dp.update(percent)
  if dp.iscanceled():
    #raise KeyboardInterrupt
    dp.close()

# def extract(file_tar,destination):
#     dp = xbmcgui.DialogProgress()
#     dp.create("Streams","Extracting module contents. Please wait.")
#     tar = tarfile.open(file_tar)
#     tar.extractall(destination)
#     dp.update(100)
#     tar.close()
#     dp.close()

# def remove(file_):
#     dp = xbmcgui.DialogProgress()
#     dp.create("Streams","Removing files.")
#     os.remove(file_)
#     dp.update(100)
#     dp.close()

# def acekit(acestream_pack):
#     ACE_KIT = os.path.join(addonpath,acestream_pack.split("/")[-1])
#     Downloader(acestream_pack,ACE_KIT,"Downloading AceStream modules.","Streams")
#     if tarfile.is_tarfile(ACE_KIT):
#         path_libraries = os.path.join(filespath)
#         extract(ACE_KIT,path_libraries)
#         xbmc.sleep(500)
#         remove(ACE_KIT)
#     binary_path = os.path.join(filespath,"acestream","chroot")
#     st = os.stat(binary_path)
#     import stat
#     os.chmod(binary_path, st.st_mode | stat.S_IEXEC)

def message(title, message):
  dialog = xbmcgui.Dialog()
  dialog.ok(title, message)

def is_exe(fpath):
  if os.path.isfile(fpath):
    if (os.access(fpath, os.X_OK) != True) :
      st = os.stat(fpath)
      os.chmod(fpath, st.st_mode | stat.S_IEXEC)
