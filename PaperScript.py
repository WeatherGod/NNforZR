#!/usr/bin/env python

import glob			# for filename globbing
import os			# for os.sep

import pylab

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

    (options, args) = parser.parse_args()
    destDir = '.'

    if options.projectName is None : parser.error("Missing PROJECT!")
    if len(options.models) == 0 : print "WARNING: No models given!"

    pylab.figure()

    for model in options.models :
        print "Model: ", model
        resultInfo = ObtainResultInfo(os.sep.join([options.dataDir, options.projectName]), model)

        ####### Plot Corr ##########
        PlotCorr(resultInfo['testObs'], resultInfo['modelPredicts'], c='black')
        pylab.title('Model/Obs Correlation Plot - Model: %s' % model, fontsize = 12)

        #pylab.savefig(os.sep.join([destDir, "Corr%s_Raw.eps" % model]))
        pylab.savefig(os.sep.join([destDir, "Corr%s_Raw.png"  % model]), dpi = 400)
        pylab.clf()


        ####### Plot ZR ###########
        PlotZR(resultInfo['reflectObs'], resultInfo['testObs'], resultInfo['modelPredicts'])
        pylab.title('Model Comparison - Z-R Plane - Model: %s' % model, fontsize = 12)

        #pylab.savefig(os.sep.join([destDir, "ZRPlot_%s_Raw.eps" % model]))
        pylab.savefig(os.sep.join([destDir, "ZRPlot_%s_Raw.png" % model]), dpi = 400)
        pylab.clf()
 

