#!/usr/bin/python

import os
import cgi
import tempfile
import string
import efp, efpXML, efpConfig, efpService
import re


form = cgi.FieldStorage(keep_blank_values=1)

error = 0
errorStrings = []
alertStrings = []
testalertStrings = []
orthologStrings = {}
alignOrthologs = {}
lowAlert = 0
sdAlert = 0
primaryProbeset = None
secondaryProbeset = None

img = None
imgMap = {}
imgFilename = {}
tableFile = {}
views = []

# Retrieve cgi inputs
dataSource    = form.getvalue("dataSource")
primaryGene   = form.getvalue("primaryGene")
secondaryGene = form.getvalue("secondaryGene")
thresholdIn   = form.getvalue("threshold")
mode          = form.getvalue("modeInput")
useThreshold  = form.getvalue("override")
grey_low      = form.getvalue("modeMask_low")
grey_stddev   = form.getvalue("modeMask_stddev")
ncbi_gi	      = form.getvalue("ncbi_gi")
primaryProbeset   = form.getvalue("primaryProbeset")
secondaryProbeset = form.getvalue("secondaryProbeset")

# Default gene id
if primaryGene == None:
   primaryGene = efpConfig.GENE_ID_DEFAULT1
if secondaryGene == None:
    secondaryGene = efpConfig.GENE_ID_DEFAULT2

if useThreshold == "":
    useThreshold = None

# set orthoListOn to off
orthoListOn = "0"

# Try Entered Threshold; if fails or threshold not checked use default threshold
if useThreshold != None:
    try:
        threshold = float(thresholdIn) # Convert str to float
    except:
		# Threshold string was malformed
		error = 1
		errorStr = 'Invalid Threshold Value "%s"<br>' % thresholdIn
		errorStrings.append(errorStr)
		useThreshold = None
if useThreshold == None and thresholdIn == None:
    # assign a default value for first calls
    if mode == "Relative" or mode == "Compare":
        threshold = 2.0
    else:	#Absolute or none
        threshold = 500
    firstCall = 1
else:
    threshold = float(thresholdIn)
    firstCall = 0

if dataSource == None:
    dataSource = efpConfig.defaultDataSource


# Serialize data from XML file into a Specimen object
spec = efp.Specimen()
xmlName = "%s/%s.xml" % (efpConfig.dataDir, dataSource)
spec.load(xmlName)

# Right now the browser only has one view - "all"
# In the future, there should be a drop down menu letting users
# choose multiple views

defaultImgFilename = "%s/%s_image.png" % (efpConfig.dataDir, dataSource)
if mode == None:
    # If no mode is selected (99% of the time this means the user just arrived
    # at the page), just show them a color map
    
    # Set Developmental_Map as default DataSource
    if dataSource == None:
        dataSource = efpConfig.defaultDataSource

else:        
###-----------------------------------"all" view-------------------------------------------------------------------------------------------------------------------------------
    for name, view in spec.getViews().iteritems():
        # If either of these probe IDs are None (bad inputs), then we just
        # spit out the default image again
        gene1 = view.createGene(primaryGene, probesetId=primaryProbeset)
        gene2 = view.createGene(secondaryGene, probesetId=secondaryProbeset)
        
        if gene1.getGeneId() is None or gene1.getProbeSetId() is None:
            errorStr = 'The requested Primary gene / probeset ID "%s" cannot be found in %s datasource ' % (primaryGene, view.dbGroup)
            error = 1
            errorStrings.append(errorStr)
        elif mode == 'Compare' and gene2.getProbeSetId() is None:
            error = 1
            errorStr = 'The requested Secondary gene / probeset ID "%s" cannot be found in %s datasource <br>' % (secondaryGene, view.dbGroup)
            errorStrings.append(errorStr)
        elif primaryGene == secondaryGene and mode == 'Compare':
            error = 1
            errorStr = 'The requested Secondary gene / probeset ID "%s" must be different than the Primary ID<br>' % secondaryGene
            errorStrings.append(errorStr)
            viewMaxSignal = 2.0
        else:
            if mode == 'Absolute':
                if useThreshold:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2,sdAlert) = view.renderAbsolute(gene1, threshold, grey_mask=grey_stddev)
                else:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2,sdAlert) = view.renderAbsolute(gene1, grey_mask=grey_stddev)
            elif mode == 'Relative':
                if useThreshold:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2,lowAlert) = view.renderRelative(gene1, threshold, grey_mask=grey_low)
                else:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2,lowAlert) = view.renderRelative(gene1, grey_mask=grey_low)
            elif mode == 'Compare':    
                if useThreshold:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2) = view.renderComparison(gene1, gene2, threshold)
                else:
                    (img,viewMaxSignal,viewMaxSignal1,viewMaxSignal2) = view.renderComparison(gene1, gene2)

            # find the max signal across all datasources and provide a link to that datasource
            (maxSignalInDatasource, maxDatasource) = view.getMaxInDatasource(gene1)
            
            maxSignalInDatasource = round(maxSignalInDatasource,2)
            # maxDatasource = re.sub("_"," ", maxDatasource)
            alertStr = "For %s data, this probe set reaches its maximum expression level (expression potential) of <b>%s</b> in the <b>%s</b> data source." % (view.dbGroup, maxSignalInDatasource, maxDatasource)
            alertStrings.append(alertStr)

            # alert the user that the scale has changed if no threshold is set
            if useThreshold == None and firstCall != 1:
                if viewMaxSignal > threshold:
                    useThresholdFlag = "on"
                    thresholdLevelSuggested = maxSignalInDatasource
                    if mode == 'Relative':
                        thresholdLevelSuggested = 4
                    if mode == 'Compare':
                        thresholdLevelSuggested = 4
                    alertStr = "For %s data, note the maximum signal value has increased to %s from %s. Use the <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>Signal Threshold option to keep it constant at %s</a>, or enter a value in the Signal Threshold box, such as <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>%s</a>. The same colour scheme will then be applied across all views.<br>" % (view.dbGroup, viewMaxSignal, threshold, dataSource, mode, primaryGene, secondaryGene, useThresholdFlag, threshold, grey_low, grey_stddev, threshold, dataSource, mode, primaryGene, secondaryGene, useThresholdFlag, thresholdLevelSuggested, grey_low, grey_stddev, thresholdLevelSuggested)
                    alertStrings.append(alertStr)
                elif viewMaxSignal < threshold:
                    useThresholdFlag = "on"
                    thresholdLevelSuggested = maxSignalInDatasource
                    if mode == 'Relative':
                        thresholdLevelSuggested = 4
                    if mode == 'Compare':
                        thresholdLevelSuggested = 4
                    alertStr = "For %s data, note the maximum signal value has decreased to %s from %s. Use the <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>Signal Threshold option to keep it constant at %s</a>, or enter a value in the Signal Threshold box, such as <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>%s</a>. The same colour scheme will then be applied across all views.<br>" % (view.dbGroup, viewMaxSignal, threshold, dataSource, mode, primaryGene, secondaryGene, useThresholdFlag, threshold, grey_low, grey_stddev, threshold, dataSource, mode, primaryGene, secondaryGene, useThresholdFlag, thresholdLevelSuggested, grey_low, grey_stddev, thresholdLevelSuggested)
                    alertStrings.append(alertStr)
                else:
                    alertStr = ""
                threshold = viewMaxSignal
            elif useThreshold == None and firstCall == 1:
                threshold = viewMaxSignal

            # alert the user if SD filter or low filter should be activated
            if grey_stddev != "on" and sdAlert == 1 and mode == 'Absolute':
                grey_stddev_flag = "on"
                if useThreshold == None:
                    useThreshold = ""
                alertStr = "Some samples exhibit high standard deviations for replicates. You can use <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>standard deviation filtering</a> to mask those with a deviation greater than half their expression value.<br>" % (dataSource, mode, primaryGene, secondaryGene, useThreshold, threshold, grey_low, grey_stddev_flag)
                alertStrings.append(alertStr)
            # alert the user if SD filter or low filter should be activated
            if grey_low != "on" and lowAlert == 1 and mode == 'Relative':
                grey_low_flag = "on"
                if useThreshold == None:
                    useThreshold = ""
                alertStr = "Some sample ratios were calculated with low values that exhibit higher variation, potentially leading to ratios that are not a good reflection of the biology. You can <a href='efpWeb.cgi?dataSource=%s&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s'>low filter below 20 units</a> to mask these.<br>" % (dataSource, mode, primaryGene, secondaryGene, useThreshold, threshold, grey_low_flag, grey_stddev)
                alertStrings.append(alertStr)

            # Otherwise, we render and display the option
            imgMap[view.name] = view.getImageMap(mode, gene1, gene2, useThreshold, threshold, dataSource, grey_low, grey_stddev)

        if img != None:
            imgFilename[view.name] = view.drawImage(mode, maxSignalInDatasource, viewMaxSignal1, viewMaxSignal2, gene1, gene2, img)
            #Create a table of Expression Values and save it in a temporary file
            expTable = view.table
            tableFile[view.name] = tempfile.mkstemp(suffix='.html', prefix='efp-', dir='output')
            os.system("chmod 644 " + tableFile[view.name][1])
            tf = open(tableFile[view.name][1], 'w')
            tf.write(expTable)
            tf.close()
            chartFile = tableFile[view.name][1].replace(".html", ".png")
            view.saveChart(chartFile, mode)
            views.append(view.name)
        
###-------------------------------------------------------HTML codes----------------------------------------------------------------------------------------------------------------------
print 'Content-Type: text/html\n'
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
print '<html>'
print '<head>'
print '  <title>%s eFP Browser</title>' % efpConfig.spec_names[efpConfig.species]
print '  <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
print '  <meta name="keywords" content="%s, genomics, expression profiling, mRNA-seq, Affymetrix, microarray, protein-protein interactions, protein structure, polymorphism, subcellular localization, proteomics, poplar, rice, Medicago, barley, transcriptomics, proteomics, bioinformatics, data analysis, data visualization, AtGenExpress, PopGenExpress, cis-element prediction, coexpression analysis, Venn selection, molecular biology">' % efpConfig.spec_names[efpConfig.species]
print '  <link rel="stylesheet" type="text/css" href="efp.css"/>'
print '  <link rel="stylesheet" type="text/css" href="domcollapse.css"/>'
print '  <script type="text/javascript" src="popup.js"></script>'
print '  <script type="text/javascript" src="efp.js"></script>'
print '  <script type="text/javascript">'
print '    regId = /%s/i;' % efpConfig.inputRegEx
print '  </script>'
print '  <script type="text/javascript" src="domcollapse.js"></script>'
print '</head>'

print '<body><form action="efpWeb.cgi" name="efpForm" method="POST" onSubmit="return checkAGIs(this)">'
print '<table width="788" border="0" align="center" cellspacing="1" cellpadding="0">'

print '<tr><td>'
print "<h1 style='vertical-align:middle;'><a href='http://bar.utoronto.ca'><img src='http://bar.utoronto.ca/bbc_logo_small.gif' alt='To the Bio-Array Resource Homepage' border=0 align=absmiddle></a>&nbsp;<img src='http://bar.utoronto.ca/bar_logo.gif' alt='The Bio-Array Resource' border=0 align=absmiddle>&nbsp;<img src='/efp/eFP_logo_large.png' align=absmiddle border=0>&nbsp;%s eFP Browser" % efpConfig.spec_names[efpConfig.species]
print "<br><img src='http://bar.utoronto.ca/images/green_line.gif' width=98%% alt='' height='6px' border=0></h1>"

print '</td></tr>'
print '<tr><td align="middle">'
print '    <table>'
print '      <tr align = "center"><th>Data Source</th>'
print '      <th>Mode'
print '<input type="checkbox" name="modeMask_stddev" title="In Absolute Mode, check to mask samples that exhibit a standard deviation of more than 50 percent of the signal value" '
if grey_stddev == "on":
    print 'checked'
print ' value="on" />'
print '<input type="checkbox" name="modeMask_low" title="In Relative Mode, check to mask the use of low expression values in ratio calculations" '
if grey_low == "on":
    print 'checked'
print ' value="on" />'
print '</th><th>Primary Gene ID</th><th>Secondary Gene ID</th>'
print '      <th id="t1">Signal Threshold<input type="checkbox" name="override" title="Check to enable threshold" onclick="checkboxClicked(this.form)" '
if useThreshold == "on":
    print 'checked'
print       ' value="on" />'
print '</th><th></th></tr>'
print '      <tr><td>'

# Help Link
print '      <img src="http://bar.utoronto.ca/affydb/help.gif" border=0 align="top" alt="Click here for instructions in a new window" onClick="HelpWin = window.open(\'http://bar.utoronto.ca/affydb/BAR_instructions.html#efp\', \'HelpWindow\', \'width=600,height=300,scrollbars,resizable=yes\'); HelpWin.focus();">&nbsp;'

# Build drop down list of Data Sources
if mode == None:
    print '<select name="dataSource" onchange="location.href=\'efpWeb.cgi?dataSource=\' + this.options[this.selectedIndex].value ;">'
elif useThreshold == None:
    thresholdSwitch = ""
    print '      <select name="dataSource" onchange="location.href=\'efpWeb.cgi?dataSource=\' + this.options[this.selectedIndex].value + \'&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s\' ;">' %(mode, primaryGene, secondaryGene, thresholdSwitch, threshold, grey_low, grey_stddev)
else:
    print '      <select name="dataSource" onchange="location.href=\'efpWeb.cgi?dataSource=\' + this.options[this.selectedIndex].value + \'&modeInput=%s&primaryGene=%s&secondaryGene=%s&override=%s&threshold=%s&modeMask_low=%s&modeMask_stddev=%s\' ;">' %(mode, primaryGene, secondaryGene, useThreshold, threshold, grey_low, grey_stddev)

xML = efpXML.findXML(efpConfig.dataDir)
for x in sorted(xML):
    print '    <option value="%s"' % x
    # To preserve modes between form submits
    if dataSource == x:
        print 'selected'
    xText = string.replace(x,'_',' ')
    print '>%s</option>' % xText
print '      </select></td>'
# xML = None
# reload(efpXML)

# Build drop down list of modes
if mode == None:
	print '      <td><select selected="Absolute" name="modeInput" onchange="changeMode(this.form)">' 
else:
	print '		 <td><select selected="Absolute" name="modeInput" onchange="location.href=\'efpWeb.cgi?dataSource=%s&modeInput=\' + this.options[this.selectedIndex].text + \'&primaryGene=%s&secondaryGene=%s&modeMask_low=%s&modeMask_stddev=%s\' ">' %(dataSource, primaryGene, secondaryGene, grey_low, grey_stddev)

# Preserve mode between form submits. If the user selected 'Compare' as his/her
# mode, when the page reloads, the list should still have 'Compare' selected.
if mode == 'Relative':
    print '    <option>Absolute</option>'
    print '    <option selected>Relative</option>'
    print '    <option>Compare</option>'
elif mode == 'Compare':
    print '    <option>Absolute</option>'
    print '    <option>Relative</option>'
    print '    <option selected>Compare</option>'
else: # Default (Absolute)
    print '    <option selected>Absolute</option>'
    print '    <option>Relative</option>'
    print '    <option>Compare</option>'

print '      </select></td><td>'
print '      <input type="text" id="g1" name="primaryGene" value="%s" size=17/></td><td>' % primaryGene
print '      <input type="text" id="g2" name="secondaryGene" size=17 value="%s" ' % secondaryGene
if mode != 'Compare':
    print 'disabled'
print '      /></td><td>'

print '      <input type="text" id="t0" name="threshold" value="%s" ' % threshold
if useThreshold == None: 
    print 'disabled'
print '      /></td>'
print '      <td><input type="submit" value="Go"/></td></tr>'
print '    </table>'
print '    </form>'
print '</td></tr>'
print '<tr><td>'

if error:
    print '    <ul>'
    for row in errorStrings:
        print '<li class="error">%s</li>' % row
    print '    </ul>'

# print additional header text if configured for selected data source
if dataSource in efpConfig.datasourceHeader:
    print '%s' % efpConfig.datasourceHeader[dataSource]
elif 'default' in efpConfig.datasourceHeader:
    print '%s' % efpConfig.datasourceHeader['default']

if len(alertStrings) > 0:
    print '    <ul>'
    for row in alertStrings:
        print '<li>%s</li>' % row
    print '    </ul>'

if mode != None and error == 0:
    ###----------------------check external services-------------------------------------------------------------------------------------------------------------------------------------------------
    # Serialize services data from XML file into a Info object
    info = efpService.Info()
    if (info.load("%s/efp_info.xml" % efpConfig.dataDir) == None):
        print '<table style="margin-left:auto; margin-right:0;"><tr>'        
        for name in (info.getServices()):
            service = info.getService(name)
            external = service.getExternal()
            highlight1 = service.checkService(primaryGene)
            highlight2 = None
            if(mode == 'Compare'):
                highlight2 = service.checkService(secondaryGene)
            if highlight1 == 'error' or highlight2 == 'error':
                print '<td><img title="connection error for service %s" width="50" height="50" alt="connection error" src="%s/error.png"></td>'% (name, efpConfig.dataDir)
                continue
            elif (highlight1):
                link = service.getLink(primaryGene)
                gene = primaryGene
            elif (highlight2):
                link = service.getLink(secondaryGene)
                gene = secondaryGene
            else:
                print '<td><img title="No %s data found" width="50" height="50" alt="No %s data found" style="opacity:0.30;filter:alpha(opacity=30);" src="%s/%s"></td>'%(name, name, efpConfig.dataDir, service.icon)
                continue
            if link:
                if external == "true":
                    print '<td><a target="_blank" title="%s gene %s" href="%s"><img width="50" height="50" alt="%s gene %s" src="%s/%s"></a></td>'%(name, gene, link, name, gene, efpConfig.dataDir, service.icon)
                else:
                    print '<td><a target="_blank" title="%s for gene %s" href="%s"><img width="50" height="50" alt="%s for gene %s" src="%s/%s"></a></td>'%(name, gene, link, name, gene, efpConfig.dataDir, service.icon)
            else:
                print '<td><img target="_blank" title="%s found for gene %s" width="50" height="50" alt="%s found for %s" src="%s/%s"></td>'%(name, gene, name, gene, efpConfig.dataDir, service.icon)
        print '</tr></table>'

###----------------------print the image-------------------------------------------------------------------------------------------------------------------------------------------------
    view_no = 1
    for view_name in views:
        print '<tr><td>'
        imgFile = imgFilename[view_name];
        temp_imgPath = imgFilename[view_name].split("/")
        last_element = temp_imgPath[-1]
        match = re.search('^efp', last_element) 
        if match is not None:
            imgFile = 'output/%s'%(last_element)
        print '  <img src="%s" border="0" ' % imgFile
        if view_name in imgMap:
            print 'usemap="#imgmap_%s">'%view_name
            print '%s' % imgMap[view_name]
        else:
            print '>'
        print '</td></tr>'
        # Creates Button and Link to Page for Table of Expression Values
        print '<tr align="center"><td><br>'
        temp_tablePath = tableFile[view_name][1].split("/")
        tableFile_name = 'output/%s'%(temp_tablePath[-1])
        print '<input type="button" name="expressiontable" value="Click Here for Table of Expression Values" onclick="resizeIframe(\'ifr%d\', ifr%d);popup(\'table%d\', \'fadein\', \'center\', 0, 1)">&nbsp;&nbsp;' % (view_no, view_no, view_no)
        tableChart_name = tableFile_name.replace(".html", ".png")
        print '<input type="button" name="expressionchart" value="Click Here for Chart of Expression Values" onclick="popup(\'chart%d\', \'fadein\', \'center\', 0, 1)">' % (view_no)
        print '<script type="text/javascript">'
        popup_content = '<span style="color:#000000"><b>For table download right click <a href="%s">here</a> and select "Save Link As ..."</b></span>' % tableFile_name
        popup_content += '<div class="closewin_text">'
        popup_content += '<a href="" onclick="popdown(\\\'table%d\\\');return false;">' % (view_no)
        popup_content += '<span style="color:#000000">[Close]</span></a><br><br>'
        popup_content += '<a href="" onclick="switchPopup(\\\'table%d\\\', \\\'chart%d\\\');return false;">' % (view_no, view_no)
        popup_content += '<span style="color:#000000">[Switch to<br> Chart]</span></a></div>'
        popup_content += '<div class="chart"><iframe id="ifr%d" name="ifr%d" width=900 frameborder=0 src="%s">' % (view_no, view_no, tableFile_name)
        popup_content += 'Your browser doesn\\\'t support iframes. Please use link abvoe to open expression table</iframe></div>'
        popup_width = '1000';
        bg_color = '#FFFFFF';
        print "loadPopup(\'table%d\',\'%s\',\'%s\',%s);" % (view_no, popup_content, bg_color, popup_width)
        popup_content = '<div class="closewin_text">'
        popup_content += '<a href="" onclick="popdown(\\\'chart%d\\\');return false;">' % (view_no)
        popup_content += '<span style="color:#000000">[Close]</span></a><br><br>'
        popup_content += '<a href="" onclick="resizeIframe(\\\'ifr%d\\\', ifr%d);switchPopup(\\\'chart%d\\\', \\\'table%d\\\');return false;">' % (view_no, view_no, view_no, view_no)
        popup_content += '<span style="color:#000000">[Switch to<br>Table]</span></a><br><br>'
        popup_content += '<a href="" onclick="zoomElement(\\\'image%d\\\', 0.1);return false;">' %(view_no)
        popup_content += '<span style="color:#000000">[Zoom +]</span></a><br>'
        popup_content += '<a href="" onclick="zoomElement(\\\'image%d\\\', -0.1);return false;">' %(view_no)
        popup_content += '<span style="color:#000000">[Zoom -]</span></a><br>'
        popup_content += '<a href="" onclick="zoomElement(\\\'image%d\\\', 0);return false;">' % (view_no)
        popup_content += '<span style="color:#000000">[Reset<br>zoom]</span></a></div>'
        popup_content += '<div class="chart"><img id="image%d" height="580px" src="%s"><br></div>' % (view_no, tableChart_name)
        print "loadPopup(\'chart%d\',\'%s\',\'%s\',%s);" % (view_no, popup_content, bg_color, popup_width)
        print "</script>"
        print '<br></td></tr>'
        view_no = view_no + 1
    print '  <tr><td><br><ul>'
    print '  <li>%s was used as the probe set identifier for your primary gene, %s (%s)</li>' % (gene1.getProbeSetId(), gene1.getGeneId(), gene1.getAnnotation())
    if mode == 'Compare':
    	print '  <li>%s was used as the probe set identifier for the secondary gene, %s (%s)</li>' % (gene2.getProbeSetId(), gene2.getGeneId(), gene2.getAnnotation())
    print '  </ul>'
    if(dataSource in efpConfig.datasourceFooter):
        print efpConfig.datasourceFooter[dataSource]
    else:
        print efpConfig.datasourceFooter['default']
    print '</td></tr>'
    print '<tr><td><img src="http://bar.utoronto.ca/bbclone/stats_image.php" title="" name="thumbnail" border="0" width="0px" height="0px"></td></tr>'
else:
    print '  <img src="%s" border="0">' % (defaultImgFilename)
print '</table>'
print '</body>'

print '</html>'
