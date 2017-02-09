# -*- coding: utf-8 -*-

""" Plexus  (c)  2015 enen92
    This file contains the acestream console of the addon. Initial versions were coded by Nouismons and so, this file is based on his work.
    
    Classes:
    
    Logger() -> Log class
    _TSPlayer(xbmc.Player) -> Inheritance of the xbmc.Player class for acestreams
    TSengine() -> Acestreamengine class, start functions, etc
    TSServ(threading.Thread) ->  Acestreamengine service class
    OverlayText(object) -> Overlaytext displayed on player
        
"""

import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import xbmcvfs
import httplib
import urllib
import urllib2
import re
import sys
import subprocess
import os
import socket
import threading
import time
import random
import json

""" Fixed variables """
addon_id = 'plugin.video.streams'
art = os.path.join('resources','art')
settings = xbmcaddon.Addon(id=addon_id)
addonpath = settings.getAddonInfo('path').decode('utf-8')
versao = settings.getAddonInfo('version')
mensagemok = xbmcgui.Dialog().ok
mensagemprogresso = xbmcgui.DialogProgress()
pastaperfil = xbmc.translatePath(settings.getAddonInfo('profile')).decode('utf-8')
addon_icon = settings.getAddonInfo('icon')

aceport=62062
server_ip="127.0.0.1"
save=False
alog=False
pwin=False
posx=False


""" Function and class list """


def show_Msg(heading, message, times = 3000, pics = addon_icon):
    try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading.encode('utf-8'), message.encode('utf-8'), times, pics.encode('utf-8')))
    except Exception, e:
        print( '[%s]: ShowMessage: Transcoding UTF-8 failed [%s]' % (addon_id, e), 2 )
        try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading, message, times, pics))
        except Exception, e:
            print( '[%s]: ShowMessage: exec failed [%s]' % (addon_id, e), 3 )

#class Logger():
    #def __init__(self,Name):
        #self.started=False
        #self.name=Name
        #self.link=None
    #def out(self,txt):
        #if alog:
            #print "%s:%s"%(self.name,txt)


class _TSPlayer(xbmc.Player):

    def __init__( self):
        self.started=False
        #self.log=Logger("TSPlayer")
        #self.log.out('init')
        self.active=True
        self.link=None
        self.vod=True
        self.duration=None
        self.coms=[]
    #def onPlayBackPaused( self ):
        #self.log.out('paused')
        
    def onPlayBackStarted( self ):
        watcher_thread = threading.Thread(name='acestream_watcher', target=ace_control_thread).start()
        xbmc.executebuiltin('XBMC.ActivateWindow("fullscreenvideo")')
        self.started=True
        #self.log.out('started')
        if self.vod:
            try: 
                self.duration= int(xbmc.Player().getTotalTime()*1000)
                comm='DUR '+self.link.replace('\r','').replace('\n','')+' '+str(self.duration)
                self.coms.append(comm)
            except: pass
        
        comm='PLAYBACK '+self.link.replace('\r','').replace('\n','')+' 0'
        self.coms.append(comm)
        xbmc.sleep(2500)
        
    def onPlayBackEnded(self):
        #self.log.out("play ended")
        self.active=False
        comm='PLAYBACK '+self.link.replace('\r','').replace('\n','')+' 100'
        self.coms.append(comm)
        
    def onPlayBackStopped(self):
        #self.log.out("play stop")
        self.active=False
        try:lat123._close()
        except:pass

    #def __del__(self):
        #self.log.out('delete')
    


class TSengine():

    def __init__(self):
        xbmc.Player().stop()
        #self.log=Logger("TSEngine")
        #self.push=Logger('OUT')
        self.alive=True
        self.progress = xbmcgui.DialogProgress()
        self.player=None
        self.files={}
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(3)
        self.progress.create("Streams","Starting...")
        self.tsserv =None
        self.conn=False
        self.title=None
        self.filename=None
        self.mode=None
        self.url=None
        self.local=False
        self.saved=False
        self.canceled = False
        self.pos=[25,50,75,100]
        l=False
        while xbmc.Player().isPlaying(): 
            l=True
            if xbmc.abortRequested:
                self.log.out("XBMC asked to abort request")
                return False
            if self.progress.iscanceled():
                self.canceled = True
                return False
            xbmc.sleep(300)
        
        settings.setSetting('active','1')
        if l: xbmc.sleep(500)

    def ts_init(self):
        self.tsserv = TSServ(self._sock)
        self.tsserv.start()
        comm="HELLOBG"
        self.TSpush(comm)
        self.progress.update(0,"Awaiting response"," ")
        while not self.tsserv.version:
            if xbmc.abortRequested:
                self.canceled = True
                #self.log.out("XBMC asked to abort request")
                return False
            if self.progress.iscanceled():
                self.canceled = True
                return False
            time.sleep(1)
        ready='READY'
        if self.tsserv.key:
            import hashlib
            sha1 = hashlib.sha1()
            pkey=self.tsserv.pkey
            sha1.update(self.tsserv.key+pkey)
            key=sha1.hexdigest()
            pk=pkey.split('-')[0]
            key="%s-%s"%(pk,key)
            ready='READY key=%s'% key
        if self.progress.iscanceled():
            self.canceled = True
            self.err=1
            return False        
        self.TSpush(ready)
        return True
    
    def sm(self,msg):
        show_Msg('AceStream',msg)
    
    def connect(self):
        server_ip='127.0.0.1'
        servip='127.0.0.1'
        aceport=62062
        #self.log.out('Trying to connect')
        self.progress.update(0,"Connecting",' ')
        #self.log.out('try to connect to Linux engine')
        #self.log.out('Connecting to %s:%s'%(servip,aceport))
        try:
           self._sock.connect((servip, aceport))
           #self.log.out('Connected to %s:%s'%(servip,aceport))
           return True
        except:
            res=self.startLin()
            if not res: return False
        i=40
        while (i>1):
            self.progress.update(0,"Starting AceStream Engine.","Inital wait:" + str('%s'%i) + " seconds" )
            try:
                self._sock.connect((servip, aceport))
                #self.log.out('Connected to %s:%s'%(servip,aceport))     
                i=0
                return True
            except:
                #self.log.out('Failed to connect to %s:%s'%(servip,aceport))
                pass
            if self.progress.iscanceled():
                self.canceled = True
                return False
                break
            i=i-1
            xbmc.sleep(1000)

        self.sm('Cant connect')
        return False

    def startLin(self):
        #self.log.out('try to start Lin engine')
        import subprocess
        command = ["sh",os.path.join(pastaperfil,"acestream","start_acestream.sh"),"--client-console"]
        self.proc = subprocess.Popen(command)
        #self.log.out('Engine starting')
        return True
      
    def TSpush(self,command):
        #self.push.out(command)
        try:
            self._sock.send(command+'\r\n')
        except: 
            #self.push.out("!!!Error!!!")
            pass
    
    def get_link(self, index=0, title='', icon='', thumb=''):     
        self.title=title
        #self.log.out("play")
        self.tsserv.ind=index
        self.progress.update(89,"Playing",'')
        for k,v in self.files.iteritems():
            if v==index: self.filename=urllib.unquote(k).replace('/','_').replace('\\','_')
        try:    
            avail=os.path.exists(self.filename.decode('utf-8'))
        except:
            try:
                avail=os.path.exists(self.filename)
                self.filename=self.filename.encode('utf-8')
            except: self.filename='temp.avi'
        #self.log.out('Starting file:%s'%self.filename)
        
        self.filename=None
        save=False
        
        #self.log.out('Get filename to save:%s'%self.filename)
        spons=''
        if self.mode!='PID': spons=' 0 0 0'
        comm='START '+self.mode+ ' ' + self.url + ' '+ str(index) + spons
        self.TSpush(comm)
        self.progress.update(89,"Link received",'')
        while not self.tsserv.got_url and not self.progress.iscanceled() and not self.tsserv.err:
            self.progress.update(int(self.tsserv.proc),self.tsserv.label,self.tsserv.line)
            xbmc.sleep(200)
            
            if self.progress.iscanceled():
                self.canceled = True
            
            if xbmc.abortRequested:
                #self.log.out("XBMC is shutting down")
                self.canceled = True
                break
        if self.tsserv.err:
            self.sm('Failed to load file')
            self.canceled = True
        
        self.progress.update(100,"Playing",'')
        save=False

        if self.tsserv.event and save:
            self.progress.update(0,"Saving file"," ")
            comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename))
            self.TSpush(comm)
            self.tsserv.event=None
            succ=True

            while not os.path.exists(self.filename.decode('utf-8')) and not self.progress.iscanceled():
                if xbmc.abortRequested or self.progress.iscanceled():
                    #self.log.out("XBMC asked to abort request")
                    succ=False
                    self.canceled = True
                    break
                xbmc.sleep(200)
            if not succ: return False
            self.tsserv.got_url=self.filename.decode('utf-8')
            self.local=True
            
        self.active=True
        self.progress.close()
        return self.tsserv.got_url
    
    def play_url_ind(self, index=0, title='', icon='', thumb=''):
        self.lnk=self.get_link(index,title,icon,thumb)
        if not self.lnk: return False
        if self.progress:self.progress.close()
        item = xbmcgui.ListItem(title,iconImage="DefaultVideo.png", thumbnailImage=thumb)
        item.setPath(path=self.lnk)
        global lat123 
        lat123 = OverlayText()
        xbmcplugin.setResolvedUrl(int(sys.argv[1]),True,item)
        xbmc.sleep(100)
        self.player=_TSPlayer()
        self.player.vod=True
        self.player.link=self.tsserv.got_url
        #self.log.out('play')
        self.player.link=self.lnk
        if self.progress:self.progress.close()
        if self.local: 
            if int(sys.argv[1]) < 0:
                xbmc.Player().play(self.lnk,item)
        else:
            xbmc.sleep(50)
            if int(sys.argv[1]) < 0:
                self.player.play(self.lnk,item)
            show_window = False
            while self.player.active and not self.local:
                if show_window == False and xbmc.getCondVisibility('Window.IsActive(videoosd)'):
                     lat123.show()
                     show_window = True
                elif not xbmc.getCondVisibility('Window.IsActive(videoosd)'):
                     try:
                        lat123.hide()
                     except: pass
                     show_window = False
                self.loop()
                xbmc.sleep(300)
                if xbmc.abortRequested:
                    self.canceled = True
                    #self.log.out("XBMC asked to abort request")
                    break
            #self.log.out('ended play')
      
    def loop(self):
        pos=self.pos
        
        if len(self.player.coms)>0:
            comm=self.player.coms[0]
            self.player.coms.remove(comm)
            self.TSpush(comm)
        
        if self.player.isPlaying():
            if self.player.getTotalTime()>0: cpos= int((1-(self.player.getTotalTime()-self.player.getTime())/self.player.getTotalTime())*100)
            else: cpos=0
            if cpos in pos: 
                pos.remove(cpos)
                comm='PLAYBACK '+self.player.link.replace('\r','').replace('\n','')+' %s'%cpos
                self.TSpush(comm)
        
        if self.tsserv.event and save:
            #self.log.out('Try to save file in loop')
            comm='SAVE %s path=%s'%(self.tsserv.event[0]+' '+self.tsserv.event[1],urllib.quote(self.filename))
            self.TSpush(comm)
            self.tsserv.event=None
            succ=True
            self.saved=True
        
        if self.saved and self.player.started:
            #self.log.out('saving content')
            if  self.player.isPlaying() and os.path.exists(self.filename.decode('utf-8')): 
                xbmc.sleep(10000)
                #self.log.out('Start local file')
                self.tsserv.got_url=self.filename
                self.local=True
                
                self.sm('Start Local File')
                try: time1=self.player.getTime()
                except: time1=0
                
                i = xbmcgui.ListItem("***%s"%self.title)
                i.setProperty('StartOffset', str(time1))
                #self.log.out('Play local file')
                self.local=True
                self.player.active=False 
        

    def load_torrent(self, torrent, mode, host=server_ip, port=aceport ):
        self.mode=mode
        self.url=torrent
        if not self.connect(): 
            
            return False
        if not self.ts_init(): 
            self.sm('Initialization Failed')
            return False
        self.conn=True
        self.progress.update(0,"Downloading","")
        
        if mode!='PID': spons=' 0 0 0'
        else: spons=''
        comm='LOADASYNC '+ str(random.randint(0, 0x7fffffff)) +' '+mode+' ' + torrent + spons
        self.TSpush(comm)

        while not self.tsserv.files and not self.progress.iscanceled():
            if xbmc.abortRequested:
                #self.log.out("XBMC is shutting down")
                self.canceled = True
                break
            if self.tsserv.err:
                self.canceled = True
                #self.log.out("Failed to load files")
                break
            xbmc.sleep(200)
        if self.progress.iscanceled():
            self.canceled = True 
            return False
        if not self.tsserv.files: 
            self.sm('Failed to load list files')
            self.canceled = True
            return False
        self.filelist=self.tsserv.files
        self.file_count = self.tsserv.count
        self.files={}
        self.progress.update(89,"Loading...",'')
        if self.file_count>1:
            flist=json.loads(self.filelist)
            for list in flist['files']:
                self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]
        elif self.file_count==1:
            flist=json.loads(self.filelist)
            list=flist['files'][0]
            self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]

        self.progress.update(100,"Loading acestream",'')
        
        return "Ok"

    def end(self):
        self.active=False
        comm='SHUTDOWN'
        if self.conn:self.TSpush(comm)
        #self.log.out("Ending")
        try: self._sock.shutdown(socket.SHUT_WR)
        except: pass
        if self.tsserv: self.tsserv.active=False
        if self.tsserv: self.tsserv.join()
        #self.log.out("end thread")
        self._sock.close()
        #self.log.out("socket closed")
        if self.progress:self.progress.close()

        try:lat123._close()
        except:pass 
        
        if self.canceled: stop_aceengine()         

        
    def __del__(self):
        settings.setSetting('active','0')
        
class TSServ(threading.Thread):

    def __init__(self,_socket):
        self.pkey='n51LvQoTlJzNGaFxseRK-uvnvX-sD4Vm5Axwmc4UcoD-jruxmKsuJaH0eVgE'
        threading.Thread.__init__(self)
        #self.log=Logger("TSServer")
        #self.inc=Logger('IN')
        #self.log.out("init")
        self.sock=_socket
        self.daemon = True
        self.active = True
        self.err = False
        self.buffer=65020
        self.temp=""
        self.msg=None
        
        self.version=None

        self.fileslist=None
        self.files=None
        self.key=None
        self.count=None
        self.ind=None
        
        self.got_url=None
        self.event=None
        self.proc=0
        self.label=''
        self.line=''
        self.pause=False
    def run(self):
        while self.active and not self.err:

            try:
                self.last_received=self.sock.recv(self.buffer)
            except: self.last_received=''

            ind=self.last_received.find('\r\n')
            cnt=self.last_received.count('\r\n')

            if ind!=-1 and cnt==1:
                self.last_received=self.temp+self.last_received[:ind]
                self.temp=''
                self.exec_com()
            elif cnt>1:
                fcom=self.last_received
                ind=1
                while ind!=-1:
                    ind=fcom.find('\r\n')
                    self.last_received=fcom[:ind]
                    self.exec_com()
                    fcom=fcom[(ind+2):]
            elif ind==-1: 
                self.temp=self.temp+self.last_received
                self.last_received=None



        #self.log.out('Daemon Dead')
                
    def exec_com(self):
        
        #self.inc.out(self.last_received)
        line=self.last_received
        comm=self.last_received.split(' ')[0]
        params=self.last_received.split(' ')[1::]
        self.msg=line
        if comm=='HELLOTS':
            try: self.version=params[0].split('=')[1]
            except: self.version='1.0.6'
            try: 
            	match = re.compile('key=(.*)').findall(line)
            	self.key = match[0].split(' ')[0]
            except: self.key=None
        elif comm=='LOADRESP':
            fil = line
            ll= fil[fil.find('{'):len(fil)]
            self.fileslist=ll

            json_files=json.loads(self.fileslist)
            try:
                aa=json_files['infohash']
                if json_files['status']==2:
                    self.count=len(json_files['files'])
                if json_files['status']==1:
                    self.count=1
                if json_files['status']==0:
                    self.count=None
                self.files=self.fileslist.split('\n')[0]
                self.fileslist=None
                #self.log.out("files:%s"%self.files) 
            except:
                self.count=None
                self.fileslist=None
                self.err=True
        elif comm=='EVENT':
            if self.last_received.split(' ')[1]=='cansave':
                event=self.last_received.split(' ')[2:4]
                ind= event[0].split('=')[1]
                if int(ind)==int(self.ind): self.event=event
            if self.last_received.split(' ')[1]=='getuserdata':
                self.sock.send('USERDATA [{"gender": 1}, {"age": 3}]\r\n')
                
        elif comm=='START' or comm=='PLAY': 
            servip="127.0.0.1"
            self.got_url=self.last_received.split(' ')[1].replace('127.0.0.1',servip) # 
            #self.log.out('Get Link:%s'%self.got_url)
            self.params=self.last_received.split(' ')[2:]
            #if 'stream=1' in self.params: self.log.out('Live Stream')
            #else: self.log.out('VOD Stream')
        elif comm=='RESUME': self.pause=0
        elif comm=='PAUSE': self.pause=1   
        if comm=="STATUS": self.showStats(line)   
        
    def showStats(self,params):
        params=params.split(' ')[1]
        ss=re.compile('main:[a-z]+',re.S)
        s1=re.findall(ss, params)[0]
        st=s1.split(':')[1]
        self.proc=0
        self.label=" "
        self.line=" "

        if st=='idle':
            self.label="AceStream engine waiting"

        elif st=='starting':
            self.label="Playing torrent."

        elif st=='err':
            self.label="No response"
            self.err="dl"

        elif st=='check': 
            self.label="Verifying data"
            self.proc=int(params.split(';')[1])

        elif st=='prebuf':   
            self.proc=int( params.split(';')[1] )+0.1
            self.label="Pre-buffering"
            self.line='Seeds:%s Download:%sKb/s'%(params.split(';')[8],params.split(';')[5])  
            engine_data = { "action": str("Pre-buffering"), "percent": str(params.split(';')[1])+ "%","download":str(params.split(';')[5]) + " Kb/s", "upload":str(params.split(';')[7]) + " Kb/s","seeds":str(params.split(';')[8]),"total_download":str(int(params.split(';')[10])/(1024*1024))+'Mb',"total_upload":str(int(params.split(';')[12])/(1024*1024))+'Mb' }

        elif st=='loading':
            self.label="Loading..."

        elif st=='dl':
            engine_data = { "action": str("Downloading"), "percent": str(params.split(';')[1])+ "%","download":str(params.split(';')[3]) + " Kb/s", "upload":str(params.split(';')[5]) + " Kb/s","seeds":str(params.split(';')[6]),"total_download":str(int(params.split(';')[8])/(1024*1024))+'Mb',"total_upload":str(int(params.split(';')[10])/(1024*1024))+'Mb' }
            try:
                lat123.set_information(engine_data)
            except: pass

        elif st=='buf':
            engine_data = { "action": str("Buffering"), "percent": str(params.split(';')[1])+ "%","download":str(params.split(';')[5]) + " Kb/s", "upload":str(params.split(';')[7]) + " Kb/s","seeds":str(params.split(';')[8]),"total_download":str(int(params.split(';')[10])/(1024*1024))+"Mb","total_upload":str(int(params.split(';')[12])/(1024*1024))+"Mb" }
            try:
                lat123.set_information(engine_data)
            except: pass

    def end(self):
        self.active = False
        self.daemon = False
        #self.log.out('Daemon Fully Dead')
        
#thread to run the kill command right after the user hits stop        
def ace_control_thread():
	while json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetActivePlayers","params":{},"id":3}'))["result"]:
		xbmc.sleep(500)
	stop_aceengine()


#TODO - Windows and proper cache clear

def stop_aceengine():
    os.system("sh "+os.path.join(pastaperfil,"acestream","stop_acestream.sh"))
    return
        
        
        

class OverlayText(object):
    def __init__(self):
        self.showing = False
        self.window = xbmcgui.Window(12005)
        viewport_w, viewport_h = self._get_skin_resolution()
        font_max = 'font13'
        font_min = 'font10'
        origin_x = int(float(viewport_w)/1.3913)
        origin_y = int(float(viewport_h)/8.0)
        window_w = int(float(viewport_w)/3.7647)
        window_h = int(float(viewport_h)/2.5714)
        acelogo_w = int(float(window_w)/8.5)
        acelogo_h = int(float(window_w)/11.0)
        text_lat = int(float(window_w)/15)
        text_w = int(float(window_w)/1.7)
        text_h = int(float(window_h)/14)
        fst_setting = int(float(window_h)/3.5)
        fst_stat_setting = int(float(window_h)/1.4)

        #main window
        self._background = xbmcgui.ControlImage(origin_x, origin_y, window_w, window_h, os.path.join(addonpath,"resources","art","background.png"))
        self._acestreamlogo = xbmcgui.ControlImage(origin_x + int(float(window_w)/11.3), origin_y + int(float(window_h)/14), acelogo_w, acelogo_h, os.path.join(addonpath,"resources","art","acestreamlogo.png"))
        self._supseparator = xbmcgui.ControlImage(origin_x, origin_y + int(float(viewport_h)/12.176), window_w-10, 1, os.path.join(addonpath,"resources","art","separator.png"))
        self._botseparator = xbmcgui.ControlImage(origin_x, origin_y + window_h - 30, window_w-10, 1, os.path.join(addonpath,"resources","art","separator.png"))
        self._title = xbmcgui.ControlLabel(origin_x+int(float(window_w)/3.4), origin_y + text_h, window_w - 140, text_h, str("Acestream Engine"), font=font_max, textColor='0xFFEB9E17')
        self._total_stats_label = xbmcgui.ControlLabel(origin_x+int(float(window_h)/1.72), origin_y + int(float(window_h)/1.6), int(float(window_w)/1.7), 20, str("Stats"), font=font_min, textColor='0xFFEB9E17')
        #labels
        self._action = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting, int(float(text_w)*1.6), text_h, str("Action:") + '  N/A', font=font_min)
        self._download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + text_h, int(float(text_w)*1.6), text_h, str("Download:") + '  N/A', font=font_min)
        self._upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 2*text_h, text_w, text_h, str("Upload:") + '  N/A', font=font_min)
        self._seeds = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_setting + 3*text_h, text_w, text_h, str("Seeds:") + '  N/A', font=font_min)
        self._total_download = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting, text_w, text_h, str("Downloaded:") + '  N/A', font=font_min)
        self._total_upload = xbmcgui.ControlLabel(origin_x + text_lat, origin_y + fst_stat_setting + text_h, text_w, text_h, str("Uploaded:") + '  N/A', font=font_min)
        self._percent_value = xbmcgui.ControlLabel(origin_x+int(float(window_h)/1.05), origin_y + fst_setting, text_w, text_h,'N/A', font=font_min)

    def show(self):
        self.showing=True
        self.window.addControl(self._background)
        self.window.addControl(self._acestreamlogo)
        self.window.addControl(self._supseparator)
        self.window.addControl(self._botseparator)
        self.window.addControl(self._title)
        self.window.addControl(self._action)
        self.window.addControl(self._download)
        self.window.addControl(self._upload)
        self.window.addControl(self._seeds)
        self.window.addControl(self._total_stats_label)
        self.window.addControl(self._total_download)
        self.window.addControl(self._total_upload)
        self.window.addControl(self._percent_value)


    def hide(self):
        self.showing=False
        self.window.removeControl(self._total_download)
        self.window.removeControl(self._total_upload)
        self.window.removeControl(self._percent_value)
        self.window.removeControl(self._title)
        self.window.removeControl(self._action)
        self.window.removeControl(self._download)
        self.window.removeControl(self._upload)
        self.window.removeControl(self._seeds)
        self.window.removeControl(self._total_stats_label)
        self.window.removeControl(self._acestreamlogo)
        self.window.removeControl(self._supseparator)
        self.window.removeControl(self._botseparator)
        self.window.removeControl(self._background)

    def set_information(self,engine_data):
        if self.showing == True:
            self._action.setLabel(str("Action:") + '  ' + engine_data["action"])
            self._percent_value.setLabel(engine_data["percent"])
            self._download.setLabel(str("Download:")+ '  ' + engine_data["download"])
            self._upload.setLabel(str("Upload:") + '  ' + engine_data["upload"])
            self._seeds.setLabel(str("Seeds:") + '  ' + engine_data["seeds"])
            self._total_download.setLabel(str("Downloaded:") + '  ' + engine_data["total_download"])
            self._total_upload.setLabel(str("Uploaded:") + '  ' + engine_data["total_upload"])
        else: pass

    def _close(self):
        if self.showing:
            self.hide()
        else:
            pass
        try: 
            self.window.clearProperties()
            print("OverlayText window closed")
        except: pass
                
    #Taken from xbmctorrent
    def _get_skin_resolution(self):
        import xml.etree.ElementTree as ET
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try: res = tree.findall("./res")[0]
        except: res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])

    
