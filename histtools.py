import numpy
import scipy.stats	# for scipy.stats.scoreatpercentile()


# BUG: If the data array has a lot of elements with the same value,
#      then .scoreatpercentile() may report the same score for both
#      the first and third quartile, which means that the interquartile
#      range is zero.
def OptimalBinSize(vals) :
    if (len(vals) > 4) :
        binSize = 2.0*(scipy.stats.scoreatpercentile(vals, 75) 
		       - scipy.stats.scoreatpercentile(vals, 25)) * (len(vals) ** (-1.0/3.0))
    else :
        StandDev = std(Values);
        binSize = 3.49 * numpy.std(vals) * (len(vals) ** (-1.0/3.0))

    # Don't forget to re-adjust the binsize estimate to make sure the
    # size will produce equally-spaced bins for the data.
    return((max(vals) - min(vals)) / max(numpy.ceil((max(vals) - min(vals)) / binSize), 1))


def OptimalBinCount(vals) :
    binSize = OptimalBinSize(vals)
    return(max(numpy.ceil((vals.max() - vals.min()) / binSize), 1))


# BUG: The .arange() function isn't quite doing what it claims to do.
#      A temporary solution is to put the maximum value at the last
#      bin, but this will likely result in a near double-sized bin
def MakeBins(vals, binSize) :
    tempHold = numpy.arange(min(vals), max(vals), binSize)
    tempHold[-1] = max(vals)
    return(tempHold)

def Hist2d(vals1, bins1, vals2, bins2) :
    lims1 = [bins1[0:(len(bins1) - 1)], bins1[1:len(bins1)]]
    lims1[1][-1] += 100 *numpy.finfo(float).eps

    lims2 = [bins2[0:(len(bins2) - 1)], bins2[1:len(bins2)]]
    lims2[1][-1] += 100 *numpy.finfo(float).eps

    binLocs = zip([numpy.nonzero(numpy.logical_and(lims2[0] <= val, lims2[1] > val))[0][0] for val in vals2],
                  [numpy.nonzero(numpy.logical_and(lims1[0] <= val, lims1[1] > val))[0][0] for val in vals1])

    n_2d = numpy.zeros((len(lims2[0]), len(lims1[0])))

    for aCoord in binLocs : n_2d[aCoord] += 1

    return(n_2d, binLocs)

