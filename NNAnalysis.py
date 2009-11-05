#!/usr/bin/env python


from optparse import OptionParser	# for Command-line parsing

import numpy
import filtertraining as f		# for decimate(), jitter(), decimate2d()
from ProjectAnalysis import *		# for ObtainResultInfo(), SaveSubprojectModel()


import os				# for mkdir()
import random				# for sample()


def MakeARFFHeader(varList, filename) :
    arffStream = file(filename, 'w')
    arffStream.write("@relation Z-R\n")
    arffStream.writelines(["\n@attribute " + varName + " NUMERIC" for varName in varList])
    arffStream.write("\n\n@data\n")
    arffStream.close()

def PerformTestTrain_zr(iterCnt, dirLoc) :
    
    for iterIndex in range(iterCnt) :
        print "%d of %d iterations" % (iterIndex + 1, iterCnt)

        trainStem = "%s/trainingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
        testStem = "%s/testingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

        modelStem = "%s/model_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
        resultsStem = "%s/results_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

        
        trainData = numpy.loadtxt(trainStem + '.csv', delimiter=',')
        testData = numpy.loadtxt(testStem + '.csv', delimiter=',')



        # Perform the model training, saving the resulting model
        # I also want the model coefficient info.
        finalCoefs = ZRBest(trainData)
        numpy.savetxt(modelStem + '.txt', finalCoefs)

        # Perform a test of the model using the available test
        # data.  The results are output to a file for loading
        # back into python for analysis
        modelPredicts = ZRModel(finalCoefs, numpy.squeeze(testData[:, 0]))
        wholeSet = numpy.append(testData, 
				modelPredicts.reshape((modelPredicts.shape[0], 1)),
				axis = 1)
        #print(modelPredicts.shape, testData.shape, wholeSet.shape)
        numpy.savetxt(resultsStem + '.csv', wholeSet, delimiter=',')


def PrepForTestTrain(dataSet, iterCnt, dirLoc, varNames, varIndxs) :
    dataLen = dataSet.shape[0]
    trainLen = numpy.floor(dataLen * 0.6666)

    for subProj in varIndxs.keys() :
	MakeARFFHeader(varNames[varIndxs[subProj]], dirLoc + '/' + subProj + '/arffHeader.txt')

    for iterIndex in range(iterCnt) :
        print "%d of %d iterations" % (iterIndex + 1, iterCnt)

        # Save a random sample of the data for training, and the rest for testing
        trainSelected = random.sample(range(dataLen), trainLen)
        testSelected = numpy.setxor1d(trainSelected, range(dataLen))

	trainData = dataSet[trainSelected, :]
	testData = dataSet[testSelected, :]

        for subProj in varIndxs.keys() :
            arffHeader = "%s/%s/arffHeader.txt" % (dirLoc, subProj)
            trainStem = "%s/%s/trainingData_%dof%d" % (dirLoc, subProj, iterIndex + 1, iterCnt)
            testStem = "%s/%s/testingData_%dof%d" % (dirLoc, subProj, iterIndex + 1, iterCnt)

            numpy.savetxt(trainStem + '.csv', trainData[:, varIndxs[subProj]], fmt="%6.4f", delimiter=',')
            os.system('cat %s %s > %s' % (arffHeader, trainStem + '.csv', trainStem + '.arff'))


            numpy.savetxt(testStem + '.csv', testData[:, varIndxs[subProj]], fmt="%6.4f", delimiter=',')
            os.system('cat %s %s > %s' % (arffHeader, testStem + '.csv', testStem + '.arff'))




def PerformTestTrain(iterCnt, dirLoc) :
    
    mlpTrainCall = "java -Xmx128m weka.classifiers.functions.MultilayerPerceptron -L 0.05 -M 0.3 -N 3000 -H '4,2' -t %s -no-cv -v -d %s > %s"
    mlpTestCall = "java -Xmx128m weka.filters.supervised.attribute.AddClassification -serialized %s -classification -i %s -o %s -c last"

    print "Working on ", dirLoc

    for iterIndex in range(iterCnt) :
        print "%d of %d iterations" % (iterIndex + 1, iterCnt)

	trainStem = "%s/trainingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
	testStem = "%s/testingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

	modelStem = "%s/model_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
	resultsStem = "%s/results_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)


        # Perform the model training, saving the resulting model
        # I also want the model coefficient info.
        os.system(mlpTrainCall % (trainStem + '.arff', modelStem + '.model', modelStem + '.txt'))

        # Perform a test of the model using the available test
        # data.  The results are output to a file for loading
        # back into python for analysis
        os.system(mlpTestCall % (modelStem + '.model', testStem + '.arff', resultsStem + '.csv'))


varNames = numpy.array(['temperature', 'relHumidity', 'pressure', 
                        'u_wind', 'v_wind', 'reflectivity', 'rainrate'])
rrIndex = 6		# column index for the rain rate
uwndIndex = 3		# column index for the U-wnd
vwndIndex = 4		# column index for the V-wnd
reflectIndex = 5	# column index for the Reflectivities
tempIndex = 0
rhIndex = 1
pressIndex = 2

resultLoc = './ModelProject_Retry2/'


parser = OptionParser()
parser.add_option("-n", "--count", dest="count", type="int",
		  help="Produce N results (training/testing) cycles", metavar="N")

parser.add_option("-t", "--trunc", dest="trunc", type="float",
                  help="Truncation parameter VAL", metavar="VAL")
parser.add_option("-d", "--data", dest="data", type="string",
		  help="Using training dataset FILE", metavar="FILE")
parser.add_option("-l", "--loc", dest="dir", type="string",
                  help="Project to be in DIR", metavar="DIR")

(options, args) = parser.parse_args()

if (options.data == None) :
    parser.error("Missing FILE")

dataFile = options.data
print "The dataset file is:", dataFile

if (options.dir != None) :
    resultLoc = options.dir


print "Results will be placed in the directory:", resultLoc


if (options.trunc == None) :
    parser.error("Missing truncation VAL")

truncVal = options.trunc



if (options.count == None) :
    parser.error("Missing N")

resultCnt = options.count
print "There will be %d iterations to perform." % (resultCnt)

dataSet = numpy.loadtxt(dataFile, delimiter=',')


os.makedirs(resultLoc)


selected = f.decimate2d(dataSet[:, reflectIndex], dataSet[:, rrIndex], truncVal)
truncData = dataSet[selected, :]
numpy.savetxt(resultLoc + '/fullSet_trunc.csv', truncData, fmt='%6.4f', delimiter=',')

filenames = {}
############################################################



varIndxs = {}

os.makedirs(resultLoc + '/FullSet')
varIndxs['FullSet'] = numpy.array([tempIndex, rhIndex, pressIndex, uwndIndex, vwndIndex, reflectIndex, rrIndex])

os.makedirs(resultLoc + "/SansWind")
varIndxs['SansWind'] = numpy.array([tempIndex, rhIndex, pressIndex, reflectIndex, rrIndex])
os.makedirs(resultLoc + "/JustWind")
varIndxs['JustWind'] = numpy.array([uwndIndex, vwndIndex, reflectIndex, rrIndex])
os.makedirs(resultLoc + "/Reflect")
varIndxs['Reflect'] = numpy.array([reflectIndex, rrIndex])

#os.makedirs(resultLoc + "/Shuffled")
#varIndxs['Shuffled'] = numpy.array([tempIndex, rhIndex, pressIndex, uwndIndex, vwndIndex, reflectIndex, rrIndex])

os.makedirs(resultLoc + "/ZRBest")
varIndxs['ZRBest'] = numpy.array([reflectIndex, rrIndex])

PrepForTestTrain(truncData, resultCnt, resultLoc, varNames, varIndxs)


# performing zr best fits
dirLoc = resultLoc + '/ZRBest/'
PerformTestTrain_zr(resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'ZRBest')
SaveSubprojectModel(resultInfo, resultLoc, 'ZRBest')


resultInfo['modelPredicts'] = ZRModel([300, 1.4], resultInfo['reflectObs'])
SaveSubprojectModel(resultInfo, resultLoc, 'NWSZR')




# full set of data
dirLoc = resultLoc + '/FullSet/'
PerformTestTrain(resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'FullSet')
SaveSubprojectModel(resultInfo, resultLoc, 'FullSet')


# Shuffled data
#shuffled = truncData.copy()
#for colIndex in allVars :
#    numpy.random.shuffle(shuffled[:, colIndex])

#dirLoc = resultLoc + '/Shuffled/'
#MakeARFFHeader(varNames, dirLoc + '/arffHeader.txt')
#filenames['Shuffled'] = PerformTestTrain(shuffled, resultCnt, dirLoc)
#resultInfo = ObtainResultInfo(resultLoc, 'Shuffled')
#SaveSubprojectModel(resultInfo, resultLoc, 'Shuffled')



# data without wind
dirLoc = resultLoc + '/SansWind/'
PerformTestTrain(resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'SansWind')
SaveSubprojectModel(resultInfo, resultLoc, 'SansWind')

# data with just wind and reflectivity
dirLoc = resultLoc + '/JustWind/'
PerformTestTrain(resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'JustWind')
SaveSubprojectModel(resultInfo, resultLoc, 'JustWind')

# data without surface info
dirLoc = resultLoc + '/Reflect/'
PerformTestTrain(resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'Reflect')
SaveSubprojectModel(resultInfo, resultLoc, 'Reflect')


##########################################################


