#!/usr/bin/python

import lxml.sax
from lxml import etree
from xml.sax.handler import ContentHandler

import math, sys
import re
import glob
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import subprocess
import os.path
import tempfile
import MySQLdb

import simplejson as json
import urllib2
from urllib2 import HTTPError

import efpDb
import efpImg
import efpConfig

# set HOME environment variable to a directory the httpd server can write to (for matplotlib)
os.environ[ 'HOME' ] = '/tmp/'
import matplotlib
matplotlib.use('Agg')   # set image engine, needed for png creation
import pylab

filecounter = 75

def mafft_align(fasta_file):
    
    cmd =  [\
            "mafft", \
                "--maxiterate", \
                "500", \
                "--globalpair", \
                "--clustalout", \
            "--quiet", \
                "%s"%(fasta_file), \
        ]
    
    outfile = tempfile.mkstemp(prefix="mafft_", dir="output")
    outputr = file(outfile[1], "w")
    retval = subprocess.call(cmd, 0, None, None, outputr, subprocess.STDOUT)
    outputr.close()

    tempf = open(outfile[1], "r")
    lines = tempf.readlines()
    new_outfile = tempfile.mkstemp(prefix="mafft_", dir="output")
    new_out = open(new_outfile[1], "w")
    new_out.writelines(lines[3:])
    new_out.close()
    os.unlink(outfile[1])
    align_file = mview_align(new_outfile[1])
    # mkstemp returns absolute path, need only relative path
    absPath = new_outfile[1].split("/")
    fileName = absPath[-1]
    match = re.search('^mafft', fileName)
    mafft_relPath = None
    if match is not None:
        mafft_relPath = 'output/%s'%(fileName)
    return align_file, mafft_relPath

def mview_align(mafft_align):
    
    cmd = [\
                "mview", \
                "-in", \
                "clustalw", \
                "-html", \
                "head", \
                "-bold", \
                "-width", \
                "70", \
                "-ruler", \
                "on", \
                "-coloring", \
                "consensus", \
                "-threshold", \
                "70", \
                "-consensus", \
                "on", \
                "%s"%mafft_align,\
            ]

    outfile = tempfile.mkstemp(prefix="mview_", suffix=".html", dir="output")
    outputr = file(outfile[1], "w")
    retval = subprocess.call(cmd, 0, None, None, outputr, subprocess.STDOUT)

    # mkstemp returns absolute path, need only relative path
    absPath = outfile[1].split("/")
    fileName = absPath[-1]
    match = re.search('^mview', fileName)
    mview_relPath = None
    if match is not None:
        mview_relPath = 'output/%s'%(fileName)
    return mview_relPath

def write_fasta(sequences, ref_gene, ref_seq):
    
    val, temp_fasta = tempfile.mkstemp()
    
    if temp_fasta != None:
        fasta_file = open(temp_fasta, "w")
        fasta_file.write(">%s\n%s\n"%(ref_gene, ref_seq))
        for gene, sequence in sequences.iteritems():
            fasta_file.write(">%s\n%s\n"%(gene, sequence))
        fasta_file.close()
    return temp_fasta

'''
getGeneList returns a list of genes contained in a tab delimited file, commented lines start with #
begin at the second line of the file

@param fileName the file name
@param n the column that contains the gene agis
'''
def getGeneList(fileName, n):
    geneList = []
    try:
        geneFile = open(fileName, 'r')
        column = n
        lines = geneFile.readlines()
    
        # appends each gene agi to the gene list if the line contains a gene name
        for i in range(1, len(lines)):
            s = lines[i].split('\t')
            if s[column] and (not s[column][0] == '#'):
                geneList.append(s[column])
    
        geneFile.close()
    except IOError, e:
        print >> sys.stderr, "Exception while reading file %s: %d %s" % (fileName, e[0], e[1])
    return geneList


##
# Returns input clamped to [min, max]
#
# @param input Input value
# @param min Minimum value
# @param max Maximum value

def clamp(input, min, max):
    if input > max:
        return max
    if input < min:
        return min
    return input



class Sample:
    def __init__(self, name, view):
        self.name = name
        self.view = view
        self.signals = {}
    
    def getSignal(self, gene, control=0):
        geneId = gene.getGeneId()
        if(geneId not in self.signals):
            self.signals[geneId] = self.view.getTissueSignal(gene, self, control)
        return self.signals[geneId]

    def getName(self):
        return self.name

class Tissue:
    def __init__(self, name, colorKey):
        self.name = name
        if(colorKey == ""):
            colorKey = "#EEEEEE"
        self.colorString = colorKey
        self.colorKey = efpImg.HTMLColorToRGB(colorKey)
        self.samples = []        # List of proj_set_id strings
        self.url = ''
        self.coords = []
        self.control = None
        
    def getName(self):
        return self.name
    
    def getColorString(self):
        return self.colorString
    
    def addURL(self, url):
        self.url = url
    
    def addCoords(self, coords):
        self.coords.append(coords)        

    def addSample(self, sample):
        self.samples.append(sample)
    
    def setControl(self, ctrl):
        self.control = ctrl

    ##
    # For the given gene, returns the average signal among all samples
    # stored in the tissue as well as the standard deviation
    #
    # @param gene
    # @return The tissue's average signal strength and stddev
    def getMeanSignal(self, gene):
        if (len(self.samples) == 0):
            return 0.0

        values = []
        mean = 0.0
        i = 0
        numSamples = len(self.samples)
        while i < numSamples:
            signal = self.samples[i].getSignal(gene)
            if(signal != None):
                values.append(signal)
                mean += signal
                i += 1
        mean /= numSamples
        stddev = math.sqrt(sum([(x - mean)**2 for x in values]) / numSamples)
        stddev = math.floor(stddev*100)/100
        return (mean,stddev)

class Group:
    def __init__(self, name):
        self.tissues = []
        self.name = name
        self.ctrlSamples = []
    
    def addCtrlSample(self, controlSample):        
        self.ctrlSamples.append(controlSample)
    
    def addTissue(self, tissue):
        self.tissues.append(tissue)
        
    def getControlSignal(self, gene):
        if (len(self.ctrlSamples) == 0):
            return 0.0
        
        mean = 0.0
        i = 0
        numSamples = len(self.ctrlSamples)
        while i < numSamples:
            mean += self.ctrlSamples[i].getSignal(gene, 1) # 1 says: get signal for sample as control sample
            i += 1
        mean /= numSamples
        mean = round(mean, 3)
        return mean

class Extra:
    def __init__(self, name, link, parameters, coords, check, checkColumn):
        self.name = name
        self.link = link
        self.button = False

        if check:
            self.check = check
        else:
            self.check = ""

        if checkColumn:
            self.checkColumn = int(checkColumn)

        if parameters == "Yes":
            self.parameters = True
        else:
            self.parameters = False

        self.coords = coords

class View:
    chartSpaceperChar = 0.06
    def __init__(self, name, db, dbGroup, image):
        self.groups = []
        self.name = name
        self.database = db
        self.colorMap = None
        if(os.path.exists(image)):
            self.colorMap = PIL.Image.open(image)      # Original color map
        self.image = image
        self.extras = []
        self.graph = (0,0,0,0)
        self.legend = (15,30)
        self.table = ''
        self.signals = []
        if(dbGroup == None):
            dbGroup = efpConfig.dbGroupDefault
        self.dbGroup = dbGroup
        self.conn = None

    def addExtra(self, extra):
        self.extras.append(extra)
    
    def addGroup(self, group):
        self.groups.append(group)

    def addGraphCoords(self, graph):
        self.graph = graph
        
    def addLegendCoords(self, legend):
        self.legend = legend
        
    def getDatabase(self):
        return self.database
    
    def getImagePath(self):
        return self.image
    
    def getViewMaxSignal(self, gene, ratio, gene2=None):
        viewMaxSignal = 0.0
        viewMaxSignal1 = 0.0
        viewMaxSignal2 = 0.0
        for group in self.groups:
            control = group.getControlSignal(gene)
            if gene2 != None:
                control2 = group.getControlSignal(gene2)
            for tissue in group.tissues:
                (signal,stddev) = tissue.getMeanSignal(gene)
                if signal > viewMaxSignal1:
                    viewMaxSignal1 = signal
                if ratio:
                    if control == 0:
                        signal = 0
                    else:
                        if signal != 0:
                            signal = abs(math.log(signal/control)/math.log(2))
                if gene2 != None:
                    (signal2,stddev2) = tissue.getMeanSignal(gene2)
                    if signal2 > viewMaxSignal2:
                        viewMaxSignal2 = signal2
                    if signal2 == 0:
                        viewMaxSignal2 = 0
                    if control == 0 or control2 == 0:
                        signal = 0
                    else:
			if signal != 0 and signal2 != 0:
                            signal = math.log((signal/control)/(signal2/control2))/math.log(2)
                if(signal > viewMaxSignal):
                    viewMaxSignal = signal
        #assign the max signal for legend
        viewMaxSignal = math.floor(viewMaxSignal*100)/100
        return (viewMaxSignal,viewMaxSignal1,viewMaxSignal2)
    
    # Set up for the Table of Expression Values
    def startTable(self, ratio, relative):
        self.table += '<style type=text/css>\n'
        # Background Colour of the Rows Alternates
        self.table += 'tr.r0 {background-color:#FFFFDD}\n'
        self.table += 'tr.r1 {background-color:#FFFFFF}\n'
        self.table += 'tr.rt {background-color:#FFFF99}\n'
        self.table += 'tr.rg {background-color:#DDDDDD}\n'
        self.table += 'td {font-family:arial;font-size:8pt;}\n'
        self.table += '</style>\n'
        self.table += '<table cellspacing=0 border=1 cellpadding=2 align=center>\n'
        # Column Headings
        self.table += '<tr class=rt><td><B>Group #</B></td><td><B>Tissue</B></td>'
        if (relative == True):
            self.table += '<td><B>Sample signal</B></td><td><B>Control signal</B></td>'
        if (ratio == True):
            self.table += '<td><B>Log2 Ratio</B></td><td><B>Fold-Change</B></td>'
        else:
            self.table += '<td><B>Expression Level</B></td><td><B>Standard Deviation</B></td>'
        self.table += '<td><B>Samples</B></td><td><B>Links</B></td></tr>\n'

    # Produces a row in the Table for each tissue 
    def appendTable(self, tissue, value, n, ratio, stddev, sampleSig, controlSig, color):
        
        signaldict = {}
        valFloor = math.floor(value*100)/100
        self.table += '<tr class=r%s><td>%s</td><td>%s</td>' % ((n%2), n,  tissue.name)
        signaldict['group'] = n
        if ((sampleSig is not None) and (controlSig is not None)):
            sampleSigFloor = math.floor(sampleSig*100)/100
            controlSigFloor = math.floor(controlSig*100)/100
            self.table += '<td align=right>%s</td><td align=right>%s</td><td align=right>%s</td>'% (sampleSigFloor, controlSigFloor, valFloor)
            signaldict['sampleSig'] = sampleSigFloor- controlSigFloor
        else:
            self.table += '<td align=right>%s</td>'%(valFloor)
            signaldict['sampleSig'] = valFloor
        # Fold Change for Relative and Compare Modes
        if ratio == True:
            fold = math.floor(math.pow(2, value)*100) / 100
            self.table += '<td align=right>%s</td>' % (fold)
            signaldict['ratio'] = fold
        else:
            self.table += '<td align=right>%s</td>' % (stddev)
            signaldict['stddev'] = stddev
        self.table += '<td>'
        for sample in tissue.samples:
            self.table += '%s,' % sample.name
        signaldict['samplename'] = tissue.name
        signaldict['signalcolor'] = color
        self.signals.append(signaldict)
        self.table += '</td><td><A target="_blank" href=%s>To the Experiment</A></td></tr>\n' % tissue.url
    
    # Completes Table of Expression Values
    def endTable(self):
        self.table += '</table>\n'

    def saveChart(self, filename, mode):
        datacount = len(self.signals)
        x = pylab.arange(datacount)
        y = []
        colors = []
        ratio = []
        color_arr = ('#FFFFFF', '#FFFFDD')
        bar_width = 0.9
        boxcolor = '#777777'
        gridcolor = '#999999'
        samples = []
        stddev = []
        groups = {}
        bg_colors = []
        max_sample = 0
        for signal in self.signals:
            y.append(signal['sampleSig'])
            #collect sample names
            # insert ' ' upfront to get backgroundcolor down to bottom
            # insert 'Iy' upfront to ensure equal height of text line for all samples
            # so with background color there are now white lines in between
            samples.append('Iy'+' '*500+signal['samplename'])
            if(len(signal['samplename']) > max_sample):
                max_sample = len(signal['samplename'])
            colors.append(color_arr[signal['group']%2])
            if('stddev' in signal):
                stddev.append(signal['stddev'])
            if('ratio' in signal):
                ratio.append(signal['ratio'])
            if (signal['group'] in groups):
                groups[signal['group']] = groups[signal['group']] + 1
            else:
                groups[signal['group']] = 1
            bg_colors.append(signal['signalcolor'])
        # initialize image with size depending on amount of values and length of sample names
        plot = pylab.figure(frameon=False, dpi=180) # initialize image
        img_width = 1.6 + datacount*0.17
        left_border = 0.8/img_width
        img_height = 3+max_sample*self.chartSpaceperChar
        bottom_border = max_sample*self.chartSpaceperChar/img_height
        plot.set_size_inches(img_width, img_height)
        pylab.hold(True)      # add subsequent plots to same image
        pylab.subplots_adjust(bottom=bottom_border, left=left_border, right=(1-left_border), top=0.95, wspace=0, hspace=0) # make room for long x-axis labels (tissue names)
        ax1 = pylab.subplot(111)
        
        # plot colored background for individual groups
        n=0
        c=1
        for group in groups.values():
            ax1.axvspan(n, n+group, facecolor=color_arr[c%2], linewidth=0.0, label=('Group %d'%c))
            c = c+1
            n = n+group
        
        # plot chart depending on mode
        if (mode == "Absolute"):
            ax1.bar(x, y, bar_width, color = boxcolor, linewidth=0, yerr=stddev)
            ax1.yaxis.grid(True, linewidth=0.5, color=gridcolor)
            ax1.set_ylabel('GCOS expression signal (TGT=100, Bkg=20)', size='x-small')
        elif (mode == "Relative"):
            y1_max = 1.1*max(y)
            y1_min = 1.1*min(y)
            y2_max = 1.1*max(ratio)-0.1
            y2_min = 1.1*min(ratio)-0.1
            
            ax1.bar(x, y, bar_width, color = boxcolor, linewidth=0)
            ax1.yaxis.grid(True, linewidth=0.5, color=gridcolor)
            ax1.set_ylabel('difference in GCOS expression signal', size='x-small')
            ax1.set_ylim(ymin=y1_min, ymax = y1_max)
            ax2=pylab.twinx()
            ax2.plot(x+bar_width/2., ratio, color = 'b', linestyle='None', marker='.', label=None) #, visible=False
            ax2.set_ylabel('fold change', size='x-small')
            ax2.set_ylim(ymin=y2_min, ymax = y2_max)
            # workaround for printing labels on x-axis twice (fixed in more current version of matplotlib
            for tl in ax2.get_xticklabels():
                tl.set_visible(False)
            for tline in ax2.get_xticklines():
                tline.set_visible(False)
        else:
            ax1.plot(x+bar_width/2., ratio, color = 'b', linestyle='None', marker='.', label=None)
            ax1.set_ylabel('fold change', size='x-small')
            
        # label x axis
        ax1.set_xticks(x+bar_width/1.2)
        for tline in ax1.get_xticklines():
            tline.set_visible(False)
        labels = ax1.set_xticklabels(samples, rotation=90, ha='right', size='xx-small')
        # set background color according to signal as in efp original image
        for i in range(len(labels)):
            labels[i].set_backgroundcolor(efpImg.RGBToHTMLColor(bg_colors[i]))
            if(efpImg.RGBToGray(bg_colors[i]) < 186):
                labels[i].set_color('#FFFFFF') # set forground color to white if background is dark
        ax1.set_xlim(xmin=0, xmax =datacount)

        pylab.savefig(filename, dpi = 180)

    # Forms a Map Covering the Image of Hyperlinks and Drop-Down Expression Values
    # modified Nov 3 2009 (HN): - Some sample signals in the Root DB are equal to 0 (no signal), and cause errors during calculations. 
    # Added condition to check if signal is zero. 
    # If Absolute mode, if signal = 0, Level = 0; else Level = math.floor(signal * 100). 
    # Else if mode is Relative/Compute: if signal != 0: signal = math.log(signal / control) / math.log(2)
    def getImageMap(self, mode, gene1, gene2, useT, threshold, datasource, grey_low, grey_stddev):
        out = '<map name="imgmap_%s">'%self.name
        for extra in self.extras:
            if extra.parameters == True:
                if useT == None:
                    thresholdSwitch = ""
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s">\n' % (extra.coords, extra.name, extra.link, mode, gene1, gene2, thresholdSwitch, threshold, grey_low, grey_stddev)
                else:
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s">\n' % (extra.coords, extra.name, extra.link, mode, gene1, gene2, useT, threshold, grey_low, grey_stddev)
            else:
                # not a heatmap button
                if extra.check == "":
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s">\n' % (extra.coords, extra.name, extra.link)                    

                # is a heatmap button
                else:
                    geneList = getGeneList(extra.check, extra.checkColumn)

                    # if the searched gene is contained in the heatmap list, activate the link
                    # if extra.button = 1, then gene1 is contained in the list
                    # if extra.button = 2, then gene2 is contained in the list
                    # if extra.button = 3, then both genes are contained in the list
                    if gene1.getGeneId() in geneList:
                        extra.button = 1
                    if gene2.getGeneId() in geneList:
                        extra.button = 2
                    if gene1.getGeneId() in geneList and gene2.getGeneId() in geneList:
                        extra.button = 3

                    # draw button img map
                if extra.button == 1:
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s%s">\n' % (extra.coords, extra.name, extra.link, gene1.getGeneId())
                elif extra.button == 2:
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s%s">\n' % (extra.coords, extra.name, extra.link, gene2.getGeneId())
                elif extra.button == 3:
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s%s%%0A%s">\n' % (extra.coords, extra.name, extra.link, gene1.getGeneId(), gene2.getGeneId())
                else:
                    out += '<area shape="polygon" coords="%s" title="%s" href="%s">\n' % (extra.coords, extra.name, extra.link)
        
        for group in self.groups:
            control = group.getControlSignal(gene1)
            if mode == "Compare":
                control2 = group.getControlSignal(gene2)        
            for tissue in group.tissues:
                (signal,stddev) = tissue.getMeanSignal(gene1)
                if mode == "Absolute":
                    sigFloor = math.floor(signal*100)
                    sigString = "Level: %s, SD: %s" % (sigFloor/100,stddev)
                else:
                    if signal != 0:
                        signal = math.log(signal / control) / math.log(2)
                    if mode == "Compare":
                        (value2,stddev2) = tissue.getMeanSignal(gene2)
                        signal2 = math.log(value2 / control2) / math.log(2)
                        signal =  signal - signal2
                    sigFloor = math.floor(signal*100) / 100
                    fold = math.floor(math.pow(2, signal)*100) / 100
                    sigString = "Log2 Value: %s, Fold-Change: %s" % (sigFloor, fold)
                for coords in tissue.coords:
                    out += '<area shape="polygon" coords="%s" title="%s \n%s" href="%s">\n' % (coords, tissue.name, sigString, tissue.url) 
        
        # Determining coordinates of triangle for link from graph
        x = int(self.graph[0])
        y = int(self.graph[1])
        w = int(self.graph[2])
        h = int(self.graph[3])
        coords = '%i,%i,%i,%i,%i,%i' %(x, y-h, x+w, y, x, y)
        out += '<area shape="polygon" coords="%s" title="The red line indicates the maximum expression of your primary gene, while the blue line, if present, indicates the maximum expression of your secondary gene" href="http://bbc.botany.utoronto.ca/affydb/BAR_instructions.html#efp_distro_%s">\n' % (coords, self.database)
        out += '</map>'
        return out

    ##
    # Draws a color legend
    #
    # @param img Target image    
    # @param title Legend title, drawn at the top of the legend    
    # @param max Maximum value    
    # @param min Minimum value    
    # @param coord Bottom left coordinate of legend, where (0, 0) is the bottom left corner
    # @param stages Number of legend items interpolated between max and min    
        
    def renderLegend(self, img, title, max, min, stages=11, lessThan=True, greaterThan=True, isRelative=False):
        # if max == min draw only on gradient stage in legend
        if(max == min):
            stages = 1
            signalGrad = 0
        else:
            # Change in signal per step, always descending from max
            signalDelta = min - max
            signalGrad = -abs(signalDelta) / (stages - 1)
        signal = max
        
        # Height of each legend item, in pixels (hardcoded for now ...)
        height = 12
    
        draw = PIL.ImageDraw.Draw(img)
    
        # Load a PIL font - these fonts are publically available from http://effbot.org/downloads/
        font = PIL.ImageFont.load("pilfonts/helvR08.pil")
        
        # Get top left coordinates of legend
        left   = self.legend[0]
        #bottom = img.size[1] - (stages + 1) * height - self.legend[1]
        bottom = self.legend[1]
        
        draw.text((left, bottom), title, font=font, fill=(0, 0, 0))
        bottom += height + 2
        
        for y in range(stages):
            signalOutput = " "

            # If we're at either the top or the bottom row of the legend, edit the
            # output string to include less than or greater than signs    
            if y == 0 and greaterThan:
                signalOutput += "> "
            elif y == stages - 1 and lessThan:
                signalOutput += "< "
        
            # Ensure True Minimum
            if y == stages - 1:
                signal = min
            
            # Keep two decimal points accuracy
            signalOutput += str(int(math.floor(signal * 100)) / 100.0)
            if(max == 0):
                intensity = 0
            else:
                intensity = int(signal * 255.0 / max)
                # Clamp intensity to [-255, 255]
                intensity = clamp(intensity, -255, 255)
    
            # Draw the colored rectangle
            if signal > 0:
                # Yellow (neutral) to red
                color = (255, 255 - intensity, 0)
            else:
                # Yellow to blue
                color = (255 + intensity, 255 + intensity, - intensity)
    
            # Draw the colored box
            draw.rectangle((left, bottom + y * height, left + 12, bottom + (y + 1) * height), fill=color)

            # Explanation of Relative Scale
            if y == 0 and isRelative:
                fold = math.pow(2, signal)
                foldDec = (fold%1)*10
                signalOutput += "  (%i.%i-Fold)" % (fold, foldDec)
            
            # Draw the signal value
            draw.text((left + 12, bottom + (y * height)), signalOutput, font=font, fill=(0, 0, 0))
            
            signal += signalGrad
        draw.rectangle((left, bottom + ((y+1) * height), left + 12, bottom + (y + 2) * height), fill=(204,204,204))
        draw.text((left + 12, bottom + ((y+1) * height)), " Masked", font=font, fill=(0, 0, 0))


    ##
    # Renders each tissue according to the ratio of the signal strength 
    # of the first gene to its control relative to ratio of the signal
    # strength of the second gene to its control
    #
    # @param gene1 Gene we're evaluating
    # @param gene2 Base Gene, used as control
    # @param db
    # @return A PIL Image object containing the final rendered data
    
    def renderComparison(self, gene1, gene2, threshold=0.0):
        outImage = self.colorMap.copy()
        
        maxSignal,maxSignal1,maxSignal2 = self.getViewMaxSignal(gene1, False, gene2=gene2)
        maxGreater = False            
        
        if threshold >= efpConfig.minThreshold_Compare:
            max = threshold
            if maxSignal > threshold:
                maxGreater = True
        else:
            # If the user doesn't give us a reasonable value for threshold,
            # use the maximum signal from dbGroup for this gene            
            max = maxSignal    

        intensity = 0 # Cast as int
        log2 = math.log(2)
        
        n = 1
        self.startTable(True, False)
        for group in self.groups:
            control1 = group.getControlSignal(gene1)
            control2 = group.getControlSignal(gene2)
            for tissue in group.tissues:
                # If for some reason this tissue object doesn't have a color key
                # assigned (malformed XML data?), skip it
                if tissue.colorKey == (0, 0, 0):
                    continue
                
                (sig1,stddev1) = tissue.getMeanSignal(gene1)
                ratio1Log = math.log(sig1/control1)/log2
                (sig2,stddev2) = tissue.getMeanSignal(gene2)
                ratio2Log = math.log(sig2/control2)/log2
                
                intensity = int((ratio1Log-ratio2Log) * 255.0 / max)
                intensity = clamp(intensity, -255, 255)
                
                if intensity > 0:
                    # Map values above equal point to [yellow, red]
                    color = (255, 255 - intensity, 0)
                else:
                    # Map values below equal point to [blue, yellow]
                    color = (255 + intensity, 255 + intensity, - intensity)
                # Add to developing Table of Expression Values
                self.appendTable(tissue, ratio1Log-ratio2Log, n, True, None, None, None, tissue.colorKey)
                
                outImage.replaceFill(self.colorMap, tissue.colorKey, color)

            n += 1
    
        # Complete Table of Expression Values
        self.endTable()
    
        self.renderLegend(outImage, "Log2 Ratio", max, -max, lessThan=maxGreater, greaterThan=maxGreater, isRelative=True)        
        return (outImage,maxSignal,maxSignal1,maxSignal2)

    ##
    # Renders tissue data on a scale of the maximum signal.
    #
    # @param gene
    # @param db
    # @return A PIL Image object containing the final rendered data
    
    def renderAbsolute(self, gene, threshold=0.0, grey_mask=False):
        outImage = self.colorMap.copy()
        
        maxSignal,maxSignal1,maxSignal2 = self.getViewMaxSignal(gene, False)        
        maxGreater = False            
        
        if threshold >= efpConfig.minThreshold_Absolute:
            max = threshold            
            if maxSignal > threshold:                
                maxGreater = True
        else:
            # If the user doesn't give us a reasonable value for threshold,
            # use the maximum signal from dbGroup for this gene            
            max = maxSignal
        n = 1
        sdAlert = 0
        self.startTable(False, False)
        for group in self.groups:
            for tissue in group.tissues:
                # If for some reason this tissue object doesn't have a color key
                # assigned (malformed XML data?), skip it
                if tissue.colorKey == (0, 0, 0):
                    continue
                
                (signal,stddev) = tissue.getMeanSignal(gene)
                intensity = int(math.floor(signal * 255.0 / max))
                
                # Grey out expression levels with high standard deviations
                if signal != 0 and stddev/signal > 0.5 and grey_mask == 'on':
                    color = (221, 221, 221)  # CCCCCC
                # Otherwise, colour appropriately
                else:
                    color = (255, 255 - intensity, 0)
                # Add to developing Table of Expression Values
                self.appendTable(tissue, signal, n, False, stddev, None, None, tissue.colorKey)
                # pass an alert back to the user otherwise
                if signal != 0 and stddev/signal > 0.5 and grey_mask != 'on':
                    sdAlert = 1
                
                # Perform fast color replacement
                outImage.replaceFill(self.colorMap, tissue.colorKey, color)

            n += 1

        # Complete Table of Expression Values
        self.endTable()
        
        self.renderLegend(outImage, "Absolute", max, 0, lessThan=False, greaterThan=maxGreater)
        return (outImage,maxSignal,maxSignal1,maxSignal2,sdAlert)
        
        # renderAbsolute
        
    ##
    # Renders tissue data relative to the control signal on a scale of the 
    # maximum signal. Note that unlike the 'max' signal, there is more than 
    # one control compared against. Groups of tissues share the same control 
    # signal against which we compare.
    #
    # @param gene
    # @param db
    # @return A PIL Image object containing the final rendered data
    
    # modified Nov 3 2009 (HN): - Some sample signals in the Root DB are equal to 0 (no signal), and cause errors during calculations. 
    # Added condition to check if signal is zero. If signal = 0, ratioLog2 = 0, else ratioLog2 = math.log(signal/control)/log2
    def renderRelative(self, gene, threshold=0.0, grey_mask=False):
        outImage = self.colorMap.copy()
        
        maxSignal,maxSignal1,maxSignal2 = self.getViewMaxSignal(gene, True)
        maxGreater = False
        
        if threshold >= efpConfig.minThreshold_Relative:
            maxLog2 = threshold
            if maxSignal > threshold:
                maxGreater = True
        else:
            # If the user doesn't give us a reasonable value for threshold,
            # use the maximum signal from dbGroup for this gene
            maxLog2 = maxSignal
        intensity = 0
        log2 = math.log(2)
        
        n = 1
        lowAlert = 0
        self.startTable(True, True)
        for group in self.groups:
            control = group.getControlSignal(gene)
            for tissue in group.tissues:
                # If for some reason this tissue object doesn't have a color key
                # assigned (malformed XML data?), skip it
                if tissue.colorKey == (0, 0, 0):
                    continue
                
                (signal,stddev) = tissue.getMeanSignal(gene)
                
                if (signal == 0 or control == 0):
                    ratioLog2 = 0
                else:
                    ratioLog2  = math.log(signal / control) / log2

                intensity = int(math.floor(255 * (ratioLog2 / maxLog2)))
                intensity = clamp(intensity, -255, 255)

                # Grey out low expression levels
                if signal <= 20 and grey_mask == 'on':
                    color = (221, 221, 221)  # CCCCCC
                # Otherwise, colour appropriately
                elif intensity > 0:
                    color = (255, 255 - intensity, 0)
                else:
                    color = (255 + intensity, 255 + intensity, - intensity)
                # Add to developing Table of Expression Values
                self.appendTable(tissue, ratioLog2, n, True, None, signal, control, tissue.colorKey)
                
                # Alert the user if low filter turned off
                if signal <= 20 and grey_mask != 'on':
                    lowAlert = 1
                
                outImage.replaceFill(self.colorMap, tissue.colorKey, color)

            n += 1

        # Complete Table of Expression Values
        self.endTable()

        self.renderLegend(outImage, "Log2 Ratio", maxLog2, -maxLog2, lessThan=maxGreater, greaterThan=maxGreater, isRelative=True)            
        return (outImage,maxSignal,maxSignal1,maxSignal2,lowAlert)
    
    def drawLine(self, img, signal, offSetVal, displaceVal, top, bottom, color):
        draw = PIL.ImageDraw.Draw(img)
        offsetX = signal*offSetVal
        offsetX += displaceVal
        offsetX = int(offsetX)
        draw.line((offsetX, top, offsetX, bottom), fill=color)
    
    def drawImage(self, mode, maxSignalInDatasource, viewMaxSignal1, viewMaxSignal2, gene1, gene2, img):
        # save generated image in output file.
        # First clean up output folder if necessary
        global filecounter

        files = glob.glob("output/*")
        if len(files) > filecounter:
            os.system("rm -f output/*")
        # Create a named temporary file with global read permissions
        outfile = tempfile.mkstemp(suffix='.png', prefix='efp-', dir='output')
        os.system("chmod 644 " + outfile[1])

        # colours
        red = (255, 0, 0)    #FF0000
        blue = (0, 0, 255)   #0000FF
    
        # Draw the AGI in the top left corner
        draw = PIL.ImageDraw.Draw(img)
        font = PIL.ImageFont.load("pilfonts/helvB10.pil")
        fontsmall = PIL.ImageFont.load("pilfonts/helvB08.pil")
        fontoblique = PIL.ImageFont.load("pilfonts/helvBO08.pil")
        color = (153, 153, 153) # grey, #999999 

        # draw a red box around button links to heatmaps if the searched gene is contained in the heatmap
        for extra in self.extras:
            # extra.button is true when a red box should be drawn, ie. when the searched gene is in the heatmap list
            if not extra.button == False:
                # split the coords into a list and cast to integers
                strCoords = extra.coords.split(',')
                coords = []
                for coord in strCoords:
                    coords.append(int(coord))
                # draw the box using the coords list
                draw.polygon(coords, outline=(255,0,0))

        for group in self.groups:
            for tissue in group.tissues:
                for coords in tissue.coords:
                    strCoords = coords.split(',')
                    intCoordList = []
                    for intCoord in strCoords:
                        intCoordList.append(int(intCoord))
                    #draw.polygon(intCoordList, fill=(255,0,0))

        draw.text(efpConfig.GENE_ID1_POS, gene1.getGeneId(), font=font, fill=color)
        if(gene1.getAlias() != None):
            draw.text(efpConfig.GENE_ALIAS1_POS, gene1.getAlias(), font=fontoblique, fill=color)
        if gene1.getProbeSetId() != None:
            draw.text(efpConfig.GENE_PROBESET1_POS, gene1.getProbeSetId(), font=fontsmall, fill=color)
        if mode == 'Compare':
            draw.text(efpConfig.GENE_ID2_POS, gene2.getGeneId(), font=font, fill=color)
            if(gene2.getAlias() != None):
                draw.text(efpConfig.GENE_ALIAS2_POS, gene2.getAlias(), font=fontoblique, fill=color)
            # underline gene ids to distinguish bars in chart
            draw.line((efpConfig.GENE_ID1_POS[0],efpConfig.GENE_ID1_POS[1]+14, efpConfig.GENE_ID1_POS[0]+8*len(gene1.getGeneId()), efpConfig.GENE_ID1_POS[1]+14), fill=red)
            draw.line((efpConfig.GENE_ID2_POS[0],efpConfig.GENE_ID2_POS[1]+14, efpConfig.GENE_ID2_POS[0]+8*len(gene2.getGeneId()), efpConfig.GENE_ID2_POS[1]+14), fill=blue)
            if gene2.getProbeSetId() !=None:
                draw.text(efpConfig.GENE_PROBESET2_POS, gene2.getProbeSetId(), font=fontsmall, fill=color)

        displaceX = int(self.graph[0])
        displaceY = int(self.graph[1])
        height = int(self.graph[3])
        bottom = displaceY

        datasource = self.database
        if(datasource not in efpConfig.GRAPH_SCALE_UNIT):
            datasource = 'default'
            
        # show where the maximum signal in any data source lies on the little graph
        for (signal, color) in zip((maxSignalInDatasource, viewMaxSignal1, viewMaxSignal2), ('#cccccc', red, blue)):
            if(signal == None): # in case viewMaxSignal2 is not defined
                break
            displaceX = int(self.graph[0])  #(re)set x base coordinate for bar
            for scale_param in efpConfig.GRAPH_SCALE_UNIT[datasource]:
                if signal <= scale_param[0]:  # if signal is within range draw bar
                    self.drawLine(img, signal, scale_param[1], displaceX, 
                                  displaceY - height *(efpConfig.GRAPH_SCALE_UNIT[datasource].index(scale_param)+1)/(1.0 * len(efpConfig.GRAPH_SCALE_UNIT[datasource])), 
                                  bottom, color)
                    break # ... and go to next signal
                else:  # else adjust x base coordinates to next segment in graph
                    displaceX += scale_param[0] * scale_param[1]
        
        img.save(outfile[1])
        imgFilename = outfile[1]
        filecounter += 1
        
        return imgFilename

    '''
    @name: getTissueSignal
    @desc: Returns the tissue signal for a given gene ID
    '''
    def getTissueSignal(self, gene, sample, control = 0):
        sampleId = sample.name
        if(self.conn == None):
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT data_signal FROM sample_data \
                        WHERE data_probeset_id=%s \
                        AND data_bot_id=%s", (gene.getProbeSetId(), sampleId))
        row = cursor.fetchone()
        signal = None
        if row != None:
            signal = row[0]
        cursor.close()
        return signal

    '''
    @name: getMaxInDatasource
    @desc: Returns the max signal and the datasource it occurs in across all datasources of assigned group for a particular gene
    '''
    def getMaxInDatasource(self, gene):
        # overall max signal across all datasources
        overallMax = 0
        maxDatasource = ''
        for dataSource in efpConfig.groupDatasource[self.dbGroup]:
            if dataSource == self.name:
                maxSignal = self.getMaxSignal(gene)
            else:
                spec = Specimen()
                spec.load("%s/%s.xml" % (efpConfig.dataDir, dataSource))
                view = spec.getViews().values()[0]  # take first view in account for max signal
                maxSignal = view.getMaxSignal(gene)
            if maxSignal > overallMax:
                overallMax = maxSignal
                maxDatasource = dataSource
        return overallMax, efpConfig.groupDatasourceName[self.dbGroup][maxDatasource]
    
    def getMaxSignal(self, gene):
        if(self.conn == None):
            self.connect()
        # select the max data signal in this datasource
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(data_signal) FROM sample_data WHERE data_probeset_id=%s", (gene.getProbeSetId()))
        max = cursor.fetchone()[0]
        cursor.close()
        return max

    def connect (self):
        try:
            self.conn = MySQLdb.connect (host = efpConfig.DB_HOST, user = efpConfig.DB_USER, passwd = efpConfig.DB_PASSWD, db = self.database)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    def createGene(self, geneId, probesetId):
        return efpDb.Gene(geneId, self.database, probesetId)

class View_dev (View):
    def getTissueSignal(self, gene, sample, control = 0):
        link = self.database[:]
        link = re.sub("_", "&", link)
        link = re.sub("GENE", gene.getGeneId(), link)
        link = re.sub("SAMPLE", sample.getName(), link)
        try:
            page = urllib2.urlopen(link)
            result = page.read()
            result = result.split()
            jsondump = json.dumps(result)
            pythonObj = json.loads(jsondump)
            signal = str(pythonObj[control+1]).split()[0].split(":")[1] # control signal is 2nd element in JSON array
            signal = re.sub('\"', "", signal)
            signal = re.sub('\,', "", signal)
            signal = round(2**float(signal), 4)
        except HTTPError:
            signal = self.getTissueSignal(gene, sample, control)
        return signal

    def getMaxSignal(self, gene):
        max = 0
        for group in self.groups:
            for tissue in group.tissues:
                for sample in tissue.samples:
                    signal = sample.getSignal(gene)
                    if(signal > max):
                        max = signal
        return max
    
    def createGene(self, geneId, probesetId):
        return efpDb.Gene_ATX(geneId, probesetId)

class View_abio (View_dev):
    def getTissueSignal(self, gene, sample, control = 0):
        return View_dev.getTissueSignal(self, gene, sample, 0)    # for abio control signals use the normal sample signal


class SpecimenHandler(ContentHandler):
    def __init__(self, specimen):
        self.spec = specimen
        self.ctrlSample = ""
        self.sampleDict = {}
    
    def startElementNS(self, dict, qname, attrs):
	uri, name = dict
        #attrs_copy = attrs.copy()
	if name == 'view':
	    try: 
	    	viewClass = attrs.getValueByQName('class')
	    except KeyError, e:
	    	viewClass = attrs.get('class')
            if( (viewClass == None) or (viewClass == "")):
                viewClass = "View"
            self.sampleDict = {}
            exec "self.currentView = %s(attrs.getValueByQName('name'), attrs.getValueByQName('db'), attrs.get('dbGroup'), '%s/' + attrs.getValueByQName('img'))" % (viewClass, efpConfig.dataDir)

        if name == 'coords':
            graph = (attrs.getValueByQName('graphX'), attrs.getValueByQName('graphY'), attrs.getValueByQName('graphWidth'), attrs.getValueByQName('graphHeight'))
            legend = (int(attrs.getValueByQName('legendX')), int(attrs.getValueByQName('legendY')))
            self.currentView.addGraphCoords(graph)
            self.currentView.addLegendCoords(legend)

        if name == 'extra':
	    checkValue = None
	    checkColumn = None
            try:
	        checkValue = attrs.getValueByQName('check')
	    except KeyError, e:
	        checkValue = attrs.get('check')
            try:
	        checkColumn = attrs.getValueByQName('checkColumn')
	    except KeyError, e:
	        checkColumn = attrs.get('checkColumn')
	    #e = Extra(attrs.getValueByQName('name'), attrs.getValueByQName('link'), attrs.getValueByQName("parameters"), attrs.getValueByQName('coords'), attrs.get('check'), attrs.get('checkColumn'))
	    e = Extra(attrs.getValueByQName('name'), attrs.getValueByQName('link'), attrs.getValueByQName("parameters"), attrs.getValueByQName('coords'), checkValue, checkColumn)
            self.currentView.addExtra(e)
        
        if name == 'group':
            self.currentGroup = Group(attrs.getValueByQName('name'))
        
        if name == 'control':
            sampleName = attrs.getValueByQName('sample')
            ctrlSample = self.sampleDict.get(sampleName)
            if ctrlSample == None:
                ctrlSample = Sample(sampleName, self.currentView)
                self.sampleDict[sampleName] = ctrlSample
            self.currentGroup.addCtrlSample(ctrlSample)
        
        if name == 'tissue':
            t = Tissue(attrs.getValueByQName('name'), attrs.getValueByQName('colorKey'))
            self.currentTissue = t
        
        if name == 'link':
            url = attrs.getValueByQName('url')
            self.currentTissue.addURL(url)
        
        if name == 'area':
            coords = attrs.getValueByQName('coords')
            self.currentTissue.addCoords(coords)
            
        if name == 'sample':
            sampleName = attrs.getValueByQName('name')
            sample = self.sampleDict.get(sampleName)
            if sample == None:
                sample = Sample(sampleName, self.currentView)
                self.sampleDict[sampleName] = sample
            self.currentTissue.addSample(sample)
    
    def endElementNS(self, qname, name):
        if name == 'view':
            self.spec.addView(self.currentView)
            
        if name == 'group':
            self.currentView.addGroup(self.currentGroup)
        
        if name == 'tissue':
            self.currentGroup.addTissue(self.currentTissue)
        
class Specimen:
    def __init__(self):
        self.views = {} # Dictionary of views
    
    def addView(self, view):
        self.views[view.name] = view
        
    def getView(self, name):
        return self.views[name]
        
    def getViews(self):
        return self.views
        
    def load(self, file):
        
        # Create the handler
        handler = SpecimenHandler(self)
	#parser.setContentHandler(handler)
        
	tree = etree.parse(file)
	lxml.sax.saxify(tree, handler)


if __name__ == '__main__':
    pass
