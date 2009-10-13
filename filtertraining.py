
from histtools import *		# for Hist2d()
import numpy


def WhereIs(vals, B) :
    return([numpy.nonzero(elementVal == B)[0][0] for elementVal in vals])

def decimate(vals, decimation):
    B = numpy.unique1d(vals)
    N = WhereIs(vals, B)

    # n contains the count of the number of elements for each bin
    # B contains the index location for each element in the array vals
    # NOTE: This histogram function will become obsolete soon by the numpy people.  The behavior will change.
    (n, B) = numpy.histogram(vals, B, new=False)
    return(DataTruncation(n, decimation, len(B), N))


def decimate2d(vals1, vals2, decimation):
    bins1 = MakeBins(vals1, OptimalBinSize(vals1))
    bins2 = MakeBins(vals2, OptimalBinSize(vals2))

    # n contains the count of the number of elements for each bin in a 2-d grid
    # binLocs contains the (x,y) location for each element in the parallel arrays vals1 & vals2
    (n, binLocs) = Hist2d(vals1, bins1, vals2, bins2)
    return(DataTruncation(n, decimation, len(numpy.nonzero(n)[0]), binLocs))

def DataTruncation(n, decimation, binCnt, binLocs):
    thresholds = [len(binLocs) * decimation / (binCnt * n[aCoord]) for aCoord in binLocs]
    return(numpy.random.random_sample(len(thresholds)) <= thresholds)
    

def jitter(vals):
    totVals = len(vals)
    B = numpy.unique(vals)
    N = WhereIs(vals, B)
    (n, B) = numpy.histogram(vals, B, new=False)
    fwdSpace = numpy.ediff1d(B, to_end=0.0)
    prevSpace = numpy.flipud(numpy.ediff1d(numpy.flipud(B), to_end=0.0))

    baseJit = ((fwdSpace[N] - prevSpace[N]) * numpy.random.rand(totVals)) - prevSpace[N]
    baseJit[n[N] <= 1] = 0.0

    return(vals + baseJit)

