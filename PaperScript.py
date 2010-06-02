#!/usr/bin/env python

import glob			# for filename globbing
import os			# for os.sep

import matplotlib.pyplot as pyplot

from ProjectUtils import ObtainResultInfo, PlotCorr, PlotZR

# Run this code if this script is executed like a program
# instead of being loaded like a library file.
if __name__ == '__main__':
   
    from optparse import OptionParser	# Command-line parsing

    parser = OptionParser()
    parser.add_option("-r", "--run", dest="projectName", type="string",
		      help="Use data from PROJECT run", metavar="PROJECT")
    parser.add_option("-d", "--dir", dest="dataDir", type="string",
		      help="Data exists at SRC", metavar="SRC", default=".")
    parser.add_option("-m", "--models", dest="models", action="append", type="string",
		      help="Create images for MODEL", metavar="MODEL")
    parser.add_option("-f", "--format", dest="outputFormat", type="string",
		      help="Desired FORMAT for the output images", metavar="FORMAT", default="png")

    (options, args) = parser.parse_args()
    destDir = '.'

    if options.projectName is None : parser.error("Missing PROJECT!")
    if len(options.models) == 0 : print "WARNING: No models given!"

    corrFig = pyplot.figure(figsize=(12.5, 5))
    zrFig = pyplot.figure(figsize=(12.5, 5))

    for index, model in enumerate(options.models) :
        print "Model: ", model
        resultInfo = ObtainResultInfo(os.sep.join([options.dataDir, options.projectName]), model)

        ####### Plot Corr ##########
	print "Plotting Corr"
	corrAx = corrFig.add_subplot(1, len(options.models), index + 1)
        PlotCorr(resultInfo['testObs'], resultInfo['modelPredicts'], axis=corrAx)
        corrAx.set_title('Model/Obs Correlation Plot - Model: %s' % model, fontsize = 'large')

	#print "Saving..."
        #pylab.savefig(os.sep.join([destDir, "Corr%s_Raw.eps" % model]))
        #pylab.savefig("%s%sCorr%s_Raw.%s"  % (destDir, os.sep, model, options.outputFormat), 
	#	      transparent=True, bbox_inches='tight')

        #pylab.clf()


        ####### Plot ZR ###########
	print "Plotting ZR"
	zrAx = zrFig.add_subplot(1, len(options.models), index + 1)
        PlotZR(resultInfo['reflectObs'], resultInfo['testObs'], resultInfo['modelPredicts'], axis=zrAx)
        zrAx.set_title('Model Comparison - Z-R Plane - Model: %s' % model, fontsize = 'large')

	#print "Saving..."
        #pylab.savefig("%s%sZRPlot_%s_Raw.%s" % (destDir, os.sep, model, options.outputFormat),
	#	      transparent=True, bbox_inches='tight')
        #pylab.clf()

    print "Saving Corr..."
    corrFig.savefig("%s%sCorrModels.%s" % (destDir, os.sep, options.outputFormat),
		    transparent=True, bbox_inches='tight')
    print "Saving ZRPlot..."
    zrFig.savefig("%s%sZRPlot_Models.%s" % (destDir, os.sep, options.outputFormat),
		  transparent=False, bbox_inches='tight')

