#!/usr/bin/python

##
# Converts "#RRGGBB" to an (R, G, B) tuple
# 
# @param 
# @author Paul Winkler
# @notes This code snippet was borrowed from an online article

def HTMLColorToRGB(colorstring):
    if (colorstring == ""):
        return (0, 0, 0)
    
    colorstring = colorstring.strip()
    if colorstring[0] == '#': colorstring = colorstring[1:]
    if len(colorstring) != 6:
        raise ValueError, "input #%s is not in #RRGGBB format" % colorstring
    r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)
   
def RGBToHTMLColor(rgb):
    if len(rgb) != 3:
        raise ValueError, "input %s is not in rgb format" % rgb
    colorstring = '#%02X%02X%02X'%(rgb[0], rgb[1], rgb[2])
    return colorstring
   
def RGBToGray(rgb):
	if len(rgb) != 3:
		raise ValueError, "input %s is not in rgb format" % rgb
	gray = rgb[0]*0.299 + rgb[1]*0.587 + rgb[2]*0.114
	return gray
