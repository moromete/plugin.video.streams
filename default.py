import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os, os.path, subprocess, stat 
import urllib, urllib2, socket, re
import json, sqlite3
from urlparse import urlparse
from posixpath import basename, dirname
import time
from datetime import datetime, timedelta

from glob import addon_log, addon, ADDON_PATH, ADDON_VERSION, Downloader

DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
if DISABLE_SCHEDULE != 'true':
  from schedule import grab_schedule, load_schedule, load_active_event
  
from play_vk_com import grab_vk_stream
from play_fastupload_ro import grab_fu_stream

try:
  try:
    raise
    import xml.etree.cElementTree as ElementTree
  except:
    from xml.etree import ElementTree
except:
  try:
    from xml.etree.ElementTree import Element
    from xml.etree.ElementTree import SubElement
    from elementtree import ElementTree
  except:
    dlg = xbmcgui.Dialog()
    dlg.ok('ElementTree missing', 'Please install the elementree addon.',
           'http://tinyurl.com/xmbc-elementtree')
    sys.exit(0)

#from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, BeautifulSOAP

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
  contextMenuItems = []
  
  plugin=sys.argv[0]
  
  u=plugin+"?mode=4"
  contextMenuItems.append(( 'Refresh Channel List', "XBMC.RunPlugin("+u+")", ))
  
  u = plugin+"?"+"mode="+str(mode) + \
      "&name="+urllib.quote_plus(name.decode('utf8').encode('utf8')) + \
      "&cat_id="+cat_id + "&url="+urllib.quote_plus(url)
  ok = True
  
  liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage="")
  liz.addContextMenuItems(contextMenuItems)
  liz.setInfo( type="Video", infoLabels={ "Title": name })
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

def addLink(name_formatted, name, url, schedule_ch_id, cat_name, cat_id, mode, iconimage, plot, totalitems):
  ok = True
  contextMenuItems = []
  
  if DISABLE_SCHEDULE != 'true':
    u=sys.argv[0]+"?mode=3&name="+urllib.quote_plus(name.decode('utf8').encode('utf8'))
    if schedule_ch_id != "0":
      u+="&sch_ch_id="+urllib.quote_plus(schedule_ch_id)
    contextMenuItems.append(( addon.getLocalizedString(30050), "XBMC.RunPlugin("+u+")", )) #Refresh Schedule
    
    u=sys.argv[0]+"?mode=5&name="+urllib.quote_plus(cat_name.decode('utf8').encode('utf8'))+"&cat_id="+cat_id
    contextMenuItems.append(( addon.getLocalizedString(30051), "XBMC.RunPlugin("+u+")", )) #Refresh All Schedules
    
    #u=sys.argv[0]+"?mode=6"
    #contextMenuItems.append(( 'EPG', "XBMC.RunPlugin("+u+")", )) #EPG
    
  u=sys.argv[0]+"?mode=4"
  contextMenuItems.append(( addon.getLocalizedString(30052), "XBMC.RunPlugin("+u+")", )) #Refresh Channel List
  
  liz = xbmcgui.ListItem(name_formatted, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot} )
  #if url[0:6]=="sop://":
    #u=sys.argv[0]+"?sop="+urllib.quote_plus(url)+"&mode=3&name="+urllib.quote_plus(name.decode('utf8').encode('utf8'))+"&iconimage="+urllib.quote_plus(iconimage)
    #contextMenuItems.append(( 'Refresh', "XBMC.RunPlugin("+u+")", ))
    
    #if CHAN_LIST == os.path.join(ADDON_PATH,"channel_guide.xml"):
    #    u=sys.argv[0]+"?sop="+urllib.quote_plus(url)+"&mode=4&name="+urllib.quote_plus(name.decode('utf8').encode('utf8'))+"&iconimage="+urllib.quote_plus(iconimage)
    #    contextMenuItems.append(( 'Remove channel', "XBMC.RunPlugin("+u+")", ))
    #channel_guide_xml=ElementTree.parse(os.path.join(ADDON_PATH,"channel_guide.xml"))
    #channel_guide_data = channel_guide_xml.find("./group/channel/.[@id='"+urlparse(url).path.strip("/")+"']")
    #if channel_guide_data:
    #    u=sys.argv[0]+"?sop="+urllib.quote_plus(url)+"&mode=5&name="+urllib.quote_plus(name.decode('utf8').encode('utf8'))+"&iconimage="+urllib.quote_plus(iconimage)
    #    contextMenuItems.append(( 'Update EPG', "XBMC.RunPlugin("+u+")", ))
  
  u=sys.argv[0]+"?"+"url="+urllib.quote_plus(url)+"&mode="+str(mode)+\
                         "&name="+urllib.quote_plus(name.decode('utf8').encode('utf8'))+\
                         "&iconimage="+urllib.quote_plus(iconimage.decode('utf8').encode('utf8'))+\
                         "&cat_id="+cat_id
  if schedule_ch_id != "0":
    u+="&sch_ch_id="+urllib.quote_plus(schedule_ch_id)
  #else:
    #u=url
    #liz.setProperty('IsPlayable', 'true')

  liz.addContextMenuItems(contextMenuItems)
  
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  return ok

def parse_ch_data():
  with open(CHAN_LIST) as json_file:
    data = json.loads(json_file.read())
    json_file.close()
    
    sql = "CREATE TABLE IF NOT EXISTS categories (id INTEGER, name TEXT)"
    db_cursor.execute(sql);
    sql="DELETE FROM categories"
    db_cursor.execute(sql)

    sql = "CREATE TABLE IF NOT EXISTS channels \
          (id INTEGER, id_cat INTEGER, name TEXT, country TEXT, language TEXT, status INTEGER, \
           video_resolution TEXT, video_aspect REAL, audio_codec TEXT, video_codec TEXT, \
           address TEXT, thumbnail TEXT, protocol TEXT, \
           schedule_id INTEGER)"
    db_cursor.execute(sql)
    sql="DELETE FROM channels"
    db_cursor.execute(sql)
    
    addon_log(data['date'])
    for group in data['groups']:
      addon_log(group['id'] + " " + group['name'])
      #sql = "INSERT INTO categories \
      #       VALUES ('%d', '%s')" % \
      #       (int(group['id']), str(group['name']))
      db_cursor.execute("INSERT INTO categories \
                         VALUES (?, ?)",
                         (group['id'], group['name']))

      for channel in group['channels']:
        addon_log(str(channel['id'])+" "+str(channel['name'].decode('utf8').encode('utf8'))+" "+ str(channel['language'])+" "+str(channel['status']))
                
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
          
        #sql = "INSERT INTO channels \
        #       VALUES ('%d', '%d', '%s', '%s', '%s', '%d', \
        #               '%s', '%f2', '%s','%s', \
        #               '%s', '%s', '%s', \
        #               '%d' )" % \
        #       ( int(channel['id']), int(group['id']), str(channel['name']), str(channel['country']), str(channel['language']), int(channel['status']), \
        #         str(video_resolution), float(video_aspect), str(audio_codec), str(video_codec), \
        #         str(channel['address']), str(thumbnail), str(channel['protocol']), \
        #         int(schedule_id) )
        db_cursor.execute( \
              "INSERT INTO channels \
               VALUES (?, ?, ?, ?, ?, ?, \
                       ?, ?, ?, ?, \
                       ?, ?, ?, \
                       ? )" ,
               ( channel['id'], group['id'], channel['name'], channel['country'], channel['language'], channel['status'], \
                 video_resolution, video_aspect, audio_codec, video_codec, \
                 channel['address'], thumbnail, channel['protocol'], \
                 schedule_id) )
        
    db_connection.commit()

def CAT_LIST(force=False):
  if force==False:
    if not os.path.isfile(CHAN_LIST):
      addon_log('channels first download')
      Downloader(CHAN_LIST_URL, CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054))  #Downloading Channel list
      parse_ch_data()
    else:
      now_time = time.mktime(datetime.now().timetuple())
      time_created = os.stat(CHAN_LIST)[8]  # get local play list modified date
      if CHAN_LIST_EXPIRE>0 and now_time - time_created > CHAN_LIST_EXPIRE:
        addon_log('channels update')
        Downloader(CHAN_LIST_URL, CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
        parse_ch_data()
  else:
    Downloader(CHAN_LIST_URL, CHAN_LIST, addon.getLocalizedString(30053), addon.getLocalizedString(30054)) #Downloading Channel list
    parse_ch_data()
  
  #try:
  #  parse_ch_data()
  #except Exception as inst:
  #  addon_log(inst)
  #  pass
  
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
      addDir(name, str(id), CHAN_LIST, 1)

  #xbmc.executebuiltin("Container.SetViewMode(500)")
  xbmc.executebuiltin("Container.SetViewMode(51)")
  
def CHANNEL_LIST(name, cat_id, schedule=False):
  addon_log(name);
  try:
    #sql = "SELECT id, name, country, language, status, \
    #       video_resolution, video_aspect, audio_codec, video_codec, \
    #       address, thumbnail, protocol, \
    #       schedule_id \
    #       FROM channels \
    #       WHERE id_cat = %d" % \
    #       (int(cat_id))
    db_cursor.execute( 'SELECT id, name, country, language, status, \
                        video_resolution, video_aspect, audio_codec, video_codec, \
                        address, thumbnail, protocol, \
                        schedule_id \
                        FROM channels \
                        WHERE id_cat = ?', \
                        (cat_id,) )
    rec=db_cursor.fetchall()  
  except Exception as inst:
    addon_log(inst)
    xbmcgui.Dialog().ok(addon.getLocalizedString(30300), addon.getLocalizedString(30301), str(inst))  #Cannot parse channel list !
    
  if len(rec)>0:
    for id, name, country, language, status, \
        video_resolution, video_aspect, audio_codec, video_codec, \
        address, thumbnail, protocol, \
        schedule_id in rec:
      
      #filter by country and language
      if( (((country != '') and (addon.getSetting('country_'+country) == 'true')) or
           ((country == '') and (addon.getSetting('country_none') == 'true')) ) and
           (((language != '') and (addon.getSetting('lang_'+language) == 'true')) or
           ((language == '') and (addon.getSetting('lang_none') == 'true')) )
        ):
        
        chan_name = name
        chan_url = address.strip()
        
        protocol = protocol.strip()
        if protocol=='sop':
          protocol = '[COLOR lightgreen]'+protocol+'[/COLOR]'
        else:
          protocol = '[COLOR yellow]'+protocol+'[/COLOR]'
        chan_thumb = thumbnail.strip()
        #addon_log(chan_thumb)
        chan_status = status
        
        if (((SHOW_OFFLINE_CH=='true') and (int(chan_status)==1)) or (int(chan_status)!=1)): #if we show or not offline channels based on settings
          logo_name = chan_name.replace(' ', '').lower()
          
          chan_name_formatted ="[B][COLOR blue]"+chan_name+"[/COLOR][/B]"
          chan_name_formatted += " ("+protocol
          if(video_codec != ''):
            chan_name_formatted += " "+video_codec
          chan_name_formatted += ")"
          if int(chan_status)==1: chan_name_formatted += " [COLOR red]"+addon.getLocalizedString(30063)+"[/COLOR]"  #Offline
          
          thumb_path=""
          if chan_thumb and chan_thumb != "":
            fileName, fileExtension = os.path.splitext(chan_thumb)
            fileName=fileName.split("/")[-1]
            if fileName != "":
              #thumb_path=os.path.join(ADDON_PATH,"logos",fileName+fileExtension)
              thumb_path=os.path.join(ADDON_PATH,"logos",logo_name+fileExtension)
    
            if not os.path.isfile(thumb_path):
              if fileName != "":
                Downloader(chan_thumb, thumb_path, fileName+fileExtension, addon.getLocalizedString(30055)) #Downloading Channel Logo
    
          #schedule
          if (schedule_id != 0) and \
             (schedule or (addon.getSetting('schedule_ch_list') == 'true')) \
             and (DISABLE_SCHEDULE != 'true'):
            if (schedule): #update all by context menu
              update_all = True
            elif(addon.getSetting('schedule_ch_list') == 'true'): #update all when we display channel list
              update_all = False
            grab_schedule(schedule_id, chan_name, update_all=update_all)
            
          if (DISABLE_SCHEDULE != 'true') and (int(cat_id) < 200):
            schedule_txt = load_schedule(chan_name)
            chan_name_formatted += "   " + schedule_txt
    
          addLink(chan_name_formatted, chan_name, chan_url, str(schedule_id), name, cat_id, 2, thumb_path, "", len(rec))
  
  xbmc.executebuiltin("Container.SetViewMode(51)")

def STREAM(name, iconimage, url, sch_ch_id):
  if(url == None):
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass
    return False
  
  if (sch_ch_id != None) and (DISABLE_SCHEDULE != 'true'):
    grab_schedule(sch_ch_id, name)
    
  #addon_log(name)
  #addon_log(iconimage)
  
  if not iconimage or iconimage == "": iconimage="DefaultVideo.png"
  listitem = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
  listitem.setLabel(name)
  listitem.setInfo('video', {'Title': name})
  
  if url[0:6]=="sop://": #play sopcast stream
    try:
      cmd = [SPSC, url, str(LOCAL_PORT), str(VIDEO_PORT), "> /dev/null &"]
      if(ARM):
        cmd = QEMU_SPSC + cmd
      #addon_log(cmd)
      spsc = subprocess.Popen(cmd, shell=False, bufsize=BUFER_SIZE, stdin=None, stdout=None, stderr=None)
      
      xbmc.sleep(int(addon.getSetting('wait_time')))
      
      res=False
      counter=50
      #while counter > 0 and os.path.exists("/proc/"+str(spsc.pid)):
      while counter > 0 and sop_pid_exists(spsc.pid):
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        xbmc.sleep(400)
        counter -= 1
        try:
          addon_log(LOCAL_URL);
          urllib2.urlopen(LOCAL_URL)
          counter=0
          res=sop_sleep(200 , spsc.pid)
          break
        except:pass
      
      addon_log(res)
        
      if res:
        player = streamplayer(xbmc.PLAYER_CORE_AUTO , spsc_pid=spsc.pid, name=name)
        addon.setSetting('player_status', 'play')
        player.play(LOCAL_URL, listitem)
        
        keep_allive(player)
        
        #watching sop process and restarting the player if it dies
        #watch_sop_thread(spsc.pid, name, listitem)
        
      #elif not os.path.exists("/proc/"+str(spsc.pid)):
      elif not sop_pid_exists(spsc.pid):
        try: xbmc.executebuiltin("Dialog.Close(all,true)")
        except: pass
        try:
          urllib2.urlopen("http://www.google.com")
          if NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30057), "",1))  #Channel is offline
        except:
          if NOTIFY_OFFLINE == "true": xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30058), "",1)) #Network is offline
      elif NOTIFY_OFFLINE == "true": 
        try: xbmc.executebuiltin("Dialog.Close(all,true)")
        except: pass
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (addon.getLocalizedString(30059), "", 1)) #Channel initialization failed
        try: stop_spsc(spsc.pid)
        except: pass
    
    except Exception as inst:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30060), str(type(inst)),str(inst),"")
      addon_log(str(inst))
      try:
        stop_spsc()
      except: pass
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass
      
  else: #play direct stream
    try:
      player = streamplayer(xbmc.PLAYER_CORE_AUTO, name=name)
      addon.setSetting('player_status', 'play')
      player.play(url, listitem)
      keep_allive(player)
      
    except Exception as inst:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30060), str(type(inst)),str(inst),"")
      try: xbmc.executebuiltin("Dialog.Close(all,true)")
      except: pass
  
def keep_allive(player):
  xbmc.sleep(500)
              
  #KEEP SCRIPT ALLIVE
  #while player.isPlaying():
  while (addon.getSetting('player_status')=='play'):
    addon_log('ALLIVE')
    xbmc.sleep(500)
    
  #xbmc.sleep(1000)
  
  try: xbmc.executebuiltin("Dialog.Close(all,true)")
  except: pass

# this function will sleep only if the sop is running
def sop_pid_exists(pid):
  try:
    os.kill(pid, 0)
  except OSError:
    return False
  else:
    return True

def sop_sleep(time , spsc_pid):
  counter=0
  increment=200
  #path="/proc/%s" % str(spsc_pid)
  
  #addon_log('proc exists')
  #addon_log(os.path.exists(path))
  try:
    #while counter < time and spsc_pid>0 and not xbmc.abortRequested and os.path.exists(path):
    while counter < time and spsc_pid>0 and not xbmc.abortRequested and sop_pid_exists(spsc_pid):
      counter += increment
      xbmc.sleep(increment)
  except Exception as inst:
    addon_log(inst)
    if DEBUG == 'true': xbmc.executebuiltin("Notification(%s,%s,%i)" % (str(type(inst)), str(inst), 5))
    return True
  if counter < time: return False
  else: return True
  
#watching sop process and restarting the player if it dies
def watch_sop_thread(spsc_pid, name, listitem):
  xbmc.sleep(100)
  sop_sleep(4000 , spsc_pid)
  
  #addon_log(spsc_pid)
  #addon_log(name)
  #addon_log(listitem)  
    
  #while os.path.exists("/proc/"+str(spsc_pid)) and not xbmc.abortRequested:
  while sop_pid_exists(spsc_pid) and not xbmc.abortRequested:
    addon_log("CHECK ONLINE")
    addon_log(SPSC_STOPED)
    
    # check if player stoped and restart it
    if not xbmc.Player(xbmc.PLAYER_CORE_AUTO).isPlaying():
      if not sop_sleep(1000 , spsc_pid): break
      if not xbmc.Player(xbmc.PLAYER_CORE_AUTO).isPlaying():
        player = streamplayer(xbmc.PLAYER_CORE_AUTO , spsc_pid=spsc_pid, name=name)
        player.play(LOCAL_URL, listitem)
        addon_log("RESTART PLAYER")

      sop_sleep(2000 , spsc_pid)
    sop_sleep(300 , spsc_pid)
    
def stop_spsc(pid=None):
  if(pid != None) :
    addon_log('KILL PID = '+str(pid))
    os.kill(pid, 9)
  else :
    addon_log('KILL ALL SOPCAST')
    if(ARM) :
      os.system("killall -9 "+QEMU)
    else :
      os.system("killall -9 "+SPSC_BINARY)

class streamplayer(xbmc.Player):
  def __init__( self , *args, **kwargs):
    self.spsc_pid=kwargs.get('spsc_pid')
    self.name=kwargs.get('name')
    addon_log('INIT PLAYER')

  def onPlayBackStarted(self):
    addon_log('START')
    addon_log(xbmc.getInfoLabel('VideoPlayer.VideoCodec'))
    addon_log(xbmc.getInfoLabel('VideoPlayer.AudioCodec'))
    
    ## this will kill the sopcast if we changed the media
    if xbmc.Player(xbmc.PLAYER_CORE_AUTO).getPlayingFile() != LOCAL_URL:
      try: stop_spsc(self.spsc_pid)
      except: pass
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    
    if DISABLE_SCHEDULE!='true':
      #display schedule active event
      active_event = load_active_event(self.name)
      if active_event:
        xbmc.executebuiltin("Notification(%s,%s,%i)" % (active_event, "", 10000))
    
  def onPlayBackEnded(self):
    addon_log('END')
    #xbmc.executebuiltin('Container.Refresh()')
    try: stop_spsc(self.spsc_pid)
    except: pass
    addon.setSetting('player_status', 'end')
    
  def onPlayBackStopped(self):
    addon_log('STOP')
    #xbmc.executebuiltin('Container.Refresh()')
    try: stop_spsc(self.spsc_pid)
    except: pass
    addon.setSetting('player_status', 'stop')

#class EPG(xbmcgui.WindowXMLDialog):
#  def __init__( self , *args, **kwargs):
#    xbmcgui.WindowXMLDialog.__init__( self , *args, **kwargs)
    #self.spsc_pid=kwargs.get('spsc_pid')
    
#  
#  def onInit(self):
#    pass
#  
#  def onControl(self,control):
#    pass
#
#  def onClick(self,controlId):
#	  pass
#	
#  def onFocus( self, controlId ):
#	  pass

def is_exe(fpath):
  if os.path.isfile(fpath):
    if (os.access(fpath, os.X_OK) != True) :
      st = os.stat(fpath)
      os.chmod(fpath, st.st_mode | stat.S_IEXEC)

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################

addon_log('------------- START -------------')  

params=get_params()

##########################################sopcast data
SPSC_BINARY = "sp-sc-auth"

#raspberry pi
QEMU = "qemu-i386"  #for raspberry pi to issue kill command
ARM = False
if(os.uname()[4][:3] == 'arm'):
  ARM = True
##############
  
if ARM == False :
  SPSC = os.path.join(ADDON_PATH, 'bin/linux_i386/sopcast', SPSC_BINARY)
  
  #make executables
  is_exe(SPSC)
  
  ## get system default env PATH
  #pathdirs = os.environ['PATH'].split(os.pathsep)
  ## looking for (the first match) sp-sc-auth binary in the system default path
  #for dir in pathdirs:
  #  if os.path.isdir(dir):
  #    if os.path.isfile(os.path.join(dir,SPSC_BINARY)):
  #      SPSC = os.path.join(dir,SPSC_BINARY)
  #      break
elif ARM == True:
  SOPCAST_ARM_PATH =  addon.getSetting('sopcast_arm_path')
  if(SOPCAST_ARM_PATH == '') :
    SOPCAST_ARM_PATH = os.path.join(ADDON_PATH, 'bin/arm/sopcast')
  
  #make executables
  is_exe(os.path.join(SOPCAST_ARM_PATH, QEMU))
    
  QEMU_SPSC = [os.path.join(SOPCAST_ARM_PATH, QEMU), os.path.join(SOPCAST_ARM_PATH, "lib/ld-linux.so.2"), "--library-path", os.path.join(SOPCAST_ARM_PATH, "lib")]
  SPSC = os.path.join(SOPCAST_ARM_PATH, SPSC_BINARY)
  #/storage/sopcast/qemu-i386 /storage/sopcast/lib/ld-linux.so.2 --library-path /storage/sopcast/lib /storage/sopcast/sp-sc-auth 2>&- $1 $2 $3
    
LOCAL_PORT =  addon.getSetting('local_port')
VIDEO_PORT =  addon.getSetting('video_port')
BUFER_SIZE = int(addon.getSetting('buffer_size'))
##########################################sopcast data

LANGUAGE = 'en'
LOCAL_URL = "http://localhost:"+str(VIDEO_PORT)+"/?"
CHAN_LIST_URL = addon.getSetting('chan_list_url')
parse_object = urlparse(CHAN_LIST_URL)
f_name = basename(parse_object[2]); #file name of the channel list
CHAN_LIST = os.path.join(ADDON_PATH, f_name) #full path of the channel list
CHAN_LIST_EXPIRE =  int(addon.getSetting('chan_list_expire'))*60*60
CHANNELS_DB = os.path.join(ADDON_PATH,'channels.sqlite')
db_connection=sqlite3.connect(CHANNELS_DB)
db_cursor=db_connection.cursor()

#DISABLE_SCHEDULE = addon.getSetting('disable_schedule')
SHOW_OFFLINE_CH = addon.getSetting('show_offline_ch')

NOTIFY_OFFLINE = "true"

addon_log(CHAN_LIST_URL)
addon_log(CHAN_LIST)

mode=None

try:
  mode=int(params["mode"])
except:
  pass

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
  
addon_log(mode)
if mode==None: #list categories
  CAT_LIST()
elif mode==1:  #list channels
  CHANNEL_LIST(name, cat_id)
elif mode==2:  #play stream
  if xbmc.Player(xbmc.PLAYER_CORE_AUTO).isPlaying():
    stop_spsc()
  
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).stop()
    try: xbmc.executebuiltin("Dialog.Close(all,true)")
    except: pass
      
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    xbmc.sleep(800)
    if cat_id == "200" :
      url = grab_vk_stream(name, url)
    if cat_id == "201" or cat_id == "202" :
      url = grab_fu_stream(name, url)
    STREAM(name, iconimage, url, sch_ch_id)
  else:
    stop_spsc()
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    if cat_id == "200" :
      url = grab_vk_stream(name, url)
    if cat_id == "201" or cat_id == "202" :
      url = grab_fu_stream(name, url)
    STREAM(name, iconimage, url, sch_ch_id)
elif mode==3:  #refresh schedule
  if sch_ch_id != None:
    grab_schedule(sch_ch_id, name, force=True)
    xbmc.executebuiltin('Container.Refresh()')
elif mode==4:  #refresh channel list
  CAT_LIST(force=True)
  xbmc.executebuiltin('Container.Refresh()')
elif mode==5:  #refresh all schedules
  CHANNEL_LIST(name, cat_id, schedule=True)
  xbmc.executebuiltin('Container.Refresh()')
#elif mode==6:  #EPG
#  addon_log('epg');
#  mydisplay = EPG("custom_help.xml",ADDON_PATH)
#  mydisplay.doModal()
#  del mydisplay

db_connection.close()

xbmcplugin.endOfDirectory(int(sys.argv[1]))