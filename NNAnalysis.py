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

def PerformTestTrain_zr(dataSet, iterCnt, dirLoc) :
    dataLen = dataSet.shape[0]
    trainLen = numpy.floor(dataLen * 0.6666)

    fileNames = {'training': [], 'testing': [], 'model': [], 'results': []}
    for iterIndex in range(iterCnt) :
        print "%d of %d iterations" % (iterIndex + 1, iterCnt)

        trainSelected = random.sample(range(dataLen), trainLen)
        testSelected = numpy.setxor1d(trainSelected, range(dataLen))

        trainStem = "%s/trainingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
        testStem = "%s/testingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

        modelStem = "%s/model_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
        resultsStem = "%s/results_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

        fileNames['training'].append(trainStem + '.csv')
        numpy.savetxt(trainStem + '.csv', dataSet[trainSelected, :], fmt="%6.4f", delimiter=',')

        fileNames['testing'].append(testStem + '.csv')
        numpy.savetxt(testStem + '.csv', dataSet[testSelected, :], fmt="%6.4f", delimiter=',')

        trainData = dataSet[trainSelected, :]
        testData = dataSet[testSelected, :]

        finalCoefs = ZRBest(trainData)

        # Perform the model training, saving the resulting model
        # I also want the model coefficient info.
        fileNames['model'].append(modelStem + '.txt')
        numpy.savetxt(modelStem + '.txt', finalCoefs)

        # Perform a test of the model using the available test
        # data.  The results are output to a file for loading
        # back into python for analysis
        fileNames['results'].append(resultsStem + '.csv')
        modelPredicts = ZRModel(finalCoefs, numpy.squeeze(testData[:, 0]))
        wholeSet = numpy.append(testData, 
				modelPredicts.reshape((modelPredicts.shape[0], 1)),
				axis = 1)
        #print(modelPredicts.shape, testData.shape, wholeSet.shape)
        numpy.savetxt(resultsStem + '.csv', wholeSet, delimiter=',')

    return(fileNames)



def PerformTestTrain(dataSet, iterCnt, dirLoc) :
    dataLen = dataSet.shape[0]
    trainLen = numpy.floor(dataLen * 0.6666)

    arffHeader = dirLoc + '/arffHeader.txt'
    
    mlpTrainCall = "java -Xmx128m weka.classifiers.functions.MultilayerPerceptron -L 0.05 -M 0.3 -N 3000 -H '4,2' -t %s -no-cv -v -d %s > %s"
    mlpTestCall = "java -Xmx128m weka.filters.supervised.attribute.AddClassification -serialized %s -classification -i %s -o %s -c last"

    fileNames = {'training': [], 'testing': [], 'model': [], 'results': []}
    for iterIndex in range(iterCnt) :
        print "%d of %d iterations" % (iterIndex + 1, iterCnt)

        # Save a random sample of the data for training, and the rest for testing
	trainSelected = random.sample(range(dataLen), trainLen)
        testSelected = numpy.setxor1d(trainSelected, range(dataLen))


	trainStem = "%s/trainingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
	testStem = "%s/testingData_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)

	modelStem = "%s/model_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)
	resultsStem = "%s/results_%dof%d" % (dirLoc, iterIndex + 1, iterCnt)


        fileNames['training'].append(trainStem + '.csv')
        numpy.savetxt(trainStem + '.csv', dataSet[trainSelected, :], fmt="%6.4f", delimiter=',')
	os.system('cat %s %s > %s' % (arffHeader, trainStem + '.csv', trainStem + '.arff'))
	
	fileNames['testing'].append(testStem + '.csv')
	numpy.savetxt(testStem + '.csv', dataSet[testSelected, :], fmt="%6.4f", delimiter=',')
	os.system('cat %s %s > %s' % (arffHeader, testStem + '.csv', testStem + '.arff'))

        # Perform the model training, saving the resulting model
        # I also want the model coefficient info.
        fileNames['model'].append(modelStem + '.txt')
        os.system(mlpTrainCall % (trainStem + '.arff', modelStem + '.model', modelStem + '.txt'))

        # Perform a test of the model using the available test
        # data.  The results are output to a file for loading
        # back into python for analysis
        fileNames['results'].append(resultsStem + '.csv')
        os.system(mlpTestCall % (modelStem + '.model', testStem + '.arff', resultsStem + '.csv'))

    return(fileNames)



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



os.makedirs(resultLoc + '/FullSet')
os.makedirs(resultLoc + "/SansWind")
os.makedirs(resultLoc + "/JustWind")
os.makedirs(resultLoc + "/Reflect")
#os.makedirs(resultLoc + "/Shuffled")
os.makedirs(resultLoc + "/ZRBest")



selected = f.decimate2d(dataSet[:, reflectIndex], dataSet[:, rrIndex], truncVal)
truncData = dataSet[selected, :]
numpy.savetxt(resultLoc + '/fullSet_trunc.csv', truncData, fmt='%6.4f', delimiter=',')

filenames = {}
############################################################

# performing zr best fits

reflectOnly = numpy.array([reflectIndex, rrIndex])
dirLoc = resultLoc + '/ZRBest/'
filenames['ZRBest'] = PerformTestTrain_zr(truncData[:, reflectOnly], resultCnt, dirLoc)
tempy = [numpy.loadtxt(aFileName, delimiter=',') for aFileName in filenames['ZRBest']['results']]
resultInfo = {'modelPredicts': numpy.array([aRow[:, 2] for aRow in tempy]),
              'testObs': numpy.array([aRow[:, 1] for aRow in tempy]),
              'reflectObs': numpy.array([aRow[:, 0] for aRow in tempy])}
SaveSubprojectModel(resultInfo, resultLoc, 'ZRBest')


resultInfo['modelPredicts'] = ZRModel([300, 1.4], resultInfo['reflectObs'])
SaveSubprojectModel(resultInfo, resultLoc, "NWSZR")


allVars = [tempIndex, rhIndex, pressIndex, uwndIndex, vwndIndex, reflectIndex, rrIndex]

# full set of data
dirLoc = resultLoc + '/FullSet/'
MakeARFFHeader(varNames, dirLoc + '/arffHeader.txt')
filenames['FullSet'] = PerformTestTrain(truncData, resultCnt, dirLoc)
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
sansWind = numpy.array([tempIndex, rhIndex, pressIndex, reflectIndex, rrIndex])
dirLoc = resultLoc + '/SansWind/'
MakeARFFHeader(varNames[sansWind], dirLoc + '/arffHeader.txt')
filenames['SansWind'] = PerformTestTrain(truncData[:, sansWind], resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'SansWind')
SaveSubprojectModel(resultInfo, resultLoc, 'SansWind')

# data with just wind and reflectivity
justWind = numpy.array([uwndIndex, vwndIndex, reflectIndex, rrIndex])
dirLoc = resultLoc + '/JustWind/'
MakeARFFHeader(varNames[justWind], dirLoc + '/arffHeader.txt')
filenames['JustWind'] = PerformTestTrain(truncData[:, justWind], resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'JustWind')
SaveSubprojectModel(resultInfo, resultLoc, 'JustWind')

# data without surface info
dirLoc = resultLoc + '/Reflect/'
MakeARFFHeader(varNames[reflectOnly], dirLoc + '/arffHeader.txt')
filenames['Reflect'] = PerformTestTrain(truncData[:, reflectOnly], resultCnt, dirLoc)
resultInfo = ObtainResultInfo(resultLoc, 'Reflect')
SaveSubprojectModel(resultInfo, resultLoc, 'Reflect')


##########################################################


