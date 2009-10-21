#!/usr/bin/env python


from optparse import OptionParser	# Command-line parsing

import glob			# for filename globbing
import os
import numpy
import scipy.stats as ss	# for sem() and other stat funcs
import scipy.stats.stats as sss	# for nanmean() and other nan-friendly funcs
import pylab			# for plotting

from filtertraining import *	# for MakeBins(), Hist2d()

from scipy import optimize
#from arff import arffread

def ZRModel(coefs, reflects) :
    return(((10.0 **(reflects/10.0))/coefs[0]) ** (1/coefs[1]))

def ZRBest(trainData) :
    def errFun(coefs) :
        return(numpy.sqrt(numpy.mean((ZRModel(coefs, trainData[:, 0]) - trainData[:, 1])**2.0)))

    return(optimize.fmin(errFun, [300, 1.4], maxiter=2000, disp=0))





def decimate2d_ZR(vals1, vals2, decimation):
    def Gaussian(vals, means, stds) :
        return(numpy.exp(-((vals - means)**2.0)/(2 * (stds**2.0))) / (numpy.sqrt(2.0 * 3.14) * stds))
    bins1 = MakeBins(vals1, OptimalBinSize(vals1))
    bins2 = MakeBins(vals2, OptimalBinSize(vals2))
    (n, binLocs) = Hist2d(vals1, bins1, vals2, bins2)
    [bin1mesh, bin2mesh] = numpy.meshgrid(bins1[0:-1], bins2[0:-1])
    weights = Gaussian(bin1mesh, 10.0 * numpy.log10(300.0*bin2mesh**1.4), 6.0) + Gaussian(bin2mesh, ZRModel([300, 1.4], bin1mesh), 6.0)
    binCnt = len(numpy.nonzero(n)[0])
    baseThresholds = numpy.array([len(binLocs) * decimation / (binCnt * n[aCoord]) for aCoord in binLocs])
    scale = baseThresholds.max()/weights.max()
    thresholds = baseThresholds * numpy.array([scale * weights[aCoord] for aCoord in binLocs])
    return(numpy.random.random_sample(len(thresholds)) <= thresholds)


############################## Plotting #########################################
def PlotCorr(obs, estimated, **kwargs) :
    pylab.scatter(obs.flatten(), estimated.flatten(), s=1, **kwargs)
    pylab.plot([0.0, obs.max()], [0.0, obs.max()], color='c', hold=True)
    pylab.xlabel('Observed Rainfall Rate [mm/hr]')
    pylab.ylabel('Estimated Rainfall Rate [mm/hr]')
    pylab.xlim((0.0, obs.max()))
    pylab.ylim((0.0, obs.max()))

def PlotZR(reflects, obs, estimated, **kwargs) :
    pylab.scatter(reflects.flatten(), obs.flatten(), color='r', s = 1)
    pylab.scatter(reflects.flatten(), estimated.flatten(), color='b', s = 1, hold = True, **kwargs)
    pylab.xlabel('Reflectivity [dBZ]')
    pylab.ylabel('Rainfall Rate [mm/hr]')
    pylab.xlim((reflects.min(), reflects.max()))
    pylab.ylim((obs.min(), obs.max()))

####################################################################################

def ObtainModelInfo(dirLoc, subProj) :
    modelList = glob.glob(os.sep.join([dirLoc, subProj, 'model_*.txt']))
    modelCoefs = [ProcessModelInfo(filename) for filename in modelList]

    coefNames = modelCoefs[0].keys()
    coefNames.sort()

    vals = []
    for weight in modelCoefs :
        vals.append([weight[coef] for coef in coefNames])

    return((coefNames, numpy.array(vals)))



#    print len(tempy), type(tempy[0])


def AnalyzeResultInfo(modelPredicts, testObs, reflectObs) :
    print "FULL SET"
    sumInfo = DoSummaryInfo(testObs, modelPredicts)
    print "RMSE: %8.4f   %8.4f" % (numpy.mean(sumInfo['rmse']), ss.sem(sumInfo['rmse']))
    print "MAE : %8.4f   %8.4f" % (numpy.mean(sumInfo['mae']), ss.sem(sumInfo['mae']))
    print "CORR: %8.4f   %8.4f" % (numpy.mean(sumInfo['corr']), ss.sem(sumInfo['corr']))




    print "\nZ < 40"
    belowCondition = reflectObs < 40
    belowSumInfo = DoSummaryInfo(numpy.where(belowCondition, testObs, numpy.NaN),
				 numpy.where(belowCondition, modelPredicts, numpy.NaN))
    print "RMSE: %8.4f   %8.4f" % (numpy.mean(belowSumInfo['rmse']), ss.sem(belowSumInfo['rmse']))
    print "MAE : %8.4f   %8.4f" % (numpy.mean(belowSumInfo['mae']), ss.sem(belowSumInfo['mae']))
    print "CORR: %8.4f   %8.4f" % (numpy.mean(belowSumInfo['corr']), ss.sem(belowSumInfo['corr']))


    
    print "\nZ >= 40"
    aboveSumInfo = DoSummaryInfo(numpy.where(belowCondition, numpy.NaN, testObs),
				 numpy.where(belowCondition, numpy.NaN, modelPredicts))
    print "RMSE: %8.4f   %8.4f" % (numpy.mean(aboveSumInfo['rmse']), ss.sem(aboveSumInfo['rmse']))
    print "MAE : %8.4f   %8.4f" % (numpy.mean(aboveSumInfo['mae']), ss.sem(aboveSumInfo['mae']))
    print "CORR: %8.4f   %8.4f" % (numpy.mean(aboveSumInfo['corr']), ss.sem(aboveSumInfo['corr']))



def DoSummaryInfo(obs, estimated) :
    return({'rmse': numpy.sqrt(sss.nanmean((estimated - obs) ** 2.0, axis = 1)),
            'mae': sss.nanmean(numpy.abs(estimated - obs), axis=1),
	    'corr': numpy.diag(numpy.corrcoef(estimated, obs), k=estimated.shape[0]),
	    'sse': numpy.sum((estimated - obs) ** 2.0, axis = 1)})



def ProcessModelInfo(filename) :
    weights = {}
    nodeName = None

    for line in open(filename) :
        line = line.strip()
        if (line.startswith('Linear Node') or line.startswith('Sigmoid Node')) :
	    nodeName = line.split(' ')[-1].strip()
        elif  (line.startswith('Threshold') 
		 or line.startswith('Node')
		 or line.startswith('Attrib')) :
            weights["%s-%s" % (nodeName, line.split()[-2])] = float(line.split()[-1])

    return(weights)

#def ObtainClassifications(filename) :
#    f = open(filename)
#    (name, sparse, alist, m) = arffread(f)
#    f.close()
#
#    return(numpy.array([aRow[-1] for aRow in m]))

def ObtainARFFData(filename, columnIndxs, linesToSkip) :
#    f = open(filename)
#    (name, sparse, alist, m) = arffread(f)
#    f.close()
#
#    return(numpy.array(m)[:, columnIndxs])
    return(numpy.loadtxt(filename, delimiter=',', skiprows=linesToSkip)[:, columnIndxs])
    

def ObtainResultInfo(dirLoc, subProj) :
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()

    skipMap = {'FullSet': 13,
	       'SansWind': 11,
	       'JustWind': 10,
	       'Reflect': 8,
	       'ZRBest': 0,
	       'Shuffled': 13,
	       'NWSZR': 0}


    tempy = [ObtainARFFData(filename, numpy.array([-1, -2, -3]), skipMap[subProj]) for filename in resultsList]
    return({'modelPredicts': numpy.array([aRow[:, 0] for aRow in tempy]),
            'testObs': numpy.array([aRow[:, 1] for aRow in tempy]),
            'reflectObs': numpy.array([aRow[:, 2] for aRow in tempy])})


def SaveSubprojectModel(resultInfo, dirLoc, subProj) :
    """
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()
    """
    summaryInfo = {'rmse': [],
		   'mae': [],
		   'corr': [],
		   'sse': [],
		   'sae': []}
    """
    skipMap = {'FullSet': 13,
	       'SansWind': 11,
	       'JustWind': 10,
	       'Reflect': 8,
	       'ZRBest': 0,
	       'Shuffled': 13,
	       'NWSZR': 0}


    for filename in resultsList :
        tempy = ObtainARFFData(filename, numpy.array([-1, -2, -3]), skipMap[subProj])
        summaryInfo['rmse'].append(numpy.sqrt(numpy.mean((tempy[:, 0] - tempy[:, 1]) ** 2.0)))
	summaryInfo['mae'].append(numpy.mean(numpy.abs(tempy[:, 0] - tempy[:, 1])))
	summaryInfo['corr'].append(numpy.diag(numpy.corrcoef(tempy[:, 0], tempy[:, 1]), k=tempy[:, 0].shape[0]))
	summaryInfo['sse'].append(numpy.sum((tempy[:, 0] - tempy[:, 1]) ** 2.0))
	summaryInfo['sae'].append(numpy.sum(numpy.abs(tempy[:, 0] - tempy[:, 1])))
    """

#    PlotCorr(resultInfo['testObs'], resultInfo['modelPredicts'])
#    pylab.title('Model/Obs Correlation Plot - Model: ' + subProj)
#    pylab.savefig(os.sep.join([dirLoc, "CorrPlot_" + subProj + ".png"]))
#    pylab.clf()
#    print "   Saved Correlation Plot..."

#    PlotZR(resultInfo['reflectObs'], resultInfo['testObs'], resultInfo['modelPredicts'])
#    pylab.title('Model Comparison - Z-R Plane - ' + subProj)
#    pylab.savefig(os.sep.join([dirLoc, "ZRPlot_" + subProj + ".png"]))
#    pylab.clf()
#    print "   Save ZR Plot..."

    summaryInfo = DoSummaryInfo(resultInfo['testObs'], resultInfo['modelPredicts'])
    statNames = summaryInfo.keys()
    for statname in statNames :
        numpy.savetxt(os.sep.join([dirLoc, "summary_%s_%s.txt" % (statname, subProj)]), summaryInfo[statname])
        print "        Saved summary data for", statname



# Run this code if this script is executed like a program
# instead of being loaded like a library file.
if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option("-d", "--dir", dest="projLoc",
                      help="Project located at DIR", metavar="DIR")

    (options, args) = parser.parse_args()

    if (options.projLoc == None) :
        parser.error("Missing DIR")

    dirLoc = options.projLoc
    print "The project is at:", dirLoc

    (pathName, dirNames, filenames) = os.walk(dirLoc).next()

    for subProj in dirNames :
        print "Subproject:", subProj
        SaveSubprojectModel(dirLoc, subProj)

#    print "Subproject: NWS ZR"
#    resultInfo_nws = ObtainResultInfo(dirLoc, "Reflect")
#    resultInfo_nws['modelPredicts'] = ZRModel([300, 1.4], resultInfo_nws['reflectObs'])
#    SaveSubprojectModel(resultInfo_nws, dirLoc, "nwszr")
    

