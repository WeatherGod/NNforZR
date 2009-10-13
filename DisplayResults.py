#!/usr/bin/env python


from optparse import OptionParser	# Command-line parsing

import pylab
import numpy




parser = OptionParser()
parser.add_option("-t", "--train", dest="train",
		  help="Display results for TRAIN", metavar="TRAIN")
parser.add_option("-d", "--data", dest="data",
		  help="Using training dataset FILE", metavar="FILE")
parser.add_option("-r", "--results", dest="test",
		  help="Using testing RESULTS", metavar="RESULTS")

(options, args) = parser.parse_args()

if (options.train == None) :
    parser.error("Missing TRAIN")

trainFile = options.train
print "The training results file is:", trainFile

if (options.data == None) :
    parser.error("Missing FILE")

dataFile = options.data
print "The dataset file is:", dataFile

if (options.test == None) :
    parser.error("Missing RESULTS")

testFile = options.test
print "The test results file is:", testFile

dataSet = numpy.loadtxt(dataFile, delimiter=',')
testSet = numpy.loadtxt(testFile, delimiter=',')
trainResults = numpy.loadtxt(trainFile)

nwsRainRate = ((10.0 **(dataSet[:, 4]/10.0))/300.0) ** (1/1.4)

nwsMAE = numpy.mean(numpy.abs(dataSet[:, 5] - nwsRainRate))
mlpMAE = numpy.mean(abs(trainResults[:, 3]))

nwsRMSE = numpy.sqrt(numpy.mean((dataSet[:, 5] - nwsRainRate) ** 2))
mlpRMSE = numpy.sqrt(numpy.mean(trainResults[:, 3] ** 2))

nwsSE = numpy.std(dataSet[:, 5] - nwsRainRate)
mlpSE = numpy.std(trainResults[:, 3])

goodPoints = pylab.find(dataSet[:, 4] <= 52.0)
trunc_nwsMAE = numpy.mean(numpy.abs(dataSet[goodPoints, 5] - nwsRainRate[goodPoints]))
trunc_nwsRMSE = numpy.sqrt(numpy.mean((dataSet[goodPoints, 5] - nwsRainRate[goodPoints]) ** 2))
trunc_nwsSE = numpy.std(dataSet[goodPoints, 5] - nwsRainRate[goodPoints])

print '      |  NWS    |  MLP    | Improve | NWS Trunc |'
print 'MAE   | %7.2f | %7.2f | %7.2f | %8.3f |' % (nwsMAE, mlpMAE, nwsMAE - mlpMAE,
						  trunc_nwsMAE)
print 'RMSE  | %7.2f | %7.2f | %7.2f | %8.3f |' % (nwsRMSE, mlpRMSE, nwsRMSE - mlpRMSE,
						  trunc_nwsRMSE)
print 'StdDev| %7.2f | %7.2f |         | %8.3f |' % (nwsSE, mlpSE, trunc_nwsSE)

pylab.scatter(dataSet[:, 4], dataSet[:, 5], '.r')
pylab.hold(True)
pylab.scatter(testSet[:, 3], testSet[:, 4], '.b')
pylab.hold(False)
pylab.show()


