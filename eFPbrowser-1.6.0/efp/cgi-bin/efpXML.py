#!/usr/bin/python
#
# Module for determining the names of the XML files available for the eFP Browser

import os

def findXML(dir):
    xML = []
    files = os.listdir(dir)
    for f in files:
        if f.endswith(".xml") and not f.startswith("efp_"):
            xML.append(f[0:-4])
    return xML

if __name__ == '__main__':
    pass

