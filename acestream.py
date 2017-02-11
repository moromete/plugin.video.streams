# -*- coding: utf-8 -*-

""" Plexus  (c)  2015 enen92

    This file contains the function that brigdes the addon to the acecore.py file
    
    Functions:
    
    load_local_torrent() -> Load a local .torrent file
    acestreams(name,iconimage,chid) -> Function that interprets the received url (acestream://,*.acelive,ts://) and sends it to acestreams_builtin
    acestreams_builtin(name,iconimage,chid -> Bridge to acecore.py file
   	

"""

#ace.acestreams(name,iconimage,url)
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import os
import urllib,xbmcvfs,os,subprocess

addon_id = 'plugin.video.streams'
art = os.path.join('resources','art')
settings = xbmcaddon.Addon(id=addon_id)
addonpath = settings.getAddonInfo('path').decode('utf-8')
mensagemok = xbmcgui.Dialog().ok
mensagemprogresso = xbmcgui.DialogProgress()
addon_icon    = settings.getAddonInfo('icon')
      
def translate(text):
      return settings.getLocalizedString(text).encode('utf-8')

aceport=62062

def load_local_torrent():
	torrent_file = xbmcgui.Dialog().browse(1, "Choose the local torrent file",'video', '.torrent')
	if torrent_file:
		if xbmc.getCondVisibility('system.platform.windows'):
			acestreams("Local .torrent ("+str("file:\\" + torrent_file) +")","",'file:\\' + torrent_file)
		else:
			acestreams("Local .torrent ("+str("file://" + torrent_file) +")","",'file://' + urllib.quote(torrent_file))
	else: pass

def acestreams(name,iconimage,chid):
	if not iconimage: iconimage=os.path.join(addonpath,'resources','art','acestream-menu-item.png')
	else: iconimage = urllib.unquote(iconimage)
	acestreams_builtin(name,iconimage,chid)

def acestreams_builtin(name,iconimage,chid):
    from acecore import TSengine as tsengine
    xbmc.executebuiltin('Action(Stop)')
    lock_file = xbmc.translatePath('special://temp/'+ 'ts.lock')
    if xbmcvfs.exists(lock_file):
    	xbmcvfs.delete(lock_file)
    if chid != '':
        chid=chid.replace('acestream://','').replace('ts://','')
        print("Starting Player Ace hash: " + chid)
        TSPlayer = tsengine()
        out = None
        if chid.find('http://') == -1 and chid.find('.torrent') == -1:
            out = TSPlayer.load_torrent(chid,'PID',port=aceport)
        elif chid.find('http://') == -1 and chid.find('.torrent') != -1:
            out = TSPlayer.load_torrent(chid,'TORRENT',port=aceport)
        else:
            out = TSPlayer.load_torrent(chid,'TORRENT',port=aceport)
        if out == 'Ok':
            TSPlayer.play_url_ind(0,name + ' (' + chid + ')',iconimage,iconimage)
            TSPlayer.end()
            return
        else:    
            mensagemok("Streams","Torrent not available or invalid")
            TSPlayer.end()
            return
    else:
        mensagemprogresso.close()
