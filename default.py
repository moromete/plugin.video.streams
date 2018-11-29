import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os, os.path
import urllib

import time
from datetime import datetime, timedelta

from settings import SETTINGS
from common import addon_log, addon, Downloader

# if SETTINGS.DISABLE_SCHEDULE != 'true':
#   #from schedule import grab_schedule, load_schedule
#   from schedule import epg

from streamplayer import streamplayer
from play_ace import acestream
from play_sop import sopcast

from resources.streams.export import export
from resources.streams.channels import Channels

addon_id = 'plugin.video.streams'
settings = xbmcaddon.Addon(id=addon_id)
fileslist = xbmc.translatePath(settings.getAddonInfo('profile')).decode('utf-8')

def get_params():
  param=[]

  paramstring=sys.argv[2]

  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

def addDir(name, cat_id, url, mode):
  name = name.encode('utf8')
  contextMenuItems = []

  plugin=sys.argv[0]

  u=plugin+"?mode=4"
  contextMenuItems.append(( 'Refresh Channel List', "XBMC.RunPlugin("+u+")", ))

  u = plugin+"?"+"mode="+str(mode) + \
      "&name="+urllib.quote_plus(name) + \
      "&cat_id="+cat_id + "&url="+urllib.quote_plus(url)
  ok = True

  liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage="")
  liz.addContextMenuItems(contextMenuItems)
  liz.setInfo( type="Video", infoLabels={ "Title": name })
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

def addLink(ch_id, name_formatted, name, url, protocol, cat_id, mode, iconimage, plot, totalitems):
  name = name.encode('utf8')
  #cat_name = cat_name.encode('utf8')
  ok = True
  contextMenuItems = []

  #if SETTINGS.DISABLE_SCHEDULE != 'true':
    #u=sys.argv[0]+"?mode=3&name="+urllib.quote_plus(name)
    #if schedule_ch_id != "0":
      #u+="&sch_ch_id="+urllib.quote_plus(schedule_ch_id)
    #contextMenuItems.append(( addon.getLocalizedString(30050), "XBMC.RunPlugin("+u+")", )) #Refresh Schedule

    #u=sys.argv[0]+"?mode=5&name="+urllib.quote_plus(cat_name)+"&cat_id="+cat_id
    #contextMenuItems.append(( addon.getLocalizedString(30051), "XBMC.RunPlugin("+u+")", )) #Refresh All Schedules

    #u=sys.argv[0]+"?mode=6"
    #contextMenuItems.append(( 'EPG', "XBMC.RunPlugin("+u+")", )) #EPG

  u=sys.argv[0]+"?mode=4"
  contextMenuItems.append(( addon.getLocalizedString(30052), "XBMC.RunPlugin("+u+")", )) #Refresh Channel List
  
  u=sys.argv[0]+"?mode=7&ch_id=" + str(ch_id)
  contextMenuItems.append(( addon.getLocalizedString(30407), "XBMC.RunPlugin("+u+")", )) #Delete Channel

  liz = xbmcgui.ListItem(name_formatted, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot} )

  u = sys.argv[0] + "?url=%s&mode=%s&name=%s&cat_id=%s&protocol=%s&ch_id=%s" % ( urllib.quote_plus(url),
      str(mode), 
      urllib.quote_plus(name), 
      cat_id, 
      protocol, 
      str(ch_id) )
  
  liz.addContextMenuItems(contextMenuItems)

  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  return ok

def CAT_LIST(force=False, mode=None):
  channels = Channels()
  if force==False:
    if not os.path.isfile(SETTINGS.CHAN_LIST):
      addon_log('channels first download')
      Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054))  #Downloading Channel list
      channels.importChannels()
    else:
      now_time = time.mktime(datetime.now().timetuple())
      time_created = os.stat(SETTINGS.CHAN_LIST)[8]  # get local play list modified date
      if SETTINGS.CHAN_LIST_EXPIRE>0 and now_time - time_created > SETTINGS.CHAN_LIST_EXPIRE:
        addon_log('channels update')
        Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
        channels.importChannels()
  else:
    Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
    channels.importChannels()

  exp = export()
  if(exp.export() != True) :
    return

  ch = Channels()
  arrCategories = ch.loadCategories()
  for cat in arrCategories:
    channelsListMode = 1
    name = cat.name
    if(mode != None):
      name="[COLOR red]"+cat.name+"[/COLOR]"
      channelsListMode=101
    
    addDir(name, str(cat.id), SETTINGS.CHAN_LIST, channelsListMode)

  #unverified category
  if ((SETTINGS.SHOW_UNVERIFIED == 'true') and (mode==None)):
    addDir("[COLOR red]"+addon.getLocalizedString(30066)+"[/COLOR]", str(-1), SETTINGS.CHAN_LIST, 100)
  
  #xbmc.executebuiltin("Container.SetViewMode(500)")
  xbmc.executebuiltin("Container.SetViewMode(51)")

def CHANNEL_LIST(name, cat_id, mode=None, schedule=False):
  if(mode == 1):
    #add new channel link
    liz=xbmcgui.ListItem('[B][COLOR green]'+addon.getLocalizedString(30402)+'[/COLOR][/B]', iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty('IsPlayable', 'false')
    url = sys.argv[0] + "?mode=6&cat_id=" + cat_id
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)

  channels = Channels(catId = cat_id)
  arrChannels = channels.loadChannels()
  for ch in arrChannels:
    if (((SETTINGS.SHOW_OFFLINE_CH=='true') and (int(ch.status)==1)) or (int(ch.status)!=1)): #if we show or not offline channels based on settings
      name_formatted ="[B]"+ch.name+"[/B]"
      name_formatted += " [[COLOR yellow]"+ch.protocol+"[/COLOR]]"

      if int(ch.status)==1: 
        name_formatted += " [COLOR red]"+addon.getLocalizedString(30063)+"[/COLOR]"  #Offline
      
      addLink(ch.id, name_formatted, ch.name, ch.address.strip(), ch.protocol.strip(),
              ch.id_cat, 2, '', "", len(arrChannels))

  xbmc.executebuiltin("Container.SetViewMode(51)")

def STREAM(name, iconimage, url, protocol, sch_ch_id, ch_id):
  if(url == None):
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass
    return False

  # if (sch_ch_id != None) and (SETTINGS.DISABLE_SCHEDULE != 'true'):
  #   epgObj = epg()
  #   epgObj.grab_schedule(sch_ch_id, name)

  #addon_log(name)
  #addon_log(iconimage)

  if not iconimage or iconimage == "": iconimage="DefaultVideo.png"
  listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  #listitem.setLabel(name)
  listitem.setInfo('video', {'Title': name})

  player = streamplayer(name=name, protocol=protocol, ch_id=ch_id)

  #play sopcast stream
  if protocol == "sop":
    if(SETTINGS.USE_PLEXUS_SOP == 'true'):
      try:
        addon_log('plexus')
        xbmc.executebuiltin('XBMC.RunPlugin(plugin://program.plexus/?mode=2&url='+url+'&name='+name+'&iconimage='+iconimage+')')
      except Exception as inst:
        addon_log(inst)
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30303), "", 10000))
    else:
      sop = sopcast(player=player, url=url, listitem=listitem)
      sop.start()

  #play acestream
  elif protocol=='acestream':
    if(SETTINGS.ACE_ENGINE_TYPE == 2): #use plexus
      try:
        addon_log('plexus')
        xbmc.executebuiltin('XBMC.RunPlugin(plugin://program.plexus/?mode=1&url='+url+'&name='+name+'&iconimage='+iconimage+')')
      except Exception as inst:
        addon_log(inst)
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30303), "", 10000))
    elif(SETTINGS.ACE_ENGINE_TYPE == 1): #use external
      #play with acestream engine started on another machine or on the localhost
      ace = acestream(player=player, url=url, listitem=listitem)
      ace.engine_connect()
  else: #play direct stream
    try:
      player.play(url, listitem)
    except Exception as inst:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30060), str(type(inst)),str(inst),"")
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################

addon_log('------------- START -------------')
addon_log(SETTINGS.CHAN_LIST_URL)
addon_log(SETTINGS.CHAN_LIST)

#read params
params=get_params()
try:
  mode=int(params["mode"])
except:
  mode=None
try:
  name=urllib.unquote_plus(params["name"].decode('utf8').encode('utf8'))
except:
  name=None
try:
  cat_id=urllib.unquote_plus(params["cat_id"].decode('utf8').encode('utf8'))
except:
  cat_id=None
try:
  iconimage=urllib.unquote_plus(params["iconimage"])
except:
  iconimage=None
try:
  url=urllib.unquote_plus(params["url"])
except:
  url=None
try:
  sch_ch_id=urllib.unquote_plus(params["sch_ch_id"])
except:
  sch_ch_id=None
try:
  protocol=urllib.unquote_plus(params["protocol"])
except:
  protocol=None
try:
  ch_id=urllib.unquote_plus(params["ch_id"])
except:
  ch_id=None

addon_log(mode)
if ((mode==None) or (mode==100)): #list categories
  CAT_LIST(mode=mode)
elif ((mode==1) or (mode==101)):  #list channels
  CHANNEL_LIST(name=name, cat_id=cat_id, mode=mode)
elif mode==2:  #play stream
  if xbmc.Player().isPlaying():
    xbmc.Player().stop()
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass
  xbmc.executebuiltin( "ActivateWindow(busydialog)" )
  STREAM(name, iconimage, url, protocol, sch_ch_id, ch_id)
# elif mode==3:  #refresh schedule
#   if sch_ch_id != None:
#     epgObj = epg()
#     epgObj.grab_schedule(sch_ch_id, name, force=True)
#     xbmc.executebuiltin('Container.Refresh()')
elif mode==4:  #refresh channel list
  CAT_LIST(force=True)
  xbmc.executebuiltin('Container.Refresh()')
elif mode==5:  #refresh all schedules
  CHANNEL_LIST(name=name, cat_id=cat_id, schedule=True)
  xbmc.executebuiltin('Container.Refresh()')
elif (mode==6): #add stream
  channels = Channels(catId = cat_id) 
  channels.addChannel()
elif (mode==7): #delete stream
  channels = Channels() 
  channels.deleteStream(ch_id)
  
try:
  xbmc.executebuiltin( "Dialog.Close(busydialog)" )
except: pass

addon_log('------------- END -------------')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
