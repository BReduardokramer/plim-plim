#!/usr/bin/python

import lib.constants as constants
import lib.ElementTree as ET
import os, datetime, cookielib, urllib, urllib2, re, sys, traceback

########################################################################
class GloboFetchVideos():
    """Get Globo movie episodes based on input file """

    #----------------------------------------------------------------------
    def __init__(self, inputfile):
        """Constructor"""
        self.inputfile=inputfile
        self.checkWriteabeLog()
        self.fetchInput()
        self.verifyInput()
        
        
    #----------------------------------------------------------------------
    def checkWriteabeLog(self):
        """Check if logfile is writable, if not, prints error message to stdout and exits"""
        if constants.LOG_ERRORS or constants.LOG_MESSAGES:
            try:
                sock=open(constants.LOG_FILE,'a')
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
    def writeLog(self, logstr,type):
        """Outputs Error information to log file"""
        if type=='error':
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            print 'ERROR   - '+logstr
            if constants.LOG_ERRORS:
                logfile=open(constants.LOG_FILE,'a')
                logfile.write(datestr+' - ERROR   - '+logstr+'\n')
                logfile.close()     
        if type=='warning' and constants.LOG_WARNINGS:
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(constants.LOG_FILE,'a')
            logfile.write(datestr+' - WARNING - '+logstr+'\n')
            logfile.close()     
        if type=='message' and constants.LOG_MESSAGES:
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(constants.LOG_FILE,'a')
            logfile.write(datestr+' - MESSAGE - '+logstr+'\n')
            logfile.close()             
        if (constants.LOG_ERRORS or constants.LOG_MESSAGES or constants.LOG_WARNINGS) and type=='start':
            datestr=datetime.datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            logfile=open(constants.LOG_FILE,'a')
            logfile.write('\n'+datestr+' - MESSAGE - '+logstr)
            logfile.close()             
            
                                
#----------------------------------------------------------------------
    def verifyInput(self):
        """Verifies if elements in input tree are according to expected"""

        #----------------------------------------------------------------------
        def countInList(item, list):
            """Count items instance in a list """
            count=0
            for i in list:
                if i==item: count+=1
            return count
        
        MandatoryShowElements=['showname', 'searchstring', 'searchfilters']              
        PartialOptionalShowElements=['downloadm3u', 'downloadmovies']              
        FullyOptionalShowElements=['maximumepisodes']

        #Root element must be <plim-plim>
        if self.inputtree.getroot().tag<>'plim-plim':
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, root element must be <plim-plim>','error')        
                exit()
                  
        #Traversing the input tree looking for problems
        for show in self.inputtree.getroot().getchildren():

            #Children of <plim-plim> must be <show>
            if show.tag<>'show':
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, children of <plim-plim> must be all <show>, <'+elem.tag+'> found.','error')        
                exit()
            
            #Children of <show> are collected in InputShowElements
            InputShowElements=[]           
            for elem in show.getchildren():
                InputShowElements.append(elem.tag)
            
            #<show> cannot have no children
            if len(InputShowElements)==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty <show> element','error')        
                exit()                
                
            #If a mandatory show element is missing, duplicate or empty, exits logging error 
            for elem in MandatoryShowElements:
                if countInList(elem,InputShowElements)==0:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, missing mandatory element <'+elem+'>','error')        
                    exit()
                elif countInList(elem,InputShowElements)>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicates found for element <'+elem+'>','error')        
                    exit()
                elif show.find(elem).text==None:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, empty element <'+elem+'>','error')        
                    exit()
                
                    
            #If all partial optional show element are missing, all are empty, or any are duplicate, exists logging error
            partialcount=0
            nonemptycount=0
            for elem in PartialOptionalShowElements:
                partialcount=countInList(elem,InputShowElements)
                if partialcount>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicates found for element <'+elem+'>','error')        
                    exit()
                if show.find(elem):
                    if show.find(elem).text<>None: 
                        nonemptycount=+1
            if partialcount==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, at least one partial optional element must be specified','error')        
                exit()
            if nonemptycount==0:
                self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, only empty partial optional elements','error')        
                exit()

            #If fully optional elements are duplicate or empty, exists logging error
            count=0
            for elem in FullyOptionalShowElements:
                count=countInList(elem,InputShowElements)
                if count>1:
                    self.writeLog('parsing '+self.inputfile+': '+'bad elements on input file, duplicates found for element <'+elem+'>','error')        
                    exit()
                
        #Building list of allowed elements
        AllowedElements=['plim-plim','show']
        AllowedElements.extend(MandatoryShowElements)
        AllowedElements.extend(PartialOptionalShowElements)
        AllowedElements.extend(FullyOptionalShowElements)
        IgnoredElements=[]
        for elem in self.inputtree.getroot().getiterator():
            #Looking for unknown elements, storing them
            if elem.tag not in AllowedElements and elem.tag not in IgnoredElements:
                IgnoredElements.append(elem.tag)  
        #Output warning about ignored elements
        if len(IgnoredElements):
            for elem in IgnoredElements:
                self.writeLog('parsing '+self.inputfile+': '+'unknown element <'+elem+'> will be ignored','warning')
        
                
        self.writeLog('parsing '+self.inputfile+': '+'successfully parsed input information','message')

                
########################################################################  

            
if __name__ == "__main__":
    
    crawler=GloboFetchVideos(constants.INPUT_FILE)    
    exit()
    
