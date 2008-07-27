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
ENC_LOCAL     = 'iso-8859-1' 
#Encoding for interfacing with Globo's search engines
ENC_UTF       = 'utf-8'

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
"""
LOGIN_BODY = {'login':USER_ID,\
              'senha':USER_PWD,\
              'ntr':'true',\
              'escondeFimVideo':'true',\
              'nocache':'1213827954549',\
              'pp':'true',\
              'midiaId':AUTH_VIDEOID,\
              'autoStart':'true'}
"""
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

#Dictionary for search queries. Empty values are filled in in run-time with show information read from input file
NEWSEARCHKEY='novaBusca'
SEARCHSTRKEY='b'
SEARCHFILTERKEY='f'
ORDERKEY='o'
SEARCH_QUERY = {'1':'1',\
                NEWSEARCHKEY:'1',\
                SEARCHSTRKEY:'',\
                SEARCHFILTERKEY:'',\
                ORDERKEY:'1'}
#base URL of the SearchEngine
SEARCH_ENGINE = 'http://playervideo.globo.com/webmedia/GMCBusca?'


##############################################
# Definitions for input file elements
EL_SHOWNAME='showname'
EL_SEARCHSTR='searchstring'
EL_SEARCHFILTER='searchfilters'
EL_DLM3U='downloadm3u'
EL_DLMOVIES='downloadmovies'
EL_ROOT='plim-plim'
EL_SHOW='show'
EL_MAXEPISODES='maximumepisodes'

ELS_MANDATORY=[]
ELS_MANDATORY.append(EL_SHOWNAME)
ELS_MANDATORY.append(EL_SEARCHFILTER)
ELS_MANDATORY.append(EL_SEARCHSTR)

ELS_DOWNLOAD=[]
ELS_DOWNLOAD.append(EL_DLM3U)
ELS_DOWNLOAD.append(EL_DLMOVIES)

ELS_OPTIONAL=[]
ELS_OPTIONAL.append(EL_MAXEPISODES)

ELS_ALLOWED=[EL_ROOT, EL_SHOW]
ELS_ALLOWED.extend(ELS_MANDATORY)
ELS_ALLOWED.extend(ELS_DOWNLOAD)
ELS_ALLOWED.extend(ELS_OPTIONAL)

FILE_MATCHING={EL_DLM3U:'(\d{6}).m3u$',\
               EL_DLMOVIES:'(\d{6})\s{1}\d{2}.flv$'}

