#!/usr/bin/python

import lib.globals as globals
import lib.ElementTree as ET
import os, datetime, cookielib, urllib, urllib2, re, sys, traceback

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
            
            status=os.stat(path)
            tmp=status.st_mode
            #check if path is a directory
            if os.path.isdir(path):
                #then check if it is writeable
                print path
            else:
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
            
        
    
                    
                    
                    
########################################################################  


"""
        iterator=self.inputtree.getroot().getiterator('show')
        for show in iterator:
            searchstr=show.find(globals.EL_SEARCHSTR).text
            searchfilters=show.find(globals.EL_SEARCHFILTER).text
            #Preparing a dictionary for being urlencoded as query string
            dict={\
                '1':'1',\
                'novaBusca':'1',\
                'b':searchstr.encode(globals.GLOBOENCODING),\
                'f':searchfilters.encode(globals.GLOBOENCODING),\
                'o':'1'\
                }
            query=urllib.urlencode(dict)
            #insert final query string as an aditional element <querystr> in the Element Tree
            searchquery=ET.SubElement(show,'querystr').text=globals.SEARCH_ENGINE+query            

"""

            
if __name__ == "__main__":
    
    crawler=GloboFetchVideos(globals.INPUT_FILE)
    
    
    
    exit()
    
