#!/usr/bin/env python


import glob			# for filename globbing
import os			# for os.sep
import numpy
import scipy.stats as ss	# for sem() and other stat funcs
import scipy.stats.stats as sss	# for nanmean() and other nan-friendly funcs
import pylab			# for plotting
import matplotlib		# for colormaps

from filtertraining import *	# for MakeBins(), Hist2d()



def decimate2d_ZR(vals1, vals2, decimation):
    """
    Don't use this.  It is experimental, and really a poor idea!
    """
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

#################################################################################
#     Plotting 
#################################################################################
def PlotCorr(obs, estimated, axis=None, **kwargs) :
    if axis is None :
        axis = pylab.gca()

    obs = obs.flatten()
    estimated = estimated.flatten()
#    pylab.scatter(obs, estimated, s=1, **kwargs)
    axis.hexbin(obs, estimated, bins='log', cmap=matplotlib.cm.gray_r, **kwargs)
    axis.plot([0.0, obs.max()], [0.0, obs.max()], color='gray', linewidth=2.5)
    axis.set_xlabel('Observed Rainfall Rate [mm/hr]', fontsize='large')
    axis.set_ylabel('Estimated Rainfall Rate [mm/hr]', fontsize='large')
    axis.set_xlim((0.0, obs.max()))
    axis.set_ylim((0.0, obs.max()))

def PlotZR(reflects, obs, estimated, axis=None, **kwargs) :
    if axis is None :
        axis = pylab.gca()

    theScale = 1

    # Doing some data 'reduction'...
    #   Starting with precision reduction
    reflects = reflects.round(theScale).flatten()
    obs = obs.round(theScale).flatten()
    estimated = estimated.round(theScale).flatten()

    print "Orig Len:", len(obs)

    # Now, we feed the data pairs through set() to get unique pairs,
    #    then rezip that data so that it can be passed as positional arguements
    #    into scatter
    obsZR = zip(*set(zip(reflects, obs)))
    modZR = zip(*set(zip(reflects, estimated)))

    print "truncated obs len:", len(obsZR[0]), "   truncated models len:", len(modZR[0])

    axis.scatter(*obsZR, s = 3.0, linewidths = 0, c='grey')
    axis.scatter(*modZR, c='black', s = 0.3, linewidths=0, **kwargs)
    #pylab.hexbin(reflects, obs, bins='log', cmap=matplotlib.cm.gray_r, **kwargs)
    #pylab.hexbin(reflects, estimated, bins='log', cmap=matplotlib.cm.gray_r, **kwargs)
    axis.set_xlabel('Reflectivity [dBZ]', fontsize='large')
    axis.set_ylabel('Rainfall Rate [mm/hr]', fontsize='large')
    axis.set_xlim((reflects.min(), reflects.max()))
    axis.set_ylim((obs.min(), obs.max()))

####################################################################################
#      Project Analysis
####################################################################################
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
	    'bias': numpy.mean(estimated - obs, axis=1)})


###############################################################################
#       Loading data
###############################################################################
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


def ObtainARFFData(filename, columnIndxs, linesToSkip) :
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


########################################################################
#        Saving processed data
########################################################################

def SaveSummaryInfo(resultInfo, dirLoc, subProj) :
    """
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()
    
    summaryInfo = {'rmse': [],
		   'mae': [],
		   'corr': []}
    
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
        print "        Saved summary data for", statname, " Mean: ", numpy.mean(summaryInfo[statname]), "  StdDev: ", numpy.std(summaryInfo[statname])


def SaveSubprojectModel(dirLoc, subProj) :
    resultsList = glob.glob(os.sep.join([dirLoc, subProj, 'results_*.csv']))
    resultsList.sort()

    summaryInfo = {'rmse': [],
                   'mae': [],
                   'corr': [],
                   'sse': [],
                   'sae': []}
    skipMap = {'FullSet': 13,
               'SansWind': 11,
               'JustWind': 10,
               'Reflect': 8,
               'ZRBest': 0,
               'Shuffled': 13,
               'NWSZR': 0}


    resultInfo = ObtainResultInfo(dirLoc, subProj)
    PlotCorr(resultInfo['testObs'], resultInfo['modelPredicts'])
    pylab.title('Model/Obs Correlation Plot - Model: ' + subProj)
    pylab.savefig(os.sep.join([dirLoc, "CorrPlot_" + subProj + ".eps"]))
    pylab.clf()
    print "   Saved Correlation Plot..."

    PlotZR(resultInfo['reflectObs'], resultInfo['testObs'], resultInfo['modelPredicts'])
    pylab.title('Model Comparison - Z-R Plane - ' + subProj)
    pylab.savefig(os.sep.join([dirLoc, "ZRPlot_" + subProj + ".png"]))
    pylab.clf()
    print "   Save ZR Plot..."



