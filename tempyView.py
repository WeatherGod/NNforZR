import numpy
import pylab
from scipy import optimize

def ZRModel(coefs, reflects) :
    return(((10.0 ** (reflects/10.0))/coefs[0]) ** (1.0/coefs[1]))


def BestZRModel(reflects, rainrate) :
    def errFun(coefs) :
        return(numpy.mean(numpy.abs(ZRModel(coefs, reflects) - rainrate)))
    return(optimize.fmin(errFun, [50, 0.5], maxiter=2000, disp=0))


def ViewPlots(numRows, numCols, years) :
    someIndex = 1
    for aYear in years :
        fullSet = numpy.loadtxt('trainingDir/subsets/'+aYear+'.csv', delimiter=',')
        pylab.subplot(numRows, numCols, someIndex)
        pylab.scatter(fullSet[:, 5], fullSet[:, 6], color = 'r', s = 1)
        finalCoefs = BestZRModel(fullSet[:, 5], fullSet[:, 6])
        pylab.scatter(fullSet[:, 5], ZRModel(finalCoefs, fullSet[:, 5]), color = 'b', s = 1)
        pylab.xlim((0, 70))
        pylab.ylim((0, 200))
        pylab.title('%s  a=%.1f b=%.3f' % (aYear, finalCoefs[0], finalCoefs[1]))
        someIndex += 1


