#!/usr/bin/python
#
# Module for retrieving gene expression data from the Department
# of Botany's Atgenexpress database

import MySQLdb
import re
import urllib2
from urllib2 import HTTPError
import efpConfig
import simplejson as json
import copy
import sys

class Gene:
    def __init__(self, id, database, probesetId):
        self.conn = None
        self.connOrtho = None
        self.annotation = None
        self.alias = None
        self.geneId = None
        self.probesetId = probesetId
        self.ncbiId = None
	self.database = database
        id = re.sub("(\.\d)$", "", id) # reduce splice variants (remove .n)
        self.retrieveGeneData(id)
        if(self.geneId == None):
            self.ncbiToGeneId(id)
            self.retrieveGeneData(self.geneId)
    
    def getGeneId(self):
        return self.geneId

    
    def getProbeSetId(self):
        return self.probesetId
    
    def getNcbiId(self):
        return self.ncbiId
    
    '''
    # name: retrieveGeneData
    # desc: Retrieves the probeset ID that corresponds to the given gene ID
    '''
    def retrieveGeneData(self, id):
        if(id == None):
            return
        if(efpConfig.DB_ANNO == None or efpConfig.DB_LOOKUP_TABLE == None or efpConfig.LOOKUP[self.database] == "0"): # annotations db not defined
	    self.retrieveLookupGeneData(id)
            return
        

        if(self.conn == None):
            self.connect()
        
        cursor = self.conn.cursor()
        select_cmd = "SELECT t1.%s, t1.probeset FROM %s t1 WHERE (t1.probeset=%%s or t1.%s=%%s) AND t1.date=(SELECT MAX(t2.date) FROM %s t2)" % \
                     (efpConfig.DB_LOOKUP_GENEID_COL, efpConfig.DB_LOOKUP_TABLE, efpConfig.DB_LOOKUP_GENEID_COL, efpConfig.DB_LOOKUP_TABLE)
        cursor.execute(select_cmd,(id, id))
        row = cursor.fetchall()
        cursor.close()
        if len(row) > 0:
           self.geneId = row[0][0]
           self.probesetId = row[0][1]
        return

    '''
    # name: retrieveLookupGeneData
    # desc: Checks whether a gene exists when no lookup is available e.g. RNA-seq Data
    '''
    def retrieveLookupGeneData(self, id):
        
        if(id == None):
            return
    
        if(self.conn == None):
            self.connect(self.database)
        
        matching_gene = id.partition("_")
	matching_gene = matching_gene[0] 
        cursor = self.conn.cursor()
        cursor.execute("SELECT data_probeset_id FROM sample_data WHERE data_probeset_id LIKE %s", (matching_gene + '%'))
        row = cursor.fetchall()
        cursor.close()
        self.conn = None

        if len(row) > 0:
            self.geneId = id
	    if (self.probesetId == None):
                self.probesetId = id
        return

       

    '''
    # name: ncbiToGeneId
    # desc: Returns the AGI corresponding to the NCBI gi accession
    # notes: NCBI gi accession comes from NCBI Linkout. Need to check whether NCBI gi accession is a NCBI GeneID or NCBI RefSeq.
    '''
    def ncbiToGeneId(self, ncbi_gi):
        if (ncbi_gi == None):
            return None
        if(efpConfig.DB_ANNO == None or efpConfig.DB_NCBI_GENE_TABLE == None): # ncbi lookup db not defined
            return None
        if(self.conn == None):
            self.connect()
        
        cursor = self.conn.cursor()
        
        select_cmd = "SELECT t1.%s FROM %s t1 WHERE t1.geneid=%%s or t1.protid=%%s" % (efpConfig.DB_NCBI_GENEID_COL, efpConfig.DB_NCBI_GENE_TABLE)
        cursor.execute(select_cmd,(ncbi_gi))
        row = cursor.fetchall()
        cursor.close()
        if len(row) != 0:
            self.geneId = row[0][0]
            self.ncbiId = ncbi_gi
        return



    def getAnnotation(self):
        if(efpConfig.DB_ANNO == None or efpConfig.DB_ANNO_TABLE == None): # annotations db not defined
            return None
        if(self.annotation == None):
            if(self.conn == None):
                self.connect()
               
            # Return the annotation and alias for a given geneId
            cursor = self.conn.cursor()
            select_cmd = "SELECT annotation FROM %s WHERE %s=%%s AND date = (SELECT MAX(date) FROM %s)" % (efpConfig.DB_ANNO_TABLE, efpConfig.DB_ANNO_GENEID_COL, efpConfig.DB_ANNO_TABLE)
            cursor.execute(select_cmd, (self.geneId));
            result = cursor.fetchone()
            if result != None:
                self.annotation = result[0]
                cursor.close()
                splitter = re.compile('__')
                items = splitter.split(self.annotation)
                splitter = re.compile('_')
                aliases = splitter.split(items[0])
                if len(items) == 1:
                    aliases[0] = ''
                self.alias = aliases[0]
        return self.annotation
    
    

    def getAlias(self):
        if(self.alias == None):
            self.getAnnotation()
        return self.alias
    
    def connect (self):
        try:
            self.conn = MySQLdb.connect (host = efpConfig.DB_HOST, user = efpConfig.DB_USER, passwd = efpConfig.DB_PASSWD, db = efpConfig.DB_ANNO)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])


class Gene_ATX (Gene):
    def __init__(self, id, probesetId):
        Gene.__init__(self, id, "atTax", probesetId)
        self.geneId = self.checkGene(self.geneId)
        
    '''
    # name: checkGene
    # desc: Searchs for At-TAX geneId    
    '''
    def checkGene(self, gene):
        if(gene == None):
            return None
        gene = re.sub("t", "T", gene)
        gene = re.sub("g", "G", gene)
        file = open('%s/geneid.txt' % efpConfig.dataDir)
        if gene+'\n' not in file:
            file.close()
            return None
        else:
            file.close()
            return gene
