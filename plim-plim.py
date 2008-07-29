#!/usr/bin/python

import lib.globals as globals
import lib.ElementTree as ET
import os, datetime, cookielib, urllib, urllib2, re, sys, math
from lib.BeautifulSoup import BeautifulSoup 
from lib.BeautifulSoup import SoupStrainer


########################################################################
class GloboFetchVideos():
    """Download globo.com movies based on input file """

    #----------------------------------------------------------------------
    def __init__(self, inputfile):
        """Initiates object, reading input file"""
        self.inputfile=inputfile
        self.checkWriteabeLog()
        self.fetchInput()
        self.checkInput()
        self.checkDirectories()      
        self.checkLastDownloads()
        
    #----------------------------------------------------------------------
    def writeLog(self, logstr,type):
        """Outputs Error information to log file"""
        if type=='error':
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            print 'ERROR   - '+logstr
            if globals.LOG_ERRORS:
                logfile=open(globals.LOG_FILE,'a')
                logfile.write(datestr+' - ERROR   - '+logstr+'\n')
                logfile.close()     
        if type=='warning' and globals.LOG_WARNINGS:
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(globals.LOG_FILE,'a')
            logfile.write(datestr+' - WARNING - '+logstr+'\n')
            logfile.close()     
        if type=='message' and globals.LOG_MESSAGES:
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(globals.LOG_FILE,'a')
            logfile.write(datestr+' - MESSAGE - '+logstr+'\n')
            logfile.close()             
        if (globals.LOG_ERRORS or globals.LOG_MESSAGES or globals.LOG_WARNINGS) and type=='start':
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(globals.LOG_FILE,'a')
            logfile.write('\n'+datestr+' - MESSAGE - '+logstr)
            logfile.close()             
 
    #----------------------------------------------------------------------
    def checkWriteabeLog(self):
        """Check if logfile is writable, if not, prints error message to stdout and exits"""
        if globals.LOG_ERRORS or globals.LOG_MESSAGES:
            try:
                sock=open(globals.LOG_FILE,'a')
                self.writeLog('Starting plim-plim -------------\n','start')
                sock.close()
            except IOError, detail:
                print 'Error opening log file: '+str(detail)
                exit()

    #----------------------------------------------------------------------
    def fetchInput(self):
        """Parses input file"""    
        #parses XML file into an ElementTree object, returns the object
        try:
            self.inputtree=ET.parse(self.inputfile)
        except IOError, detail:
            self.writeLog('parsing '+self.inputfile+'Error parsing input file - '+str(detail),'error')
            exit()
        except Exception, detail:
            if str(detail.__module__)=='xml.parsers.expat':
                import xml.parsers.expat as expat
                errorstr=expat.ErrorString(detail.code)
                self.writeLog('parsing '+self.inputfile+': '+'malformed input file on line '+str(detail.lineno)+': '+errorstr,'error')
            else:
                self.writeLog('parsing '+self.inputfile+': '+'Unhandled exception while parsing inputfile \''+self.inputfile+'\':'+str(detail),'error')
            exit()            

            
    #----------------------------------------------------------------------
    def checkInput(self):
        """Verifies if elements in input tree are according to expected"""

        #Root element must be globals.EL_ROOT
        if self.inputtree.getroot().tag<>globals.EL_ROOT:
            self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, root element must be <'+globals.EL_ROOT+'>','error')        
            exit()
                  
        #Traversing each show tree looking for problems on elements
        for show in self.inputtree.getroot().getchildren():

            #Children of globals.EL_ROOT must be globals.EL_SHOW, if other found, exist with error
            if show.tag<>globals.EL_SHOW:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, children of <'+globals.EL_ROOT+'> must be all <'+globals.EL_SHOW+'>, <'+show.tag+'> found','error')        
                exit()
            
            #The tags of the children of globals.EL_SHOW are collected in InputShowElements
            InputShowElements=[]           
            for elem in show.getchildren():
                InputShowElements.append(elem.tag)
            
            #globals.EL_SHOW cannot have no children
            if len(InputShowElements)==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty '+globals.EL_SHOW+'> element','error')        
                exit()                
                
            #If empty or duplicate elements are found, exits logging error        
            for elem in InputShowElements:
                if show.find(elem).text==None:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty element <'+elem+'>','error')        
                    exit()
                if InputShowElements.count(elem)>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicate element <'+elem+'>','error')        
                    

            #If a mandatory show element is missing, exits logging error 
            for elem in globals.ELS_MANDATORY:
                if InputShowElements.count(elem)==0:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, missing mandatory element <'+elem+'>','error')        
                    exit()
                elif InputShowElements.count(elem)>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicates found for element <'+elem+'>','error')        
                    exit()             
                
            #If all download show element are missing, exists logging error
            count=0
            for elem in globals.ELS_DOWNLOAD:
                count+=InputShowElements.count(elem)
            if count==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, at least one download element must be specified','error')        
                exit()               
                
        #Looking for unkown elements, if found they are ignored, and warning message is logged
        IgnoredElements=[]
        for elem in self.inputtree.getroot().getiterator():
            #Looking for unknown elements, storing them
            if elem.tag not in globals.ELS_ALLOWED and elem.tag not in IgnoredElements:
                IgnoredElements.append(elem.tag)  
        #Output warning about ignored elements
        if len(IgnoredElements):
            for elem in IgnoredElements:
                self.writeLog('parsing '+self.inputfile+': '+'unknown element <'+elem+'> will be ignored','warning')

        #If it comes till here, then all may be well, output message         
        self.writeLog('parsing '+self.inputfile+': '+'successfully parsed input information','message')

        
   #----------------------------------------------------------------------
    def checkDirectories(self):
        """Verifies if specified directories are writeable"""
        
        for elem in self.inputtree.getroot().getiterator(globals.EL_DLM3U):
            path=elem.text.encode(globals.ENC_LOCAL)
           #check if path is a directory
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                    self.writeLog('checking directories: non-existing directory \''+path+'\' created.','message')
                except Exception, ex:
                    self.writeLog('checking directories: not able to create directory \''+path+'\' created.','error')
                    exit()
        
        for elem in self.inputtree.getroot().getiterator(globals.EL_DLMOVIES):
            path=elem.text.encode(globals.ENC_LOCAL)
            if os.path.isdir(path):
                print path
            else:
                try:
                    os.makedirs(path)
                    self.writeLog('checking directories: non-existing directory \''+path+'\' created.','message')
                except Exception, ex:
                    self.writeLog('checking directories: not able to create directory \''+path+'\' created.','error')
                    exit()
                    

    #----------------------------------------------------------------------
    def checkLastDownloads(self):
        """For each show, finds the id (globo.com video id) of last episode existing in the download 
        directory. This id is inserted as sub element of the show elements in self.inputtree to be 
        used later"""
        
        #Iterationg per show
        for show in self.inputtree.getroot().getiterator(globals.EL_SHOW):
            
            #Finding occurrence of any download element
            for download_element in globals.ELS_DOWNLOAD:

                #If download element is found
                if show.find(download_element)<>None:         

                    #get directory listing of directory described by download_element
                    dir=os.listdir(show.find(download_element).text.encode(globals.ENC_LOCAL))

                    #match object for the file matching for this download_element 
                    reg=re.compile(globals.FILE_MATCHING[download_element],re.IGNORECASE)
                    idlist=[]

                    #For each entry in the dir listing, matches the file matching
                    #looking for 6-digit string (exact matching on globals.FILE_MATCHING)
                    for elem in dir:
                        match=reg.findall(elem)

                        #'match' is a list (check globals.FILE_MATCHING, grouping). If something is matched
                        if len(match): 
                            #then id is the first element of 'match'. It is stored in idlist
                            idlist.append(match[0])

                    #sort the list of ids, and store the last as subelement to the show element
                    if len(idlist):
                        idlist.sort()
                        ET.SubElement(show,download_element+'_last').text=str(idlist[-1])
                                        
             
    #----------------------------------------------------------------------
    def performLogin(self):
        """Sends login POST info to get authentication cookie set and session
        initiated . Returns set of Cookies setup by login page"""
    
        #create opener to handle cookies
        self.cookiejar = cookielib.LWPCookieJar()  
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        urllib2.install_opener(opener)
        
        #urlenconde the body content of the login page (the login form data)
        login_body = urllib.urlencode(globals.LOGIN_BODY) 
    
        #request the login page, cookies are handled automatically
        req = urllib2.Request(globals.LOGIN_URL, login_body, globals.LOGIN_HEADERS)           
        handle = urllib2.urlopen(req)                               
        handle.close()
        
        print self.cookiejar
        
        return
    
            
    #-----------------------------------------------------------------------
    def getMovies(self):
        """Download the links and movies"""
        
        self.fetchShowIndexes()
        #if not self.cookiejar: self.performLogin()
        
        #fetch the search results
        
      
        

        
    #----------------------------------------------------------------------
    def fetchShowIndexes(self):
        """Fecthes the index of matching episodes for each shown in self.inputtree"""
        
        
        for show in self.inputtree.getroot().getiterator(globals.EL_SHOW):          
            
            showname=show.find(globals.EL_SHOWNAME).text.encode(globals.ENC_UTF)
            searchfilters=show.find(globals.EL_SEARCHFILTER).text.encode(globals.ENC_UTF)
            searchstr=show.find(globals.EL_SEARCHSTR).text.encode(globals.ENC_UTF)
            globals.SEARCH_QUERY[globals.SEARCHFILTERKEY]=searchfilters
            globals.SEARCH_QUERY[globals.SEARCHSTRKEY]=searchstr
            
            page=1
            numpages=page
            episodes=ET.SubElement(show,'episodes')
            
            while page<=numpages:
                
                #Inserts page number on the search query dictionary.
                globals.SEARCH_QUERY[globals.PAGEKEY]=str(page)

                #Now that search query is ready with all correct parameter, encode it
                query=urllib.urlencode(globals.SEARCH_QUERY)
                
                #Retrieve the search results online
                #req = urllib2.Request(globals.SEARCH_ENGINE_URL, query, globals.SEARCH_HEADERS)
                #handle = urllib2.urlopen(req)
                #html=handle.read()
                #handle.close()
                
                #Retrieve the search results from files
                sock=open('Search_'+showname+'_'+str(page)+'.html','r')
                html=sock.read()
                sock.close
                               
                #On the first page, collects info about the number of episodes
                if page==1:

                    #Match the total number of episodes using BeautifulSoup. For speed, parsing is done only on the 
                    #chosen tags, by using SoupStrainer before the call to BeautifulSoup. The matched is for <li class=segundo>
                    trainer = SoupStrainer('li', { 'class' : 'segundo' })
                    [tag for tag in BeautifulSoup(html, parseOnlyThese=trainer)]
                    
                    #numepisodes is nested in the 3rd <sttong> tag inside <li class=segundo> tag                   
                    numepisodes=int(tag.findAll('strong')[2].string)
                                        
                    #episodesperpage is the 2nd <strong> tag
                    episodesperpage=int(tag.findAll('strong')[1].string)
                    
                    #Number of pages
                    numpages=int(math.ceil(float(numepisodes)/float(episodesperpage)))
                    
                #Parsing the tags which contain the title, description, url
                trainer = SoupStrainer('div', {'class':'conteudo-texto'})
                soup=BeautifulSoup(html, parseOnlyThese=trainer)                            
                
                for tag in soup.contents:
                    
                    title=tag.h2.a['title']
                    url=tag.h2.a['href']
                    
                    #Match episode id out of episode url 
                    matchstr='http\S*GIM(\d{6})\S*html'    
                    pattern=re.compile(matchstr)
                    match=pattern.findall(url)
                    id=match[0]                

                    #Match episode description, searching inside the contents structure, as there may be tags inside the <p> tag
                    description=''
                    for piece in tag.p.contents:
                        description+=piece.string 
                    
                    episodedetails=ET.SubElement(episodes,'episodedetails')
                    id=ET.SubElement(episodedetails,'id').text=id
                    title=ET.SubElement(episodedetails,'title').text=title
                    ur=ET.SubElement(episodedetails,'url').text=url
                    description=ET.SubElement(episodedetails,'description').text=description
                    
                    
                #Parsing the tags which contain the duration for the episodes
                iterator=episodes.find('episodedetails').getiterator()
                trainer = SoupStrainer('span', {'class':'tempo'})
                soup=BeautifulSoup(html, parseOnlyThese=trainer)
                
                for tag in soup.contents:
                    duration=ET.SubElement(iterator,'duration')           
                
                page+=1          
        
        self.inputtree.write('output.xml','iso8859-1')
        sock.close()
              
                    
########################################################################  



if __name__ == "__main__":
    
    crawler=GloboFetchVideos(globals.INPUT_FILE)
    crawler.getMovies()
    exit()
    
