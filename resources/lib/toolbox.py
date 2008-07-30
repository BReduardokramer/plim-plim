from traceback import extract_stack
import re

def makeDict(*args):
    '''
    This function creates a dictionary containing all of the variables passed as parameters with the 
    variable name being the key and the value of the variable as the value
    Author: Andrew Konstantaras
    http://code.activestate.com/recipes/576373/
    '''
    strAllStack = str(extract_stack())
    #pattern of a makeDict call...
    makeDict_pattern = 'makeDict[ ]*\('
    #finding the last call to makeDict i.e. current call...
    last_ocurrence = list(re.finditer(makeDict_pattern, strAllStack))[-1]
    #finding args names...
    strStack = strAllStack[last_ocurrence.start():]
    strArgs = strStack[(strStack.find('(') + 1):strStack.find(')')].strip()
    lstVarNames = strArgs.split(',')
    lstVarNames = [ s.strip() for s in lstVarNames ]      
    #building dict
    tplArgs = map(None, lstVarNames, args)
    newDict = dict(tplArgs)
    return newDict
