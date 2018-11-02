import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os, os.path
import urllib, urllib2, socket, re
import json, sqlite3
import tarfile

import time
from datetime import datetime, timedelta

from settings import SETTINGS
from common import addon_log, addon, Downloader

if SETTINGS.DISABLE_SCHEDULE != 'true':
  #from schedule import grab_schedule, load_schedule
  from schedule import epg

from streamplayer import streamplayer
from play_vk_com import grab_vk_stream
from play_fastupload_ro import grab_fu_stream
from play_ace import acestream
from play_sop import sopcast

from resources.streams.mystreams import *

addon_id = 'plugin.video.streams'
settings = xbmcaddon.Addon(id=addon_id)
fileslist = xbmc.translatePath(settings.getAddonInfo('profile')).decode('utf-8')


# try:
#   try:
#     raise
#     import xml.etree.cElementTree as ElementTree
#   except:
#     from xml.etree import ElementTree
# except:
#   try:
#     from xml.etree.ElementTree import Element
#     from xml.etree.ElementTree import SubElement
#     from elementtree import ElementTree
#   except:
#     dlg = xbmcgui.Dialog()
#     dlg.ok('ElementTree missing', 'Please install the elementree addon.',
#            'http://tinyurl.com/xmbc-elementtree')
#     sys.exit(0)

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

def addLink(ch_id, name_formatted, name, url, protocol, schedule_ch_id, cat_name, cat_id, mode, iconimage, plot, totalitems):
  name = name.encode('utf8')
  cat_name = cat_name.encode('utf8')
  ok = True
  contextMenuItems = []

  if SETTINGS.DISABLE_SCHEDULE != 'true':
    u=sys.argv[0]+"?mode=3&name="+urllib.quote_plus(name)
    if schedule_ch_id != "0":
      u+="&sch_ch_id="+urllib.quote_plus(schedule_ch_id)
    contextMenuItems.append(( addon.getLocalizedString(30050), "XBMC.RunPlugin("+u+")", )) #Refresh Schedule

    u=sys.argv[0]+"?mode=5&name="+urllib.quote_plus(cat_name)+"&cat_id="+cat_id
    contextMenuItems.append(( addon.getLocalizedString(30051), "XBMC.RunPlugin("+u+")", )) #Refresh All Schedules

    #u=sys.argv[0]+"?mode=6"
    #contextMenuItems.append(( 'EPG', "XBMC.RunPlugin("+u+")", )) #EPG

  u=sys.argv[0]+"?mode=4"
  contextMenuItems.append(( addon.getLocalizedString(30052), "XBMC.RunPlugin("+u+")", )) #Refresh Channel List

  liz = xbmcgui.ListItem(name_formatted, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot} )

  u=sys.argv[0]+"?"+"url="+urllib.quote_plus(url)+"&mode="+str(mode)+\
                         "&name="+urllib.quote_plus(name)+\
                         "&iconimage="+urllib.quote_plus(iconimage)+\
                         "&cat_id="+cat_id+"&protocol="+protocol+\
                         "&ch_id="+str(ch_id)
  if schedule_ch_id != "0":
    u+="&sch_ch_id="+urllib.quote_plus(schedule_ch_id)

  liz.addContextMenuItems(contextMenuItems)

  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  return ok

def parse_ch_data():
  with open(SETTINGS.CHAN_LIST) as json_file:
    data = json.loads(json_file.read())
    json_file.close()

    sql = "CREATE TABLE IF NOT EXISTS categories (id INTEGER, name TEXT)"
    db_cursor.execute(sql);
    sql="DELETE FROM categories"
    db_cursor.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS channels \
          (id INTEGER, id_cat INTEGER, name TEXT, language TEXT, status INTEGER, \
           video_resolution TEXT, video_aspect REAL, audio_codec TEXT, video_codec TEXT, \
           address TEXT, thumbnail TEXT, protocol TEXT, \
           schedule_id INTEGER, unverified INTEGER)"
    db_cursor.execute(sql)
    sql="DELETE FROM channels"
    db_cursor.execute(sql)

    addon_log(data['date'])

    for group in data['groups']:
      addon_log(str(group['id']) + " " + group['name'])
      db_cursor.execute("INSERT INTO categories \
                         VALUES (?, ?)",
                         (group['id'], group['name']))

      for channel in group['channels']:
        #addon_log(str(channel['id'])+" "+unicode(channel['name'])+" "+ str(channel['language'])+" "+str(channel['status']))
        if ((not channel['unverified']) or (SETTINGS.SHOW_UNVERIFIED=='true')):

          addon_log(channel['name'].encode('utf8'))

          schedule_id = 0
          thumbnail = ""
          video_resolution = ""
          video_aspect = 0
          audio_codec = ""
          video_codec = ""

          stream_type = channel['stream_type']
          if 'schedule' in channel:
            schedule = channel['schedule']
            schedule_id = schedule['ch_id']
          if 'thumbnail' in channel:
            thumbnail = channel['thumbnail']
          if 'video_resolution' in stream_type:
            video_resolution = stream_type['video_resolution']
          if 'video_aspect' in stream_type:
            video_aspect = stream_type['video_aspect']
          if 'audio_codec' in stream_type:
            audio_codec = stream_type['audio_codec']
          if 'video_codec' in stream_type:
            video_codec = stream_type['video_codec']

          db_cursor.execute( \
                "INSERT INTO channels \
                 VALUES (?, ?, ?, ?, ?, \
                         ?, ?, ?, ?, \
                         ?, ?, ?, \
                         ?, ?)" ,
                 ( channel['id'], group['id'], channel['name'], channel['language'], channel['status'], \
                   video_resolution, video_aspect, audio_codec, video_codec, \
                   channel['address'], thumbnail, channel['protocol'], \
                   schedule_id, channel['unverified']) )

    db_connection.commit()

def CAT_LIST(force=False, mode=None):
  if force==False:
    if not os.path.isfile(SETTINGS.CHAN_LIST):
      addon_log('channels first download')
      Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054))  #Downloading Channel list
      parse_ch_data()
    else:
      now_time = time.mktime(datetime.now().timetuple())
      time_created = os.stat(SETTINGS.CHAN_LIST)[8]  # get local play list modified date
      if SETTINGS.CHAN_LIST_EXPIRE>0 and now_time - time_created > SETTINGS.CHAN_LIST_EXPIRE:
        addon_log('channels update')
        Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
        parse_ch_data()
  else:
    Downloader(SETTINGS.CHAN_LIST_URL, SETTINGS.CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
    parse_ch_data()
  
  #addDir("[B]"+addon.getLocalizedString(30401)+"[/B]", "", "", 6)

  rec = []
  try:
    sql = "SELECT id, name \
           FROM categories"
    db_cursor.execute(sql)
    rec=db_cursor.fetchall()
  except Exception as inst:
    #addon_log(inst)
    #cannot parse the channel list
    xbmcgui.Dialog().ok(addon.getLocalizedString(30300), addon.getLocalizedString(30301), str(inst))  #Cannot parse channel list !

  if len(rec)>0:
    for id, name in rec:
      channelsListMode=1
      if(mode!=None):
        name="[COLOR red]"+name+"[/COLOR]"
        channelsListMode=101
      addDir(name, str(id), SETTINGS.CHAN_LIST, channelsListMode)

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
    url = sys.argv[0] + "?mode=6&cat_id=" + cat_id
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)

  if (SETTINGS.DISABLE_SCHEDULE != 'true'):
    epgObj = epg()

  addon_log(name);
  rec = []
  try:
    sql = 'SELECT id, name, language, status, \
           address, thumbnail, protocol, \
           schedule_id, unverified \
           FROM channels \
           WHERE id_cat = ?'
    if((mode!=None) and (int(mode)==101)):
      sql += ' and unverified = 1'
    else:
      sql += ' and unverified IS NULL'
    sql += ' ORDER BY name'
    db_cursor.execute( sql, (cat_id,) )
    rec=db_cursor.fetchall()
  except Exception as inst:
    addon_log(inst)
    xbmcgui.Dialog().ok(addon.getLocalizedString(30300), addon.getLocalizedString(30301), str(inst))  #Cannot parse channel list !

  if len(rec)>0:
    for id, name, language, status, \
        address, thumbnail, protocol, \
        schedule_id, unverified in rec:

      #filter by country and language
      #if( (((country != '') and (addon.getSetting('country_'+country) == 'true')) or
           #((country == '') and (addon.getSetting('country_none') == 'true')) ) and
           #(((language != '') and (addon.getSetting('lang_'+language) == 'true')) or
           #((language == '') and (addon.getSetting('lang_none') == 'true')) )
        #):

      chan_name = name
      chan_url = address.strip()

      protocol = protocol.strip()
      #if protocol=='sop':
      #  protocol_color = '[COLOR lightgreen]'+protocol+'[/COLOR]'
      #else:
      #  protocol_color = '[COLOR yellow]'+protocol+'[/COLOR]'

      chan_thumb = ''
      if(thumbnail):
        chan_thumb = thumbnail.strip()
      #addon_log(chan_thumb)
      chan_status = status

      if (((SETTINGS.SHOW_OFFLINE_CH=='true') and (int(chan_status)==1)) or (int(chan_status)!=1)): #if we show or not offline channels based on settings
        logo_name = chan_name.replace(' ', '').lower()
        logo_name = logo_name.encode('utf8')

        chan_name_formatted ="[B]"+chan_name+"[/B]"
        chan_name_formatted += " [[COLOR yellow]"+protocol+"[/COLOR]]"

        if int(chan_status)==1: chan_name_formatted += " [COLOR red]"+addon.getLocalizedString(30063)+"[/COLOR]"  #Offline

        thumb_path=""
        if chan_thumb and chan_thumb != "":
          fileName, fileExtension = os.path.splitext(chan_thumb)
          fileName=fileName.split("/")[-1]

          logoDir = os.path.join(SETTINGS.ADDON_PATH,"logos");
          #create logos directory if does not exists
          if(not os.path.isdir(logoDir)):
            os.makedirs(logoDir)

          if fileName != "":
            #thumb_path=os.path.join(ADDON_PATH,"logos",fileName+fileExtension)
            fileExtension = fileExtension.encode('utf8')
            thumb_path=os.path.join(logoDir,logo_name+fileExtension)

          if not os.path.isfile(thumb_path):
            if fileName != "":
              try:
                Downloader(chan_thumb, thumb_path, fileName+fileExtension, addon.getLocalizedString(30055)) #Downloading Channel Logo
              except Exception as inst:
                pass;

        #schedule
        if (schedule_id != 0) and \
            (schedule or (addon.getSetting('schedule_ch_list') == 'true')) \
            and (SETTINGS.DISABLE_SCHEDULE != 'true'):
          if (schedule): #update all by context menu
            update_all = True
          elif(addon.getSetting('schedule_ch_list') == 'true'): #update all when we display channel list
            update_all = False
          #addon_log('grab_schedule')
          epgObj.grab_schedule(schedule_id, chan_name, update_all=update_all)

        if (SETTINGS.DISABLE_SCHEDULE != 'true') and (int(cat_id) < 200):
          schedule_txt = epgObj.load_schedule(chan_name)
          chan_name_formatted += "   " + schedule_txt

        addLink(id, chan_name_formatted, chan_name, chan_url, protocol, str(schedule_id),
                name, cat_id, 2, thumb_path, "", len(rec))

  xbmc.executebuiltin("Container.SetViewMode(51)")

def STREAM(name, iconimage, url, protocol, sch_ch_id, ch_id):
  if(url == None):
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass
    return False

  if (sch_ch_id != None) and (SETTINGS.DISABLE_SCHEDULE != 'true'):
    epgObj = epg()
    epgObj.grab_schedule(sch_ch_id, name)

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
    # else: #use internal
    #   if xbmc.getCondVisibility('System.Platform.Android'):
    #       #xbmc.executebuiltin("Notification(%s,%s,%i)" % ("android", "", 3000))
    #       ace = acestream(player=player, url=url, listitem=listitem)
    #       ace.engine_connect()
    #   elif xbmc.getCondVisibility('system.platform.linux'):
    #       #xbmc.executebuiltin("Notification(%s,%s,%i)" % ("linux", "", 3000))
    #       addon_log('linux')
    #       addon_log(os.uname())
    #       if "aarch" in os.uname()[4]:
    #           addon_log('aarch')
    #           #xbmc.executebuiltin("Notification(%s,%s,%i)" % ("aarch", "", 3000))
    #           if not os.path.isfile(os.path.join(fileslist,"acestream","chroot")):
    #               arch = '64' if sys.maxsize > 2**32 else '32'
    #               acestream_pack = "https://raw.githubusercontent.com/viorel-m/kingul-repo/master/acestream/acestream_arm%s.tar.gz" % arch
    #               acekit(acestream_pack)
    #           import acestream as ace
    #           ace.acestreams_builtin(name,iconimage,url)
    #       elif "arm" in os.uname()[4]:
    #           addon_log('arm')
    #           if not os.path.isfile(os.path.join(fileslist,"acestream","chroot")):
    #               acestream_pack = "https://raw.githubusercontent.com/viorel-m/kingul-repo/master/acestream/acestream_arm32.tar.gz"
    #               acekit(acestream_pack)
    #           import acestream as ace
    #           ace.acestreams_builtin(name,iconimage,url)

  #play direct stream
  else:
    try:
      player.play(url, listitem)
    except Exception as inst:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30060), str(type(inst)),str(inst),"")
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass


#watching sop process and restarting the player if it dies
#def watch_sop_thread(spsc_pid, name, listitem):
#  xbmc.sleep(100)
#  sop_sleep(4000 , spsc_pid)
#
#  #addon_log(spsc_pid)
#  #addon_log(name)
#  #addon_log(listitem)
#
#  #while os.path.exists("/proc/"+str(spsc_pid)) and not xbmc.abortRequested:
#  while sop_pid_exists(spsc_pid) and not xbmc.abortRequested:
#    addon_log("CHECK ONLINE")
#    addon_log(SPSC_STOPED)
#
#    # check if player stoped and restart it
#    if not xbmc.Player(xbmc.PLAYER_CORE_AUTO).isPlaying():
#      if not sop_sleep(1000 , spsc_pid): break
#      if not xbmc.Player(xbmc.PLAYER_CORE_AUTO).isPlaying():
#        player = streamplayer(xbmc.PLAYER_CORE_AUTO , spsc_pid=spsc_pid, name=name)
#        player.play(LOCAL_URL, listitem)
#        addon_log("RESTART PLAYER")
#
#      sop_sleep(2000 , spsc_pid)
#    sop_sleep(300 , spsc_pid)

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################

addon_log('------------- START -------------')

db_connection=sqlite3.connect(SETTINGS.CHANNELS_DB)
db_cursor=db_connection.cursor()

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
    #stop_spsc()

    xbmc.Player().stop()
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass

    #xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    #xbmc.sleep(800)
    #if cat_id == "200" :
    #  url = grab_vk_stream(name, url)
    #if cat_id == "201" or cat_id == "202" :
    #  url = grab_fu_stream(name, url)
    #STREAM(name, iconimage, url, protocol, sch_ch_id, ch_id)
  #else:
    #stop_spsc()

  #dialog = xbmcgui.DialogProgress()
  #dialog.create('Kodi', 'Loading...')

  xbmc.executebuiltin( "ActivateWindow(busydialog)" )


    #if cat_id == "200" :
    #  url = grab_vk_stream(name, url)
    #if cat_id == "201" or cat_id == "202" :
    #  url = grab_fu_stream(name, url)
  STREAM(name, iconimage, url, protocol, sch_ch_id, ch_id)
elif mode==3:  #refresh schedule
  if sch_ch_id != None:
    epgObj = epg()
    epgObj.grab_schedule(sch_ch_id, name, force=True)
    xbmc.executebuiltin('Container.Refresh()')
elif mode==4:  #refresh channel list
  CAT_LIST(force=True)
  xbmc.executebuiltin('Container.Refresh()')
elif mode==5:  #refresh all schedules
  CHANNEL_LIST(name=name, cat_id=cat_id, schedule=True)
  xbmc.executebuiltin('Container.Refresh()')
elif (mode==6): 
  add_stream(cat_id) #add stream
  #addDir('[B][COLOR green]'+addon.getLocalizedString(30402)+'[/COLOR][/B]', "", "", 7)
#elif (mode==7): add_stream() #add stream
  
#elif mode==6:  #EPG
#  addon_log('epg');
#  mydisplay = EPG("custom_help.xml",ADDON_PATH)
#  mydisplay.doModal()
#  del mydisplay

db_connection.close()

try:
  xbmc.executebuiltin( "Dialog.Close(busydialog)" )
except: pass

addon_log('------------- END -------------')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
