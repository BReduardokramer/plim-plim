#!/usr/bin/python

#Base libraries imports
import os, datetime, cookielib, urllib, urllib2, re, sys, math

#Local resources imports
BASE_RESOURCE_PATH = os.path.join(os.getcwd().replace( ";", "" ), "resources" )
sys.path.append(os.path.join( BASE_RESOURCE_PATH, "lib" ) )
import ElementTree as ET
from BeautifulSoup import BeautifulSoup, SoupStrainer
import globals
import toolbox


########################################################################
class plimplim():
    """Download globo.com movies based on input file """
    
    #----------------------------------------------------------------------
    def __init__(self, inputfile):
        """Initiates object, reading input file"""
        self.inputfile=inputfile
        self.checkWriteabeLog()
        self.fetchInput()
        self.checkInput()
        self.checkDownloadDirs()      
        self.checkLastDownloads()
        
    #----------------------------------------------------------------------
    def writeLog(self, logstr, type):
        
        """Outputs Error information to log file"""
        
        logstr=logstr.encode(globals.ENC_LOCAL)

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
        """Check if logfile is writable when logging is activated, if not, prints error message to stdout and exits"""

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
        """Parses input file into an ElementTree object, returns the object"""    
        
        try:
            self.inputtree=ET.parse(self.inputfile)
        
        except IOError, detail:
            self.writeLog('parsing '+self.inputfile+'Error parsing input file - '+str(detail),'error')
            exit()

        except Exception, detail:
            #using expat for getting more detailed information about the exception
            if str(detail.__module__)=='xml.parsers.expat':
                import xml.parsers.expat as expat
                errorstr=expat.ErrorString(detail.code)
                self.writeLog('parsing '+self.inputfile+': '+'malformed input file on line '+str(detail.lineno)+': '+errorstr,'error')

            else:
                self.writeLog('parsing '+self.inputfile+': '+'Unhandled exception while parsing inputfile \''+self.inputfile+'\':'+str(detail),'error')
            exit()            

            
    #----------------------------------------------------------------------
    def checkInput(self):
        """Quality check on elements in input tree. This function will ensure the program will proceed only if the element structure is as described in the sample
        input file"""

        #root element must be globals.EL_ROOT
        if self.inputtree.getroot().tag<>globals.EL_ROOT:
            self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, root element must be <'+globals.EL_ROOT+'>','error')        
            exit()
                  
        #traversing each show tree checking the subelements
        for show in self.inputtree.getroot().getchildren():

            #children of globals.EL_ROOT must be globals.EL_SHOW, if other found, exist with error
            if show.tag<>globals.EL_SHOW:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, children of <'+globals.EL_ROOT+'> must be all <'+globals.EL_SHOW+'>, <'+show.tag+'> found','error')        
                exit()
            
            #the tags of the children of globals.EL_SHOW are collected in InputShowElements for further testing
            InputShowElements=[]           
            for elem in show.getchildren():
                InputShowElements.append(elem.tag)
            
            #globals.EL_SHOW cannot have no children
            if len(InputShowElements)==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty '+globals.EL_SHOW+'> element','error')        
                exit()                
                
            #if empty or duplicate elements are found, exits logging error        
            for elem in InputShowElements:
                if show.find(elem).text==None:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty element <'+elem+'>','error')        
                    exit()
                if InputShowElements.count(elem)>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicate element <'+elem+'>','error')        
                    

            #if a mandatory show element is missing or duplicate, exits logging error 
            for elem in globals.ELS_MANDATORY:
                if InputShowElements.count(elem)==0:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, missing mandatory element <'+elem+'>','error')        
                    exit()
                elif InputShowElements.count(elem)>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicates found for element <'+elem+'>','error')        
                    exit()             
                
            #if all download show element are missing, exists logging error. At least one download show element should exist
            count=0
            for elem in globals.ELS_DOWNLOAD:
                count+=InputShowElements.count(elem)
            if count==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, at least one download element must be specified','error')        
                exit()               
                
        #looking for unkown elements, if found they are ignored, and warning message is logged
        IgnoredElements=[]
        for elem in self.inputtree.getroot().getiterator():
            if elem.tag not in globals.ELS_ALLOWED and elem.tag not in IgnoredElements:
                IgnoredElements.append(elem.tag)  
                
        #output warning about ignored elements
        if len(IgnoredElements):
            for elem in IgnoredElements:
                self.writeLog('parsing '+self.inputfile+': '+'unknown element <'+elem+'> will be ignored','warning')

        #if it reaches here, then all may be well, output message         
        self.writeLog('parsing '+self.inputfile+': '+'successfully parsed input information','message')
        
        
   #----------------------------------------------------------------------
    def checkDownloadDirs(self):
        """Verifies specified download directories"""
        
        #for each type of download elements, iterates through their instances found in the input tree, checking if 
        #the specified directories exists. If not, tries to create them, handling exceptions.
        for element_type in globals.ELS_DOWNLOAD:
            
            for elem in self.inputtree.getroot().getiterator(element_type):
                
                path=elem.text.encode(globals.ENC_LOCAL)
                
                #in case the path does not exists, creates a new directory, handling exceptions and exiting in case of errors
                if not os.path.isdir(path):
                    try:
                        os.makedirs(path)
                        self.writeLog('checking directories: non-existing directory \''+path+'\' created.','message')
                    
                    except Exception, ex:
                        self.writeLog('checking directories: not able to create directory \''+path+'\' created.','error')
                        exit()
        
                        
    #----------------------------------------------------------------------
    def checkLastDownloads(self):
        """For each show, finds the id (globo.com video id) of the newset episode existing in the download 
        directory. This id is inserted as sub element of the show elements in self.inputtree to be 
        used later. At the end, the oldest of these ids is stored as globals.EL_OLDEST in the input tree. This
        will be used later for stop the searching for new episodes"""
        
        #iterating per show
        for show in self.inputtree.getroot().getiterator(globals.EL_SHOW):
            
            newest_episodes_found=[]

            #for each occurrence of any possible download element
            for download_element in globals.ELS_DOWNLOAD:

                #check actually existing elements
                if show.find(download_element)<>None:      
                    
                    showname=show.find(globals.EL_SHOWNAME).text
                    downloaddir=show.find(download_element).text

                    #get directory listing of directory described by download_element
                    dir=os.listdir(downloaddir)

                    #match object for the file matching for this download_element 
                    reg=re.compile(globals.FILE_MATCHING[download_element],re.IGNORECASE)
                    idlist=[]

                    #for each entry in the dir listing, matches the file matching
                    #looking for the id, a 6-digit string (check match pattern on globals.FILE_MATCHING)
                    for file in dir:

                        match=reg.findall(file)

                        #'match' is a list (check globals.FILE_MATCHING, grouping). If something is matched.
                        if len(match): 
                            
                            #then id is the first element of 'match'. It is stored in idlist
                            idlist.append(match[0])

                    #sort the list of ids, and store the last as subelement to the show element
                    if len(idlist):
                        idlist.sort()
                        self.writeLog('Show '+showname+''+': id of latest existing episode in '+downloaddir+' is '+str(idlist[-1]),'message')
                        ET.SubElement(show,download_element+'_last').text=str(idlist[0])
                        newest_episodes_found.append(idlist[-1])
                    else:
                        self.writeLog('Show "'+showname+'"'+': no existing episode found in \"'+downloaddir+'\"','message')
                
            #Store in input tree the oldest of the newest existing episode found in disk.
            # HERE: a change is needed. For each download, a last existing episode should be stored, instead of the oldest newest
            if len(newest_episodes_found):
                newest_episodes_found.sort()
                ET.SubElement(show, globals.EL_OLDEST).text=str(newest_episodes_found[0])
            else:
                ET.SubElement(show, globals.EL_OLDEST).text=''

                        
                        
    #----------------------------------------------------------------------
    def doLogin(self):
        """Sends login POST info to get authentication cookie set and session
        initiated . Cookis are stored in self.cookiejar"""
    
        #create opener to handle cookies
        cookiejar = cookielib.LWPCookieJar()  
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        urllib2.install_opener(opener)
        
        #urlenconde the body content of the login page (the login form data)
        login_body = urllib.urlencode(globals.LOGIN_BODY) 
    
        #request the login page, cookies are handled automatically
        req = urllib2.Request(globals.LOGIN_URL, login_body, globals.LOGIN_HEADERS)           
        sock = urllib2.urlopen(req)                               
        sock.close()
        
        return cookiejar
    
             
  
        
    
        
    #----------------------------------------------------------------------
    def parseEpisodeSearch_numpages(self, html):
        """Returns the number of pages found in each show's search results first page"""

        #<li class=segundo> is the tag holding number of episodes info
        trainer = SoupStrainer('li', { 'class' : 'segundo' })            
        list=[tag for tag in BeautifulSoup(html, parseOnlyThese=trainer)]
        
        numpages=''
        
        #If matches are returned, then episodes were found, parses information about number of episodes and pages
        if len(list):
            
            #numepisodes is nested in the 3rd <sttong> tag inside <li class=segundo> tag. 
            numepisodes=tag.findAll('strong')[2].string
                                
            #episodesperpage is the 2nd <strong> tag.
            episodesperpage=int(tag.findAll('strong')[1].string)
            
            #Number of pages.
            numpages=str(int(math.ceil(float(numepisodes)/float(episodesperpage))))
                                                        
        return numpages
    

    #----------------------------------------------------------------------
    def parseEpisodeSearch(self, html):
        """Parse the search result pages matching information about the episodes. Information found is inserted into self.inputtree"""
        
        #using BeautifulSoup for mathing the html. For speed, parsing is done only on the chosen tags, by using SoupStrainer 
        #before the call to BeautifulSoup. Episode title, description and url information are stored all together 
        #in <div class=conteudo-texto> tags in the html code
        trainer = SoupStrainer('div', {'class':'conteudo-texto'})
        soup=BeautifulSoup(html, parseOnlyThese=trainer)            
        
        #element to hold the list of episodes found
        episodeslist=ET.Element(globals.EL_EPISODELIST)
        
        #for each <div class=conteudo-texto> tag, matches and store the relevant info
        for tag in soup.contents:
            
            #subelement to hold episode details
            episodedetails=ET.SubElement(episodeslist,globals.EL_EPISODEDETAILS)
            
            #match the episode title and store it as subelement of episodetails
            ET.SubElement(episodedetails,globals.EL_EPISODETITLE).text=tag.h2.a['title']
            
            #match the episode url and store it as subelement of episodetails
            ET.SubElement(episodedetails,globals.EL_EPISODEURL).text=tag.h2.a['href']
            
            #match episode id out of the episode url, and store it as subelement of episodetails
            matchstr='http\S*GIM(\d{6})\S*html'    
            pattern=re.compile(matchstr)
            match=pattern.findall(tag.h2.a['href'])
            ET.SubElement(episodedetails,globals.EL_EPISODEID).text=match[0]                
    
            #match episode description and store it as subelement of episodetails. The whole "contents" field of the tag is retrieved, as there 
            #may be sub tags inside the <p> tag
            description=''
            for piece in tag.p.contents:
                description+=piece.string 
            ET.SubElement(episodedetails,globals.EL_EPISODEDESCRIPTION).text=description
        
        #episodes durations are stored in <span class="tempo"> tags in the html code
        trainer = SoupStrainer('span', {'class':'tempo'})
        soup=BeautifulSoup(html, parseOnlyThese=trainer)
            
        #we need to iterate through the already existing episodedetails elements and insert the duration as subelement to each.
        iterator=episodeslist.getiterator(globals.EL_EPISODEDETAILS)       
        for index,tag in enumerate(soup):
            ET.SubElement(iterator[index],globals.EL_EPISODEDURATION).text=tag.string       
                
        #episodes dates are stored in <td class="coluna-data"> tags in the html code
        trainer = SoupStrainer('td', {'class':'coluna-data'})
        soup=BeautifulSoup(html, parseOnlyThese=trainer)

        #we need to iterate through the already existing episodedetails elements and insert the duration as subelement to each.
        iterator=episodeslist.getiterator(globals.EL_EPISODEDETAILS)       
        for index,tag in enumerate(soup):
            ET.SubElement(iterator[index],globals.EL_EPISODEDATE).text=tag.string       
            
        return episodeslist         
    

    #----------------------------------------------------------------------
    def openPage(self, req, filename=None):
        """Open the requested page. If filename is given, opens page from a local file named filename"""
        
        try:
            if filename: 
                sock=open(filename,'r')
            else: 
                sock = urllib2.urlopen(req)
            html=sock.read()
            sock.close()
            return html                               

        except Exception, detail:
            if filename:
                self.writeLog('opening local page \"'+filename+'\" - '+str(detail),'error')
            else:
                self.writeLog('opening page \"'+filename+'\" - '+str(detail),'error')
            exit()
    
    #----------------------------------------------------------------------
    def saveLocalPage(self, content, filename):
        """Saves content locally as a file named filename"""
        
        try:
            sock=open(filename,'w')
            sock.write(content)
            sock.close()
        
        except Exception, detail:
            self.writeLog('saving file \"'+filename+'\" - '+str(detail),'error')
            exit()

            
    #----------------------------------------------------------------------
    def localPageName(self, req):
        """Return a string to be used as a file name, based on req, for the local files used if globals.DEV_MODE is set"""

        validchars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.^+%&'
        
        name=req.get_full_url()+req.data+'.html'      
        strippedname=''.join(c for c in name if c in validchars)
        
        fullpath=os.path.join(globals.DEV_MODE_DIR, strippedname)

        return fullpath
    
    #----------------------------------------------------------------------
    def querySearchEngine(self, req):
        """Query the search engine for show episodes. If DEV_MODE='offline', query is done on local files instead of 
        the online search engine. This is for convenience on debugging/developing.Refer to globals.DEVEL_MODE for details """
               
        #in DEV_MODE, define the name of local files, using data from "req" info to have unique name for each query
        if globals.DEV_MODE: 
            name=self.localPageName(req)

        try:
            
            #if in DEV_MODE='offline', open pages from local files, otherwise, query the search engines online
            if globals.DEV_MODE=='offline': 
                html=self.openPage(req, filename=name)                
            else:
                html=self.openPage(req)
                            
        except Exception, details:
            
            if globals.DEV_MODE=='offline':
                self.writeLog('opening search page from local file \"'+name+'\" :'+str(details),'error')               
            else:
                self.writeLog('querying the search engine :'+str(details),'error')               
            exit()                    
            
        return html

    
    #----------------------------------------------------------------------
    def stripOlderEpisodes(self, lastexisting=None, list=None):
        """ Deletes episodes older than or equal to (episode id smaller than or equal to) "latestexisting" from episode list """
        
        videoidlist=[videoid_elem.text for videoid_elem in list.getiterator(globals.EL_EPISODEID)]      
        deletelist=videoidlist[videoidlist.index(lastexisting):]
        
        #delete elements which have their globals.EL_EPISODEID.text in deletelist         
        for elem in list.getiterator(globals.EL_EPISODEDETAILS):
            
            if elem.find(globals.EL_EPISODEID).text in deletelist:
                list.remove(elem)
                
        return list

    
    #----------------------------------------------------------------------
    def checkExistingEpisodes(self, lastexisting=None, list=None):
        """ Checks if the "lastexisting" id string is in the episode list "list", returning true if found"""
        
        idlist=[idelem.text for idelem in list.getiterator(globals.EL_EPISODEID)]

        if oldestneeded in idlist:
            return 1
        else:
            return   

      
    #----------------------------------------------------------------------
    def searchEpisodes(self):
        """Main search loop, iterates through the show tags in input tree, fetching the search results, storing 
        them back in input tree. The search loop will proceed untill the "last existing"  episode is 
        reached - check checkLastDownloads() for info - or till all search results page were parsed."""
        
        
        for show in self.inputtree.getroot().getiterator(globals.EL_SHOW):
            
            showname=show.find(globals.EL_SHOWNAME).text
           
            #there will always at least one result page, so element holding the number of pages is set initially to 1. 
            ET.SubElement(show,globals.EL_NUMPAGES).text='1'
            
            #preparing the query for the seach enginge
            globals.SEARCH_QUERY[globals.SEARCHFILTERKEY]=show.find(globals.EL_SEARCHFILTER).text.encode(globals.ENC_UTF)
            globals.SEARCH_QUERY[globals.SEARCHSTRKEY]=show.find(globals.EL_SEARCHSTR).text.encode(globals.ENC_UTF)
            
            #let the log know what we are about to do
            if show.find(globals.EL_OLDEST).text:
                self.writeLog('Show "'+showname+'"'+': searching for episodes newer than '+show.find(globals.EL_OLDEST).text,'message')
            else:
                self.writeLog('Show "'+showname+'"'+': searching for all new episodes','message')
            
            #page counter when looping through results
            page=1
            foundOldestNeeded=0
            
            #main search loop
            while page<=int(show.find(globals.EL_NUMPAGES).text) and not foundOldestNeeded: 

                #a little more chat with the log
                self.writeLog('Show "'+showname+'"'+': Parsing search results page '+str(page),'message')

                #last item to be inserted on the search query is the search page number
                globals.SEARCH_QUERY[globals.PAGEKEY]=str(page)
                
                
                #encode the request
                req = urllib2.Request(globals.SEARCH_ENGINE_URL, urllib.urlencode(globals.SEARCH_QUERY), globals.SEARCH_HEADERS)
                
                #submit the query to the search engine
                html=self.querySearchEngine(req)
                
                #download the search results in case if in DEV_MODE
                if globals.DEV_MODE=='download': self.saveLocalPage(html, self.localPageName(req))
                
                #for first page, store the number of pages to be parsed in the main tree
                if page==1: 
                    show.find(globals.EL_NUMPAGES).text=self.parseEpisodeSearch_numpages(html)
                
                #parse the results into a ElementTree element containing details about the episodes
                episodelist=self.parseEpisodeSearch(html)
                
                #if episodes exist in disk, check if the downloaded episode list reached the last existing episodes in disk. 
                if (show.find(globals.EL_OLDEST).text):
                    
                    foundOldestNeeded=self.checkExistingEpisodes(lastexisting=show.find(globals.EL_OLDEST).text, list=episodelist)
                    
                    #if found last exsiting, strip all elements older than it
                    if foundOldestNeeded:
                        episodelist=self.stripOlderEpisodes(lastexisting=show.find(globals.EL_OLDEST).text, list=episodelist)
                        
                show.append(episodelist)
                page+=1
           
            #if no results were found, write warning to log
            if show.find(globals.EL_NUMPAGES).text=='':
                self.writeLog('Show "'+showname+'"'+': search results have no match','warning')

                
            
    #----------------------------------------------------------------------                
    def parseVideoPage(self, videoid):
        """Parses the video page (globals.PLAYER_URL+<movie id>), return Element containing the direct url flash
        video URLs, as well as thumbnail URL
        """
        url=globals.PLAYER_URL+videoid
        req = urllib2.Request(url , None, globals.SEARCH_HEADERS)
        sock = urllib2.urlopen(req)
        html=sock.read()
        sock.close()
        
        return html
        
        
    #----------------------------------------------------------------------                
    def downloadEpisodes(self):
        """Parses the inputtree, downloading the episodes as specified (movies, playlists)
        """
        
        for show in self.inputtree.getroot().getiterator(globals.EL_SHOW):
            
            for episode in show.getiterator(globals.EL_EPISODEDETAILS):
                
                title=episode.find(globals.EL_EPISODETITLE).text
                videoid=episode.find(globals.EL_EPISODEID).text
                url=episode.find(globals.EL_EPISODEURL).text
                
                data=self.parseVideoPage(videoid)
            
            
            
        
########################################################################  



if __name__ == "__main__":
    
    crawler=plimplim(globals.INPUT_FILE)
    
    crawler.searchEpisodes()

    #crawler.downloadEpisodes()

    crawler.inputtree.write('output.xml',globals.ENC_LOCAL)
    exit()
    
