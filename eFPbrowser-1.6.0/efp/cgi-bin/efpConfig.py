'''
Created on Nov 24, 2009

@author: rtbreit
'''

DB_HOST = 'localhost'           # hostname of MySQL database server
DB_USER = 'efpro'            # username for database access
DB_PASSWD = 'efp@2015'          # password for database access
DB_ANNO = 'annotations_lookup'  # database name for annotations lookup

# lookup table for gene annotation
DB_ANNO_TABLE = 'agi_annotation'
# column name for gene id in this table
DB_ANNO_GENEID_COL = 'agi'

# lookup table for probeset id
DB_LOOKUP_TABLE = 'at_agi_lookup'
# column name for gene id in this table
DB_LOOKUP_GENEID_COL = 'agi'

# lookup tables for ncbi ids
DB_NCBI_GENE_TABLE = 'agi_ncbi_geneid'
DB_NCBI_PROT_TABLE = 'agi_ncbi_protid'
# column name for gene id in this table
DB_NCBI_GENEID_COL = 'agi'

# Y-AXIS message
Y_AXIS = {}
Y_AXIS['atgenexp'] = "GCOS expression signal (TGT=100, Bkg=20)"
Y_AXIS['http://jsp.weigelworld.org/json?geneId=GENE_sampleId=SAMPLE_dataSet=dev'] = "GCOS expression signal (TGT=100, Bkg=20)"

# Check if probeset <=> geneid lookup exists (1 = lookup exists, 0 = lookup does not exist)
LOOKUP = {}
LOOKUP['atgenexp'] = "1"
LOOKUP['atTax'] = "1"

# initial gene ids when start page is loaded
GENE_ID_DEFAULT1 = 'At1g01010'
GENE_ID_DEFAULT2 = 'At3g27340'

# the little graph on the tga image has a scale
# such that 1 unit is x pixels for different ranges on the x-axis of the graph
# the GRAPH_SCAL_UNIT consists of value pairs: upper end of range and scale unit
# so ((1000, 0.031), (10000, 0.003222), (1000000, 0.00031)) means:
# use 0.031 as scale unit for 0 < signal < 1000
# use 0.003222 as scale unit for 1000 < signal < 10000
# use 0.00031 as scale unit for 10000 < signal < 1000000
# see also efp.drawImage()
GRAPH_SCALE_UNIT = {}
# the default values are used if for the given data source no special values are defined
GRAPH_SCALE_UNIT["default"] = [(1000, 0.031), (10000, 0.003222), (1000000, 0.00031)]

# define additional header text for individual data sources
# you can use key 'default' for each not individually defined
datasourceHeader = {}
datasourceHeader['default'] = ''
datasourceHeader['Seed'] = "<ul><li>Click on citations below the images for the corresponding publications.</li></ul>"

# define additional footer text for individual data sources
# you can use key 'default' for each not individually defined
datasourceFooter = {}
datasourceFooter['default'] = '<ul><li>Find co-expressed genes with <a href="http://bar.utoronto.ca/ntools/cgi-bin/ntools_expression_angler.cgi">Expression Angler</a></li> \
                               <li>Perform electronic Northerns to examine this gene\'s response under different conditions with <a href="http://bar.utoronto.ca/affydb/cgi-bin/affy_db_exprss_browser_in.cgi">Expression Browser</a></li> \
                               <li>See <a href="http://bar.utoronto.ca/affydb/BAR_instructions.html#efp">distribution of average expression levels</a> for the probe sets on the ATH1 GeneChip in the samples used for the eFP Browser, to determine if a given gene is a high or low expresser. The small graph that is shown on the eFP output in Compare and Absolute modes indicates the highest level of expression for the primary gene in red, and the highest level of expression of the secondary gene in blue. The grey line indicates the maximum level of expression of the first gene in any data source</li> \
                               </ul>'

# regular expression for check of gene id input (here agi and probeset id allowed)
inputRegEx = "(At[12345CM]g[0-9]{5})|([0-9]{6}(_[xsfi])?_at)|[0-9]{6,9}"

# default thresholds
minThreshold_Compare = 0.6  # Minimum color threshold for comparison is 0.6, giving us [-0.6, 0.6] on the color legend
minThreshold_Relative = 0.6 # Minimum color threshold for median is 0.6, giving us [-0.6, 0.6] on the color legend ~ 1.5-Fold
minThreshold_Absolute = 10  # Minimum color threshold for max is 10, giving us [0, 10] on the color legend

# coordinates where to write gene id, probeset id and gene alias into image
GENE_ID1_POS = (0, 0)
GENE_ID2_POS = (0, 14)
GENE_PROBESET1_POS = (75, 0)
GENE_PROBESET2_POS = (75, 14)
GENE_ALIAS1_POS = (140, 0)
GENE_ALIAS2_POS = (140, 14)

defaultDataSource = 'Developmental_Map'
# folder with XML configuration files for data sources
dataDir = 'data'

dbGroupDefault = 'ATH1'
# list of datasources in same group to find max signal 
groupDatasource = {}
#groupDatasource["ATH1"] = ['Developmental_Map', 'Seed', 'Hormone', 'Abiotic_Stress', 'Biotic_Stress', 'Natural_Variation', 'Light_Series', 'Root']
#groupDatasource["AtTAX"] = ['Developmental_Map_At-TAX', 'Abiotic_Stress_At-TAX']
groupDatasource["ATH1"] = ['Developmental_Map']
groupDatasource["AtTAX"] = ['Developmental_Map_At-TAX']

# mapping of xml file name to display datasource name
groupDatasourceName = {}
#groupDatasourceName["ATH1"] = {'Developmental_Map':'Developmental Map or Tissue Specific', 'Seed':'Seed', 'Hormone':'Hormone or Chemical', 'Abiotic_Stress':'Abiotic Stress', 'Biotic_Stress':'Biotic Stress', 'Natural_Variation':'Natural Variation','Light_Series':'Light Series','Root':'Root'}
#groupDatasourceName["AtTAX"] = {'Developmental_Map_At-TAX':'Developmental Map AtTAX', 'Abiotic_Stress_At-TAX':'Abiotic Stress AtTAX'}
groupDatasourceName["ATH1"] = {'Developmental_Map':'Developmental Map or Tissue Specific'}
groupDatasourceName["AtTAX"] = {'Developmental_Map_At-TAX':'Developmental Map AtTAX'}

# identifier of Species of this efp browser (also found in ortholog db, if used)
species = 'TAIR10'

# translation table for species id to display name
spec_names = {}
spec_names['POP'] = 'Poplar'
spec_names['TAIR10'] = 'Arabidopsis'
spec_names['MEDV3'] = 'Medicago'
spec_names['SOYBEAN'] = 'Soybean'
spec_names['RICE'] = 'Rice'
spec_names['BARLEY'] = 'Barley'
