#!/usr/bin/env python

import glob			# for filename globbing
import os			# for os.sep

import matplotlib.pyplot as pyplot
import numpy
import matplotlib.cm

from ProjectUtils import ObtainResultInfo


def CalcErr(resultInfo) :
    return numpy.abs(resultInfo['modelPredicts'] - resultInfo['testObs'])

# Run this code if this script is executed like a program
# instead of being loaded like a library file.
if __name__ == '__main__':
   
    from optparse import OptionParser	# Command-line parsing

    parser = OptionParser()
    parser.add_option("-r", "--run", dest="projectName", type="string",
		      help="Use data from PROJECT run", metavar="PROJECT")
    parser.add_option("-d", "--dir", dest="dataDir", type="string",
		      help="Data exists at SRC", metavar="SRC", default=".")
    parser.add_option("-o", "--orig", dest="origModel", type="string",
		      help="Orig MODEL", metavar="MODEL")
    parser.add_option("-n", "--new", dest="newModel", type="string",
		      help="New MODEL", metavar="MODEL")
    parser.add_option("-f", "--format", dest="outputFormat", type="string",
                      help="Desired FORMAT for the output images", metavar="FORMAT", default="png")

    (options, args) = parser.parse_args()
    destDir = '.'

    if options.projectName is None : parser.error("Missing PROJECT!")
    if options.origModel is None : parser.error("Missing original MODEL!")
    if options.newModel is None : parser.error("Missing new MODEL!")




    resultInfo_Orig = ObtainResultInfo(os.sep.join([options.dataDir, options.projectName]), options.origModel)
    resultInfo_New = ObtainResultInfo(os.sep.join([options.dataDir, options.projectName]), options.newModel)

    errImprove = CalcErr(resultInfo_Orig) - CalcErr(resultInfo_New)

    print "Mean Improve: ", numpy.mean(errImprove.flatten())

    fig = pyplot.figure()
    ax = fig.gca()
    ax.hexbin(resultInfo_Orig['reflectObs'].flatten(), errImprove.flatten(), bins='log', cmap=matplotlib.cm.bone_r)
    ax.set_xlabel('Reflectivity [dBZ]', fontsize='large')
    ax.set_ylabel('Error Improvement [mm/hr]', fontsize='large')
    ax.set_title("%s Error Improvement over %s" % (options.newModel, options.origModel), fontsize='large')

    #pylab.savefig(destDir + os.sep + "%s_%s_Improve_Raw.eps" % (options.newModel, options.origModel))
    fig.savefig("%s%s%s_%s_Improve.%s" % (destDir, os.sep, options.newModel, options.origModel, options.outputFormat),
		transparent=True, bbox_inches='tight')

