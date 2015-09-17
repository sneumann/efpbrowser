'''
Created on Jan 5, 2010
@author: Robert Breit

Module with classes for parsing service check configurations and handling the service checks
'''

# use lxml.sax instead
import lxml.sax
from lxml import etree
from xml.sax.handler import ContentHandler

import urllib2
import httplib
import socket
import re


class Service:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.link = ''
	self.external = 'false'

    def addConnect(self, url):
        self.connect = url
        
    def addIcon (self, filename):
        self.icon = filename
        
    def addLink (self, url):
        self.link = url
        
    def addExternal (self, webservice):
	self.external = webservice
    
    def addNoResultRegex (self, pattern):
        self.resultPattern = pattern
        self.patterntype = 'negative'
        
    def addResultRegex (self, pattern):
        self.resultPattern = pattern
        self.patterntype = 'positive'

    def checkService(self, gene):
        # Get sample signals through webservice.
        link = self.connect[:]
        if(link == ''):
            return 'Yes';              # return Yes, if no url defined
        
        link = re.sub("GENE", gene, link)
 
        try:
            # timeout condition
	    timeout = 10
	    socket.setdefaulttimeout(timeout)
	    page = urllib2.urlopen(link)
            result = page.read()
            check = re.search(self.resultPattern, result) 
            if self.patterntype == 'negative':
                if check == None:
                    return 'Yes'        # result doesn't match pattern for NoResult
                else:
                    return None         # result matches pattern for NoResult
            else:
                if check == None:
                    return None         # result doesn't match pattern for Result
                else:
                    return 'Yes'        # result matches pattern for Result
        except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException):
            return 'error'

        return None
    
    def getExternal(self):
        return self.external
    
    def getLink(self, gene):
        link = self.link[:]
        link = re.sub("GENE", gene, link)
        return link

class ServiceHandler(ContentHandler):
    def __init__(self, info):
        self.info = info
    
    def startElementNS(self, dict, qname, attrs):
 	uri, name = dict
        if name == 'service':
            self.currentService = Service(attrs.getValueByQName('name'), attrs.getValueByQName('type'))
        
        if name == 'connect':
            self.currentService.addConnect(attrs.getValueByQName('url'))

        if name == 'icon':
            self.currentService.addIcon(attrs.getValueByQName('filename'))

        if name == 'link':
            self.currentService.addLink(attrs.getValueByQName('url'))

        if name == 'noresult_regex':
            self.currentService.addNoResultRegex(attrs.getValueByQName('pattern'))

        if name == 'result_regex':
            self.currentService.addResultRegex(attrs.getValueByQName('pattern'))
        
	if name == 'external':
            self.currentService.addExternal(attrs.getValueByQName('webservice'))
        
 
    def endElementNS(self, qname, name):
        if name == 'service':
            self.info.addService(self.currentService)
            
            
        
class Info:
    def __init__(self):
        self.services = {} # Dictionary of views
    
    def addService(self, service):
        self.services[service.name] = service
        
    def getService(self, name):
        return self.services[name]
        
    def getServices(self):
        allServices = []
	externalServices = []
	for name in self.services:
	    service = self.getService(name)
 	    if service.getExternal() == 'true':
	       externalServices.append(name)
	    else:
	       allServices.append(name)
	allServices.extend(externalServices)
        return allServices
    
    def load(self, file):
        
        # Create the handler
        handler = ServiceHandler(self)
        
        # Parse the file
        try:
	    # Parse the file
	    tree = etree.parse(file)
	    lxml.sax.saxify(tree, handler)
        except (etree.XMLSyntaxError):
            return 'error'
        
        return None
        
