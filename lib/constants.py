#!/usr/bin/python

##############################################
# Globo.com account information
USER_ID='ricardobonon@gmail.com'
USER_PWD='fl10nqsklg'

##############################################
# Log information
# 0 do not log, 1 log (if all is 0, no log is created)
LOG_ERRORS=1
LOG_WARNINGS=1
LOG_MESSAGES=1
LOG_FILE='plimp-lim.log'

##############################################
# Directories and Files
INPUT_FILE           = 'input.xml'

##############################################
# Encoding Settings
#Encoding for input/output XML files
XMLENCODING          = 'iso-8859-1' 
#Encoding for interfacing with Globo's search engines
GLOBOENCODING        = 'utf-8'

##############################################
# Globo HTTP Parameters and URLs

#This can be any valid Globo.com Video ID for performing the authentication 
#(Video ID is the number after the text GIM in URLs of Globo.com videos
AUTH_VIDEOID=str('842866')

#Direct URL for Globo's Flash video player
PLAYER_URL='http://playervideo.globo.com/webmedia/GMCPlayListASX?flash=true&midiaId='

#URL for authenticating login info and cookie setting
LOGIN_URL='http://playervideo.globo.com/webmedia/player/GMCLogin'

#Body of HTTP request to Globo's authentication engine
LOGIN_BODY = {'login':USER_ID,\
              'senha':USER_PWD,\
              'ntr':'true',\
              'escondeFimVideo':'true',\
              'nocache':'1213827954549',\
              'pp':'true',\
              'midiaId':AUTH_VIDEOID,\
              'autoStart':'true'}

#Headers of HTTP request to Globo's authentication engine
LOGIN_HEADERS = {'Content-type': 'application/x-www-form-urlencoded',\
                 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',\
                 'Accept-Language':' en-us,en;q=0.5',\
                 'Accept-Encoding':' gzip,deflate',\
                 'Accept-Charset':' ISO-8859-1,utf-8;q=0.7,*;q=0.7',\
                 'Keep-Alive':' 300',\
                 'Connection':' keep-alive',\
                 'Referer':' http://playervideo.globo.com/webmedia/player/GMCPlayMidia?midiaId='+AUTH_VIDEOID+'&autoStart=true&pp=true&escondeFimVideo=true&ntr=true&nocache=',\
                 'Content-Type':' application/x-www-form-urlencoded',\
                 'Content-Length':' 137'}

#Headers of HTTP request to Globo's search engine. We are here using exactly what a browser would send
#that is why we keep separate LOGIN and SEARCH headers.
SEARCH_HEADERS = {'Content-type': 'application/x-www-form-urlencoded',\
                 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',\
                 'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9) Gecko/2008052906 Firefox/3.0',\
                 'Accept-Language':' en-us,en;q=0.5',\
                 'Accept-Charset':' ISO-8859-1,utf-8;q=0.7,*;q=0.7',\
                 'Keep-Alive':' 300',\
                 'Connection':' keep-alive'}

SEARCH_ENGINE = 'http://playervideo.globo.com/webmedia/GMCBusca?'

