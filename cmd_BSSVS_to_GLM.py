# takes in command line arguments instead of user input prompts
import sys
import os
import numpy
import math
import xml.etree.ElementTree as ET

tb = '\t'

# possible inputs
# python scriptName XMLfileName discreteTraitName single individualFileDirectory
# python scriptName XMLfileName discreteTraitName single individualFileDirectory -batch batchFileName
# python scriptName XMLfileName discreteTraitName batch batchFileName
# python scriptName XMLfileName discreteTraitName batch batchFileName single individualFileDirectory

def printUsageError(scriptName):
    print("ERROR: Invalid Arguments")
    print("\tUsage: ",sys.argv[0],"xmlFileName discreteTraitName single individualFileDirectory")
    print("\t       ",sys.argv[0],"xmlFileName discreteTraitName batch batchFileName")
    print("\t       ",sys.argv[0],"xmlFileName discreteTraitName batch batchFileName indiv individualFileDirectory")
    print("\t       ",sys.argv[0],"xmlFileName discreteTraitName single individualFileDirectory batch batchFileName\n")

def readCMDinputs():
    usageError = False
    print()
    if len(sys.argv) != 5 and len(sys.argv) != 7:
        printUsageError(sys.argv[0])
        usageError = True
    else:
        if len(sys.argv) == 5:
            if sys.argv[3] != 'single' and sys.argv[3] != 'batch':
                printUsageError(sys.argv[0])
                usageError = True
        else:
            if (sys.argv[3] == 'single' and sys.argv[5] == 'batch') or (sys.argv[5] == 'single' and sys.argv[3] == 'batch'):
                pass
            else:
                printUsageError(sys.argv[0])
                usageError = True
                
    if usageError:
        return 'ERROR'
    else:
        return sys.argv[1::]

# also import the a predictor file as a matrix (single predictor, like distance)
# these files need to have 
def importPredictorMatrix(file, sep, xmlDiscreteStates):  
    singlePreFile = open(file,'r')
    count = 0
    statesRow = []
    statesCol = []
    tups = []
    preName = ""
    foundError = False

    for line in singlePreFile:
        tup = line.split(sep)
        if count == 0:
            preName = tup[0].replace(' ','')
            for j in range(1,len(tup)):
                statesRow.append(tup[j].rstrip().lower().replace(' ',''))

            if len(statesRow) != len(xmlDiscreteStates):
                print("ERROR: Different number of discrete states in XML and \""+file+"\".")
                print("      "+str(len(xmlDiscreteStates)) + " in XML and " + str(len(statesRow)) + " in \""+file+"\".")
                foundError = True
                break
        else:
            statesCol.append(tup[0].rstrip().lower().replace(' ',''))
            # add in check to see if the values are real and log-transformable
            dat = []
            for k in range(1,len(tup)):
                if numpy.isnan(numpy.log(float(tup[k].rstrip()))) or numpy.isinf(numpy.log(float(tup[k].rstrip()))):
                    if tup[k] == '0':
                        dat.append('0')
                    else:
                        print("ERROR: Invalid value to log-transform.\t  Line: "+str(count+1)+"\tColumn: "+str(k))
                        foundError = True
                    
                else:
                    dat.append(numpy.log(float(tup[k].rstrip())))
            tups.append(dat)
        count +=1
    singlePreFile.close()

    # make sure the matrix is square
    if len(statesCol) != len(statesRow):
        print("ERROR: Matrix provided is not square.")
        foundError = True

    if foundError:
        print()
        return 'ERROR'
    else:
        correctDataValues = []       
        if statesRow == xmlDiscreteStates and statesCol == xmlDiscreteStates:
            correctDataValues = tups
        else:
            correctDataVals = []
            if statesRow != statesCol:
                statesSorted = []
                for j in range(len(statesRow)):
                    idx = statesCol.index(statesRow[j])
                    statesSorted.append(tups[idx])
                tups = statesSorted
                
            for j in range(len(xmlDiscreteStates)):
                idx = xmlDiscreteStates.index(statesRow[j])
                correctDataValues.append(tups[idx])

    # append them to the 'dists' array in the proper order
        pres = []
        for i in range(0,len(correctDataValues)):
            for j in range(i+1, len(correctDataValues)):
                pres.append(correctDataValues[i][j])

        for i in range(0,len(correctDataValues)):
            for k in range(i+1, len(correctDataValues)):
                pres.append(correctDataValues[k][i])

        # write them to the outfile
        predictor_matrix = []
        text = "<parameter id=\"" + preName + "\" value=\""
        for i in range(len(pres)):
            text = text + str(pres[i]) + ' '
            predictor_matrix.append(float(pres[i]))
        text = text[:len(text)-1]
        preLine = '\t\t\t\t\t' + text + '\"/>\n'

        return [preLine, predictor_matrix, preName]

# takes in the predictor data file and a delimiter (tab or comma)
# returns the trait name (first line of file, first delimited value)
# if there is only one value, 'insufficientData' error will ensue
def processGLMHeader(file,sep):
    infile = open(file,'r')
    head = infile.readline()
    preNames = []
    if sep == '\t':
        tup = head.split('\t')
        if len(tup) == 1:
            trait = "insufficientData"
        else:
            trait = tup[0].lower()
            for predictor in range(1,len(tup)):
                preNames.append((tup[predictor].rstrip()).replace(' ',''))
                
    elif sep == ',':
        tup = head.split(',')
        if len(tup) == 1:
            trait = "insufficientData"
        else:
            trait = tup[0].lower()
            for predictor in range(1,len(tup)):
                preNames.append((tup[predictor].rstrip()).replace(' ',''))
    infile.close()

    return [trait,preNames]

# called from 'getOriginDestination'
# takes in the list of predictors and directionality (origin, destination, both)
# prints them so the user can verify correctness and/or make changes
def printPredictorList(preList, directions):
    print('Current list of predictors to include from batch file:\n')
##    print("\tNum  Predictor          Direction")
##    print("\t---  ---------          ---------")
    maxPreLength = 0
    for j in preList:
        if len(j) > maxPreLength:
            maxPreLength=len(j)
    dashStr='---------'
    for j in range(len(dashStr)-8):
        dashStr+='-'
    print("\t"+format("Num","<5")+format("Predictor","<"+str(maxPreLength))+"  Direction")
    print('\t---  ---------'+dashStr+'  ---------')


    
    for j in range(len(preList)):
        print('\t' + format('('+str(j)+')',"<5") + format(preList[j],"<"+str(maxPreLength)) + '  ' + directions[j])
    print()


# uses a while loop to verify whether the user is satisfied with the list of predictors
# will continue to execute until the user has each predictor in the direction that they would like
def verifyPredictorList(currentPredictorList):
    predictorNumbers = currentPredictorList[0]
    predictorDirs    = currentPredictorList[1]
    predictorNames   = currentPredictorList[2]

    okList = False
    while okList == False:
        printPredictorList(predictorNames, predictorDirs)

        listCorrect = input("If this list is correct, enter \"y\". If you would like to modify it, enter \"n\" (y/n): ")
        while listCorrect != 'y' and listCorrect != 'n':
            listCorrect = input("Invalid selection. Is the list of predictors correct (y/n)? ").lower()
            
        if listCorrect == 'y':
            okList = True
        else:
            nextStep = input("Enter predictor that you want to remove or change the direction of (0-" + str(len(predictorNumbers)-1) + "): ")
            while nextStep not in predictorNumbers:
                nextStep = input("Invalid selection. Enter predictor that you want to remove/modify from the above list: ")
            if predictorNames[int(nextStep)] == 'Distance':
                if predictorDirs[int(nextStep)] == 'N/A':
                    print("\nDistance will be removed.")
                    predictorDirs[int(nextStep)] = '** REMOVE **'
                else:
                    print("\nDistance will be added.")
                    predictorDirs[int(nextStep)] = 'N/A'                    
            else:
                rem_mod = input("Enter (1) to remove \"" + predictorNames[int(nextStep)] + "\" or (2) to modify it (1/2): ").lower()
                while rem_mod != '1' and rem_mod != '2':
                    rem_mod = input("Invalid selection. Enter (1) to remove \"" + predictorNames[int(nextStep)] + "\" or (2) to change its direction (1/2): ").lower()
                    
                if rem_mod == '2':
                    opt = input("Enter (1) to select 'origin', (2) to select 'destination', or (3) to select 'both': ")
                    while opt != '1' and opt != '2' and opt != '3':
                        opt = input("Invalid selection. Enter (1) to select 'origin', (2) to select 'destination', or (3) to select 'both': ")
                    if opt == '1':
                        predictorDirs[int(nextStep)] = 'Origin'
                    elif opt == '2':
                        predictorDirs[int(nextStep)] = 'Destination'
                    else:
                        predictorDirs[int(nextStep)] = 'Both'
                else:
                    predictorDirs[int(nextStep)] = '** REMOVE **'

                print('\nPredictor list updated.')

    return [predictorNames, predictorDirs]

# finalizes the list of predictors that the user wishes to utilize in their GLM specification
# takes in the names of the predictors, the predictor data, the boolean for whether or not 'distance'
# is desired, and the name of the discrete trait
def getOriginDestination(preNames, data, distBoolean, discreteTraitName):
    allOptions = [[],[],[]]
    for j in range(len(preNames)):
        allOptions[0].append(str(j))
        allOptions[1].append("Both")
        allOptions[2].append(preNames[j])

    if distBoolean:
        allOptions[0].append(str(j+1))
        allOptions[1].append("N/A")
        allOptions[2].append('Distance')

    finalPredictorDirections = verifyPredictorList(allOptions)

    return [finalPredictorDirections[0], finalPredictorDirections[1]]        

# returns a list of state names from the predictor input file
# these should be the first delimited value of each row (after the first row)
# it removes any whitespace and converts all state names to lowercase for comparison
def getGLMdiscreteStateNames(file, sep):
    infile = open(file,'r')
    count = 0
    stateNames = []
    for line in infile:
        if count == 0:
            count+=1
        else:
            tup = line.split(sep)
            stateNames.append((tup[0].lower()).replace(' ',''))
            count += 1
    infile.close()
    return stateNames

# takes in the predictor data file, the delimiter, the name of the discrete trait
# the latitude/longitude index values (-1 if not detected)
# rawLat and rawLong are 'y'/'n' boolean values to indicate whether latitude or longitude
# should be kept as separate predictors, if distance is desired (specified via getCoords boolean)
def getGLMdata(file, sep, traitname, latindex, longindex, rawLat, rawLong, getCoords):
    infile = open(file,'r')
    latidx = latindex
    longidx = longindex
    # if both latitude and longitude are included, it is assumed that a 'distance'
    # predictor is desired and will be created separately
    # otherwise, it is assumed that all columns in the predictor file are desired
    # to be included in the GLM XML file
   
    data = []
    coords = []
    foundInvalid=False
    lineCount = -1
    for line in infile:
        lineCount +=1
        tup = line.split(sep)
        # ignore the first line
        if lineCount == 0:
            pass
        else:
            nums = []
            if getCoords:
                try:
                    for k in range(1,len(tup)):
                        if (k == latidx):
                            if rawLat == 'n':
                                pass
                            else:
                                nums.append(str(numpy.log(float(tup[k].rstrip()))))
                              
                        elif (k == longidx):
                            if (rawLong == 'n'):
                                pass
                            else:
                                nums.append(str(numpy.log(float(tup[k].rstrip()))))
                            
                        else:
                            nums.append(str(numpy.log(float(tup[k].rstrip()))))
                            if 'nan' == str(numpy.log(float(tup[k].rstrip()))):
                                if foundInvalid:
                                    pass
                                else:
                                    print("Invalid data point(s) in predictor file.")
                                    foundInvalid = True
                                print("\t Line: " + str(lineCount+1) + tb + 'Column: ' + str(k+1) + tb + "Value: " + tup[k].rstrip()) 
                    data.append(nums)
                    coords.append([float(tup[latidx].rstrip()),float(tup[longidx].rstrip())])
                except:
                    print("Invalid data point in predictor file.")
                    print("\t Line: " + str(lineCount+1) + tb + 'Column: ' + str(k+1) + tb + "Value: " + tup[k].rstrip())
            else:
                # convert all data entries to FLOAT and log-transform them (natural log)
                try:
                    for k in range(1,len(tup)):
                        nums.append(str(numpy.log(float(tup[k].rstrip()))))
                        if 'nan' == str(numpy.log(float(tup[k].rstrip()))):
                            if foundInvalid:
                                pass
                            else:
                                print("Invalid data point in predictor file.")
                                foundInvalid=True
                            print("\t Line: " + str(lineCount+1) + tb + 'Column: ' + str(k+1) + tb + "Value: " + tup[k].rstrip()) 
                    data.append(nums)
                except:
                    print("Invalid data point in predictor file.")
                    print("\t Line: " + str(lineCount+1) + tb + 'Column: ' + str(k+1) + tb + "Value: " + tup[k].rstrip())

    predictorsWithNegatives = []
    for j in range(len(data)):
        for k in range(len(data[j])):
            if data[j][k] == 'nan':
                if k in predictorsWithNegatives:
                    pass
                else:
                    predictorsWithNegatives.append(k)
            
    infile.close()
    return [data, coords, predictorsWithNegatives]


def verifyXMLdiscreteTrait(filename, userTraitName, rootname):
    file = open(filename,'r')
    foundUserTraitName = False
    newglmTraitName = userTraitName
    for child in rootname:

        # get the names of the discrete states for the specified discrete trait
        if child.tag == 'generalDataType':
            attribute = str(child.attrib)
            attrib = attribute[attribute.find(' \'')+2:attribute.find('.dataType')]
            if attrib.lower() == userTraitName:
                if attrib != userTraitName:
                    newglmTraitName = attrib
                for sub in child:
                    foundUserTraitName = True
    file.close()

    if foundUserTraitName:
        return newglmTraitName
    else:
        return False

                    
# uses the XML file to get the name of the discrete states specified under the 'glmTraitName' variable
# that was specified in the first value of the predictor input file
# searches the XML file for this discrete trait, and if not found it will return "noGLMtraitFound"
# which will tell the user that there is no such trait name in their XML file
# it also searches for BSSVS specifications (bitFlipOperator and poissonPrior) and indicates whether
# BSSVS has been specified in the XML file so the remaining portion of the program knows which parts to modify
def getXMLDiscreteStateNames(filename, treename, rootname, glmTraitName):
    file = open(filename,'r')
    foundGLMtraitName = False
    foundBitFlip = False
    foundPoisson = False
    discreteStateNames = []
    discreteStateNames_raw = []

    newglmTraitName = glmTraitName
    for child in rootname:

        # get the names of the discrete states for the specified discrete trait
        if child.tag == 'generalDataType':
            attribute = str(child.attrib)
            attrib = attribute[attribute.find(' \'')+2:attribute.find('.dataType')]
            if attrib.lower() == glmTraitName:
                if attrib != glmTraitName:
                    newglmTraitName = attrib
                for sub in child:
                    foundGLMtraitName = True
                    if (sub.tag).lower() == 'state':
                        attrib = str(sub.attrib)
                        statename = attrib[attrib.find(':')+3:attrib.find("\'}")]
                        discreteStateNames.append((statename.lower()).replace(' ',''))
                        discreteStateNames_raw.append(statename)

        # see if there is a bitflip operator for the specified discrete trait
        elif child.tag == 'operators':
            for subchild in child:
                if subchild.tag == 'bitFlipOperator':
                    for bitflipchild in subchild:
                        attribute = str(bitflipchild.attrib)
                        attrib = attribute[attribute.find(' \'')+2:attribute.find('.indicators')]
                        if attrib == newglmTraitName:
                            foundBitFlip = True

        # see if there is a poisson prior for the specified discrete trait
        elif child.tag == 'mcmc':
            for subchild in child:
                if subchild.tag == 'posterior':
                    for posteriorChild in subchild:
                        if posteriorChild.tag == 'prior':
                              for priorChild in posteriorChild:
                                if priorChild.tag == 'poissonPrior':
                                    for poissonChild in priorChild:
                                        attribute = str(poissonChild.attrib)
                                        attrib = attribute[attribute.find(' \'')+2:attribute.find('.nonZeroRates')]
                                        if attrib == newglmTraitName:
                                            foundPoisson = True
    file.close()
        
    # if there is a bitflip operator and poisson prior for the specified discrete trait
    # then BSSVS has been specified. mark the boolean as 'true'. otherwise, false.
    if foundPoisson and foundBitFlip:
        bssvs = True
    else:
        bssvs = False

    if foundGLMtraitName:
        return [discreteStateNames, discreteStateNames_raw, bssvs]
    else:
        return "noGLMtraitFound"
    
def writeCoeffValues(numpredictors, outfilename):
    txt = "\""
    for j in range(numpredictors):
        txt += '1 '
    outfilename.write(txt.rstrip() + "\"/>\n")

def writeOriginPredictors(count, preData, outfilename):
    origin_matrix = []
    for pre in range(len(preData)):
        pre_array = []
        text = "<parameter id=\"" + preData[pre][0] + "_origin\" value=\""
        for i in range(0,count):
            for j in range(i+1, count):
                text = text + preData[pre][1][i] + ' '
                pre_array.append(preData[pre][1][i])
        for i in range(0,count):
            for j in range(i+1, count):
                text = text + preData[pre][1][j] + ' '
                pre_array.append(preData[pre][1][j])
        outfilename.write('\t\t\t\t\t'+text[:len(text)-1] + "\"/>\n")
        origin_matrix.append(pre_array)

    return origin_matrix        
        
def writeDestinationPredictors(count, preData, outfilename):
    destination_matrix = []
    for pre in range(len(preData)):
        pre_array = []
        text = "<parameter id=\"" + preData[pre][0] + "_destination\" value=\""
        for i in range(0,count):
            for j in range(i+1, count):
                text = text + preData[pre][1][j] + ' '
                pre_array.append(preData[pre][1][i])
        for i in range(0,count):
            for j in range(i+1, count):
                text = text + preData[pre][1][j] + ' '
                pre_array.append(preData[pre][1][i])
        outfilename.write('\t\t\t\t\t'+text[:len(text)-1] + "\"/>\n")
        destination_matrix.append(pre_array)

    return destination_matrix

# calculates the great circle distance between any two coordinate points
# this program outputs the data in miles, but it will be log transformed and
# standardized anyways, so units really aren't important here
def calcDist(x1, y1, x2, y2):
    earthRad = 3959 # miles
    deltaLat = (x1-x2) * math.pi / 180
    deltaLong = (y1-y2) * math.pi / 180

    lat1 = x1 * math.pi / 180
    lat2 = x2 * math.pi / 180

    a = math.sin(deltaLat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(deltaLong/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist = c * earthRad

    return dist

# takes in a list of coordinates and a file path
# writes a matrix of pairwise distances (log transfrormed) between each state
# this will be read by writeGLMsubModel
def calculateDistances(coords,file):
    distfile = open(file,'w')
    for j in range(len(coords)):
        for k in range(len(coords)):
            if j == k:
                distfile.write('0\t')
            else:
                dist = numpy.log(calcDist(coords[j][0],coords[j][1],coords[k][0],coords[k][1]))
                distfile.write(str(dist) + tb)
        distfile.write('\n')
    distfile.close()

# reads in the distance matrix that was created 
def writeDistancePredictor(distanceFileName, outfilename):
    readDists = open(distanceFileName, 'r')

    # read in the distances and append them as floats to 'values' array
    values = []
    for line in readDists:
        tups = []
        tup = line.split(tb)
        for k in range(len(tup)-1):
            tups.append(float(tup[k].rstrip()))
        values.append(tups)
    readDists.close()

    # append them to the 'dists' array in the proper order
    dists = []
    for i in range(0,len(values)):
        for j in range(i+1, len(values)):
            dists.append(values[i][j])

    for i in range(0,len(values)):
        for k in range(i+1, len(values)):
            dists.append(values[k][i])

    # write them to the outfile
    distance_matrix = []
    text = "<parameter id=\"" + "Distance" + "\" value=\""
    for i in range(len(dists)):
        text = text + str(dists[i]) + ' '
        distance_matrix.append(str(dists[i]))
    text = text[:len(text)-1]
    outfilename.write('\t\t\t\t\t'+text + '\"/>\n')

    return distance_matrix

# write the GLM substitution model that replaces the generalSubstitutionModel for the specified discrete trait
def writeGLMsubModel(singlePreList, data, stoploop, numstates, traitname, preNames, preDirs, distBoolean, distFile, outfile, numPredictors):
    outfile.write('\n\t<!-- GLM Edit: Add GLM Substitution Model               -->\n')
    outfile.write('\t<glmSubstitutionModel id=\"' + traitname+'.model\">\n')
    outfile.write('\t\t<dataType idref=\"' + traitname+'.dataType\"/>\n')
    outfile.write('\t\t<rootFrequencies>\n')
    outfile.write('\t\t\t<frequencyModel normalize="true">\n')
    outfile.write('\t\t\t\t<dataType idref=\"' + traitname+'.dataType\"/>\n')
    outfile.write('\t\t\t\t<frequencies>\n\t\t\t\t\t<parameter dimension=\"'+str(numstates)+'\"/>\n')
    outfile.write('\t\t\t\t</frequencies>\n')
    outfile.write('\t\t\t</frequencyModel>\n')
    outfile.write('\t\t</rootFrequencies>\n')
    outfile.write('\t\t<glmModel id=\"glmModel\" family=\"logLinear\" checkIdentifiability=\"true\">\n')
    outfile.write('\t\t\t<independentVariables>\n')
    outfile.write('\t\t\t\t<parameter id=\"glmCoefficients\" value=')

    writeCoeffValues(numPredictors, outfile)

    outfile.write('\t\t\t\t<indicator>\n')
    outfile.write('\t\t\t\t\t<parameter id=\"coefIndicator\" value=')

    writeCoeffValues(numPredictors, outfile)

    outfile.write('\t\t\t\t</indicator>\n')
    outfile.write('\t\t\t\t<designMatrix id=\"designMatrix\" standardize=\"true\">\n')

    # create the designMatrix
    designMatrix = []

    # if there are single predictors to add, write them and append them to the designMatrix
    if len(singlePreList) > 0:
        for j in singlePreList:
            outfile.write(j[0])
            designMatrix.append(j[1])

    # if there are no predictors from a batch file, move on
    if len(preNames) == 0:
        pass

    # if there are, write origin/destination predictors as specified by user
    else:
        origins = []
        destinations = []
        for j in range(len(preNames)):
            stateData = []
            for k in range(numstates):
                stateData.append(data[k][j])
            if preDirs[j] == 'Both':
                origins.append([preNames[j], stateData])
                destinations.append([preNames[j], stateData])
            elif preDirs[j] == 'Origin':
                origins.append([preNames[j], stateData])
            else:
                destinations.append([preNames[j], stateData])
                
        
        origin_mat = writeOriginPredictors(stoploop, origins, outfile)
        for j in range(len(origin_mat)):
            arr = []
            for k in range(len(origin_mat[j])):
                arr.append(float(origin_mat[j][k]))
            designMatrix.append(arr)
        
        dest_mat = writeDestinationPredictors(stoploop, destinations, outfile)
        for j in range(len(dest_mat)):
            arr = []
            for k in range(len(dest_mat[j])):
                arr.append(float(dest_mat[j][k]))
            designMatrix.append(arr)

        # if there was a distance predictor from the batch file, use "distanceMatrix.txt" to write those values  
        if distBoolean:
            dist_mat = writeDistancePredictor(distFile, outfile)
            arr = []
            for k in range(len(dist_mat)):
                arr.append(float(dist_mat[k]))
            designMatrix.append(arr)

    # check the rank of all predictor data as they fall in the designMatrix
    # print an appropriate message to let the user know if designMatrix is of full rank
    countedPredictors = len(designMatrix)
    if countedPredictors != numpy.linalg.matrix_rank(designMatrix):
        print("Warning: GLM Design Matrix not of full rank.")
        print("\tPredictors =\t" + str(countedPredictors))
        print('\tRank =\t\t' +str(numpy.linalg.matrix_rank(designMatrix)))
        print("\tThese data will not execute in BEAST.")

    else:
        print("Checking rank of GLM Design Matrix.")
        print("\tPredictors =\t" + str(countedPredictors))
        print('\tRank =\t\t' +str(numpy.linalg.matrix_rank(designMatrix)))
        print("\tThese data look good and will execute in BEAST.")

    outfile.write('\t\t\t\t</designMatrix>\n')
    outfile.write('\t\t\t</independentVariables>\n')
    outfile.write('\t\t</glmModel>\n')
    outfile.write('\t</glmSubstitutionModel>\n\n')
    outfile.write('\t<!-- End GLM Edit: Add GLM Substitution Model -->\n\n')

# write the product statistic "coefficientsTimesIndicators" for the GLM trait
def writeProductStatistic(outfile):
    outfile.write('\n\t<!-- GLM Edit: Add in Product Statistic -->\n')
    outfile.write('\t<productStatistic id=\"coefficientsTimesIndicators\" elementwise=\"false\">\n')
    outfile.write('\t\t<parameter idref=\"glmCoefficients\"/>\n')
    outfile.write('\t\t<parameter idref=\"coefIndicator\"/>\n')
    outfile.write('\t</productStatistic>\n')
    outfile.write('\t<!-- End GLM Edit: Add in Product Statistic -->\n\n')

# add in the bitFlipOperator, randomWalkOperator, and mvnOperator for the GLM specification
def addGLMoperators(outfile):
    outfile.write('\n\t\t<!-- GLM Edit: Add Operators for coefIndicator and glmCoefficients -->\n')
    outfile.write('\t\t<bitFlipOperator weight=\"3\">\n')
    outfile.write('\t\t\t<parameter idref=\"coefIndicator\"/>\n')
    outfile.write('\t\t</bitFlipOperator>\n')
    outfile.write('\t\t<randomWalkOperator windowSize=\"0.5\" weight=\"1\">\n')
    outfile.write('\t\t\t<parameter idref=\"glmCoefficients\"/>\n')
    outfile.write('\t\t</randomWalkOperator>\t')
    outfile.write('\t\t<mvnOperator scaleFactor=\"1\" weight=\"5\" formXtXInverse=\"true\">\n')
    outfile.write('\t\t\t<parameter idref=\"glmCoefficients\"/>\n')
    outfile.write('\t\t\t<varMatrix>\n')
    outfile.write('\t\t\t\t<parameter idref=\"designMatrix\"/>\n')
    outfile.write('\t\t\t</varMatrix>\n')
    outfile.write('\t\t</mvnOperator>\n')	
    outfile.write('\t\t<!-- End GLM Edit: Add Operators for coefIndicator and glmCoefficients-->\n\n')

# add the binomialLikelihood, which is a 50% probability that no predictor will be included
def addBinomialLikelihood(traitname, numpredictors, outfile):
    outfile.write('\n\t\t\t\t<!-- GLM Edit: Add Binomial Likelihood -->\n')
    outfile.write('\t\t\t\t<!-- 50% probability that no predictor will be included -->\n')
    outfile.write('\t\t\t\t<binomialLikelihood>\n')
    outfile.write('\t\t\t\t\t<proportion>\n')
    outfile.write('\t\t\t\t\t\t<parameter value=\"' + str(1 - 0.5**(1 / numpredictors)) + '\"/>\n')
    outfile.write('\t\t\t\t\t</proportion>\n')
    outfile.write('\t\t\t\t\t<trials>\n')
    outfile.write('\t\t\t\t\t\t<parameter value=')

    writeCoeffValues(numpredictors, outfile)

    outfile.write('\t\t\t\t\t</trials>\n')
    outfile.write('\t\t\t\t\t<counts>\n')
    outfile.write('\t\t\t\t\t\t<parameter idref="coefIndicator"/>\n')
    outfile.write('\t\t\t\t\t</counts>\n')
    outfile.write('\t\t\t\t</binomialLikelihood>\n')
    outfile.write('\t\t\t\t<!-- End ELM Edit for Binomial Likelihood -->\n\n')

# add the logfile for the glm predictor to obtain the mean, variance, etc. of the coefficient indicators and beta coefficients
def addGLMfileLog(outfile, traitname, logging):
    outfile.write('\n\t\t<!-- GLM Edit: Add GLM File Log -->\n')
    outfile.write('\t\t<log id=\"glmFileLog\" ' + logging + '\" fileName=\"glm_logfile.' + traitname + '.model.log\">\n')
    outfile.write('\t\t\t<parameter idref=\"coefIndicator\"/>\n')
    outfile.write('\t\t\t<parameter idref=\"glmCoefficients\"/>\n')
    outfile.write('\t\t\t<productStatistic idref=\"coefficientsTimesIndicators\"/>\n')
    outfile.write('\t\t\t<glmModel idref=\"glmModel\"/>\n')
    outfile.write('\t\t\t<parameter idref=\"' + traitname + '.clock.rate\"/>\n')
    outfile.write('\t\t</log>\n')
    outfile.write('\t\t<!-- End GLM Edit: Add GLM File Log -->\n\n')

def getTotalNumberOfPredictors(preDirections, distBool, singlePreList):
    tot = len(singlePreList)

    for j in range(len(preDirections)):
        if preDirections[j] == 'Both':
            tot += 2
        else:
            tot += 1

    if distBool:
        tot += 1

    return tot

# the big function that creates the new XML file
# takes in the input and output file paths as well as all other relevant data from the remainder of the program
def createGLM_XML(readFromXML, writeToXML, BSSVS_specified, dataForPredictors, namesOfPredictors, directionsOfPredictors, loopToStop, distanceBoolean, distanceFileName, discreteStateNames, discreteTraitName, singlePredictorsList):

##    print(namesOfPredictors,len(namesOfPredictors))
##    print(len(dataForPredictors),len(dataForPredictors[0]))
##    print(dataForPredictors)

    # createGLM_XML(inputXMLfilePath, outputXMLfilePath, bssvs_specified, [], [], [], len(XMLdiscreteStateNames), False, "distanceMatrix.txt", XMLdiscreteStateNames, traitName, singlePres)


    # open the current BSSVS-specified XML file
    # open a new XML file to replace the BSSVS specificaiton with a GLM
    XMLinput = open(readFromXML,'r')
    XMLoutput = open(writeToXML,'w')

    # figure out exactly how many predictors there are using the directions and the distance boolean
    totalNumberOfPredictors = getTotalNumberOfPredictors(directionsOfPredictors, distanceBoolean, singlePredictorsList)

    # set several booleans to control the XML file processing
    addSourceCredit = False
    replaceGeneralSubModel = False
    commentOutScaleOp      = False

    if BSSVS_specified:
        commentOutBitFlipOp    = False
        commentOutPoissonPrior = False
        removeLogNonZeroRates  = False
    else:
        commentOutBitFlipOp    = True
        commentOutPoissonPrior = True
        removeLogNonZeroRates  = True

    commentOutUniformCachedPriors = False
    
    changeLogFileName      = False
    removeLogRates         = False
    removeBSSVSlog         = False

    for line in XMLinput:
        if addSourceCredit == False:
            if (line.find('<beast>') >= 0):
                XMLoutput.write('\n<!-- Supplemented by GLM Parsing Code                 -->\n')
                XMLoutput.write('<!-- \t   Written by Dan Magee                        -->\n')
                XMLoutput.write('<!-- \t   Ph.D. Candidate                             -->\n')
                XMLoutput.write('<!-- \t   Department of Biomedical Informatics        -->\n')
                XMLoutput.write('<!-- \t   Biodesign Center for Environmental Security -->\n')
                XMLoutput.write('<!-- \t   Arizona State University                    -->\n')
                XMLoutput.write('<!-- \t   djmagee <<at>> asu <<dot>> edu              -->\n\n')
                XMLoutput.write(line)
                addSourceCredit = True
            else:
                XMLoutput.write(line)
            
        # Search for the general substitution model of the discrete trait to be 
        elif replaceGeneralSubModel == False:
            if (line.find('generalSubstitutionModel') >= 0) and (line.find(discreteTraitName+'.model') >= 0):

                XMLoutput.write('\n\t<!-- GLM EDIT: Swap generalSubstitutionModel with glmSubstitutionModel -->\n')
                XMLoutput.write('\t<!--\n')
                XMLoutput.write(line)
                nextLine = XMLinput.readline()

        
                while nextLine.find('<siteModel id=\"' + discreteTraitName + '.siteModel\">') < 0:
                    if nextLine.find('<!--') >= 0:
                        pass
                    else:
                        XMLoutput.write(nextLine)
                    nextLine = XMLinput.readline()
                siteModelLine = nextLine
                
                XMLoutput.write('\t-->\n')
                XMLoutput.write('\t<!-- End GLM EDIT: Swap generalSubstitutionModel with glmSubstitutionModel -->\n')                

                writeGLMsubModel(singlePredictorsList, dataForPredictors, loopToStop, len(discreteStateNames), discreteTraitName, namesOfPredictors, directionsOfPredictors, distanceBoolean, distanceFileName, XMLoutput, totalNumberOfPredictors)
                    
                writeProductStatistic(XMLoutput)
                XMLoutput.write(siteModelLine)
                
                replaceGeneralSubModel = True
            else:
                XMLoutput.write(line)

        elif commentOutScaleOp == False:
            
            if (line.find('<scaleOperator') >= 0):
                
                nextLine = XMLinput.readline()
                if nextLine.find(discreteTraitName+'.rates') >= 0:
                    
                    XMLoutput.write('\n\t\t<!-- GLM Edit: Remove scaleOperator for ' + discreteTraitName + ' -->\n')
                    XMLoutput.write('\t\t<!--\n')
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)

                    nextLine = XMLinput.readline()
                    while nextLine.find('</scaleOperator>') < 0:
                        XMLoutput.write(nextLine)
                        nextLine = XMLinput.readline()
                    XMLoutput.write(nextLine)
                    XMLoutput.write('\t\t-->\n')
                    XMLoutput.write('\t\t<!-- End GLM Edit: Remove scaleOperator for ' + discreteTraitName + ' -->\n')
                    commentOutScaleOp = True

                else:
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine) 
                
            else:
                XMLoutput.write(line)

        elif commentOutBitFlipOp == False:
            
            if (line.find('<bitFlipOperator') >= 0):
                nextLine = XMLinput.readline()
                if nextLine.find(discreteTraitName+'.indicators') >= 0:
                    
                    XMLoutput.write('\n\t\t<!-- GLM Edit: Remove bitFlipOperator for ' + discreteTraitName + ' -->\n')
                    XMLoutput.write('\t\t<!--\n')
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)

                    nextLine = XMLinput.readline()
                    while nextLine.find('</bitFlipOperator>') < 0:
                        XMLoutput.write(nextLine)
                        nextLine = XMLinput.readline()
                    XMLoutput.write(nextLine)
                    XMLoutput.write('\t\t-->\n')
                    XMLoutput.write('\t\t<!-- End GLM Edit: Remove bitFlipOperator for ' + discreteTraitName + ' -->\n')
                    addGLMoperators(XMLoutput)
                    commentOutBitFlipOp = True

                else:
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine) 
                
            else:
                XMLoutput.write(line)
                
        elif commentOutPoissonPrior == False:
            if (line.find('<poissonPrior') >= 0):
                nextLine = XMLinput.readline()
                if nextLine.find(discreteTraitName + '.nonZeroRates') >= 0:
                    
                    XMLoutput.write('\n\t\t\t\t<!-- GLM Edit: Remove Poisson Prior for BSSVS of ' + discreteTraitName + ' -->\n')
                    XMLoutput.write('\t\t\t\t<!--\n')
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)

                    nextLine = XMLinput.readline()
                    while nextLine.find('</poissonPrior>') < 0:
                            XMLoutput.write(nextLine)
                            nextLine = XMLinput.readline()
                    XMLoutput.write(nextLine)
                    XMLoutput.write('\t\t\t\t-->\n')
                    XMLoutput.write('\t\t\t\t<!-- END GLM Edit: Remove Poisson Prior for BSSVS of ' + discreteTraitName + ' -->\n')

                    addBinomialLikelihood(discreteTraitName, totalNumberOfPredictors, XMLoutput)
                    commentOutPoissonPrior = True
                    
                else:
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)

            else:
                XMLoutput.write(line)
                    
        elif commentOutUniformCachedPriors == False:
            if line.find('<uniformPrior') >= 0:
                nextLine = XMLinput.readline()
                if nextLine.find(discreteTraitName + '.frequencies') >= 0:
                    
                    XMLoutput.write('\n\t\t\t\t<!-- GLM Edit: Remove uniform prior on frequencies and cached prior on rates -->\n')
                    XMLoutput.write('\t\t\t\t<!--\n')
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)
                    
                    nextLine = XMLinput.readline()
                    while nextLine.find('</cachedPrior>') < 0:
                        XMLoutput.write(nextLine)
                        nextLine = XMLinput.readline()
                    XMLoutput.write(nextLine)
                    XMLoutput.write('\t\t\t\t-->\n')
                    XMLoutput.write('\t\t\t\t<!-- End GLM Edit: Remove uniform prior on frequencies and cached prior on rates -->\n\n')

                    XMLoutput.write('\t\t\t\t<!-- GLM Edit: Add normal prior on GLM coefficients -->\n')
                    XMLoutput.write('\t\t\t\t<normalPrior mean=\"0\" stdev=\"2\">\n')
                    XMLoutput.write('\t\t\t\t\t<parameter idref=\"glmCoefficients\"/>\n')
                    XMLoutput.write('\t\t\t\t</normalPrior>\n')
                    XMLoutput.write('\t\t\t\t<!-- End GLM Edit: Add normal prior on GLM coefficients -->\n\n')

                    commentOutUniformCachedPriors = True                    

                else:
                    XMLoutput.write(line)
                    XMLoutput.write(nextLine)

            else:
                XMLoutput.write(line)    

        elif removeLogNonZeroRates == False:
            if line.find('<column label=\"' + discreteTraitName + '.nonZeroRates') >= 0:
                XMLoutput.write('\n\t\t\t<!-- GLM Edit: Remove nonZeroRates from log -->\n')
                XMLoutput.write('\t\t\t<!--\n')
                XMLoutput.write(line)

                nextLine = XMLinput.readline()
                while nextLine.find('</column>') < 0:
                    XMLoutput.write(nextLine)
                    nextLine = XMLinput.readline()
                XMLoutput.write(nextLine)
                XMLoutput.write('\t\t\t-->\n')
                XMLoutput.write('\t\t\t<!-- End GLM Edit: Remove nonZeroRates from log-->\n\n')
                
                removeLogNonZeroRates = True

            else:
                XMLoutput.write(line)

        elif changeLogFileName == False:
            if line.find('<log id=\"fileLog\"') >= 0:
                newLine = line[:line.find('.log')] + '_GLMedits_' + discreteTraitName + line[line.find('.log')::]
                XMLoutput.write(newLine)
                changeLogFileName = True
                
            else:
                XMLoutput.write(line)
                
        elif removeLogRates == False:
            if line.find('<parameter idref=\"' + discreteTraitName + '.rates\"/>') >= 0:
                XMLoutput.write('\n\t\t\t<!-- GLM Edit: Remove BSSVS Rates, Indicators, nonZeroRates -->\n')
                XMLoutput.write('\t\t\t<!--\n')
                XMLoutput.write(line)

                if BSSVS_specified:
                    nextLine = XMLinput.readline()
                    while (nextLine.find(discreteTraitName + '.indicators') >= 0) or (nextLine.find(discreteTraitName + '.nonZeroRates') >= 0):
                        XMLoutput.write(nextLine)
                        nextLine = XMLinput.readline()

                    XMLoutput.write('\t\t\t-->\n')
                    XMLoutput.write('\t\t\t<!-- End GLM Edit: Remove BSSVS Rates, Indicators, nonZeroRates -->\n\n')                    
                    XMLoutput.write(nextLine)

                else:
                    XMLoutput.write('\t\t\t-->\n')
                    XMLoutput.write('\t\t\t<!-- End GLM Edit: Remove BSSVS Rates, Indicators, nonZeroRates -->\n\n')

                removeLogRates = True

            else:
                XMLoutput.write(line)

        elif removeBSSVSlog == False:
            if (line.find('<log id=') >= 0) and (line.find('logEvery=') >= 0) and (line.find(discreteTraitName+'.rates.log') >= 0):
                logEvery = line[line.find('logEvery'):line.find('\"',line.find('logEvery')+10)]

                XMLoutput.write('\n\t\t<!-- GLM Edit: Remove BSSVS file log -->\n')
                XMLoutput.write('\t\t<!--\n')
                XMLoutput.write(line)
                nextLine = XMLinput.readline()

                while (nextLine.find('</log>') < 0):
                    XMLoutput.write(nextLine)
                    nextLine = XMLinput.readline()
                XMLoutput.write(nextLine)
                
                XMLoutput.write('\t\t-->\n\t\t<!--End GLM Edit: Remove BSSVS file log-->\n\n')

                addGLMfileLog(XMLoutput, discreteTraitName, logEvery)

                removeBSSVSlog = True

            else:
                XMLoutput.write(line)

        
        elif (line.find('.log') >= 0) and (line.find('fileName=') >= 0):
            newline = line[:line.find('.log')] + '_GLMedits_' + discreteTraitName + line[line.find('.log')::]
            XMLoutput.write(newline)
                
        elif (line.find('.trees') >= 0) and (line.find('fileName=') >= 0):
            newline = line[:line.find('.trees')] + '_GLMedits_' + discreteTraitName + line[line.find('.trees')::]
            XMLoutput.write(newline)
            
        elif (line.find('operatorAnalysis') >= 0) and (line.find('.ops') >= 0):
            newline = line[:line.find('.ops')] + '_GLMedits_' + discreteTraitName + line[line.find('.ops')::]

            XMLoutput.write(line)
        else:
            XMLoutput.write(line)

    XMLinput.close()
    XMLoutput.close()

# FOR THE USER PROMPT VERSION
##def getXMLinputFile():
##    xmlInputFileName = input("Enter XML file to convert from BSSVS to GLM: ")
##    xmlInput = open(xmlInputFileName,'r')
##    tree = ET.parse(xmlInput)
##    root = tree.getroot()
##    xmlInput.close()
##
##    return [xmlInputFileName, tree, root]
##
##def getPredictorInputFile():
##    preInputFileName = input("\nEnter .txt or .csv file of predictor data: ")
##    glmInput = open(preInputFileName, 'r')
##    glmInput.close()
##
##    if (preInputFileName[len(preInputFileName)-4::].rstrip().lower() == '.csv'):
##        delimiter = ','
##    else:
##        delimiter = '\t'
##
##    glmInput = open(preInputFileName, 'r')
##    tup=glmInput.readline().rstrip().split(delimiter)
##    traitName = tup[0].lower().rstrip()
##    glmInput.close()
## 
##    return [preInputFileName, delimiter]
##
##def getDiscreteTraitName():
##    userDiscreteTraitName = input("Enter name of discrete trait to model as GLM: ")
##
##    return userDiscreteTraitName.rstrip()

def getXMLinputFile(inputFile):
    xmlInput = open(inputFile,'r')
    tree = ET.parse(xmlInput)
    root = tree.getroot()
    xmlInput.close()

    return [tree, root]

def getPredictorInputFileDelim(preInputFileName):
    glmInput = open(preInputFileName, 'r')
    glmInput.close()

    if (preInputFileName[len(preInputFileName)-4::].rstrip().lower() == '.csv'):
        delimiter = ','
    else:
        delimiter = '\t'

    glmInput = open(preInputFileName, 'r')
    tup=glmInput.readline().rstrip().split(delimiter)
    glmInput.close()
 
    return delimiter


# reads predictor data from a batch file
# searches for 'lat/long' like predictors to include distance directly
def getPreDataFromBatch(batchFile,batchPreNames,delim,traitName):
    # find out if there are 'lat' and 'long' predictors for distance
    latitude = -1
    longitude = -1
    for k in range(len(batchPreNames)):
        if batchPreNames[k].lower() == 'lat' or batchPreNames[k].lower() == 'latitude':
            latitude = k+1
            latName = batchPreNames[k]
            break
    for k in range(len(batchPreNames)):
        if batchPreNames[k].lower() == 'long' or batchPreNames[k].lower() == 'longitude':
            longitude = k+1
            longName = batchPreNames[k]
            break
   
    # if it appears that there are coordinates, ask the user if they'd like to include a 'distance' predictor
    # set 'includeDistance' to False by default
    includeDistance = False
    if (latitude >= 0) and (longitude >= 0):
        print("Predictors \"" + latName + "\" and \"" + longName + "\" in "+batchFile+ " look like coordinates.")
        wantDistance = input("Would you like to create a \"distance\" predictor (y/n)? ").lower()
        while (wantDistance != 'y') and (wantDistance != 'n'):
            wantDistance = input("\tPlease try again. Enter 'y' to create \"Distance\" predictor or 'n' to pass: ").lower()

        # if they want distance, take the 'latitude' and 'longitude' predictors and create a list of coordinates
        # this will be used to create a distance matrix that can be read and converted into a 'distance' predictor
        if wantDistance == 'y':
            # change the boolean 'includeDistance'
            includeDistance = True
            glmCoordinatesSorted = []
                
            print('\t"Distance" predictor will be created.\n')
            keepLatRaw = input('Would you like to keep predictor "' + latName + '" as a separate predictor (y/n)? ').lower()
            while (keepLatRaw != 'y') and (keepLatRaw != 'n'):
                keepLatRaw = input("\tPlease try again. Enter \"y\" to keep \"" + latName + "\" as a predictor or \"n\" to pass: ").lower()

            if keepLatRaw == 'y':
                print('\t' + latName + ' predictor will be created.\n')
            else:
                print('\t' + latName + ' predictor will NOT be created.\n')
                batchPreNames.remove(latName)

            keepLongRaw = input('Would you like to keep predictor "' + longName + '" as a separate predictor (y/n)? ').lower()
            while (keepLongRaw != 'y') and (keepLongRaw != 'n'):
                keepLongRaw = input("\tPlease try again. Enter \"y\" to keep \"" + longName + "\" as a predictor or \"n\" to pass: ").lower()             

            if keepLongRaw == 'y':
                print('\t' + longName + ' predictor will be created.\n')
            else:
                print('\t' + longName + ' predictor will NOT be created.\n')
                batchPreNames.remove(longName)

            # get the predictor data from the GLM file
            # send along the coordinates of latitude/longitude in the data file along with the y/n to keep coordinate(s) in raw form
            glmFileData = getGLMdata(batchFile, delim, traitName, latitude, longitude, keepLatRaw, keepLongRaw, includeDistance)

        else:
            print('\t"Distance" predictor will NOT be created.')
            print("\tPredictors " + latName + " and " + longName + " will be used in raw form.\n")
            glmFileData = getGLMdata(batchFile, delim, traitName, latitude, longitude, 'y', 'y', includeDistance)

    else:
        glmFileData = getGLMdata(batchFile, delim, traitName, -1, -1, 'n', 'n', includeDistance)

    # getGLMdata returns [data, coords, predictorsWithNegatives]
    batchPredictorData = glmFileData[0]
    batchCoordinates = glmFileData[1]
    batchNegPredictors = glmFileData[2]

    return [batchPreNames, batchPredictorData, batchCoordinates, batchNegPredictors, includeDistance]

def getAllPredictorData(discreteTraitName,XMLdiscreteStates,XMLdiscreteStatesRaw,batchPreFile,indivPreDir,inputXMLfileName):
    singlePredictors = []
    batchPredictorNames = []
    predictorFileError = False
    uploadedBatch = False
    uploadedSingle = False
    gotBatchData = False

    # if there was a batch file uploaded, get its predictor data
    if batchPreFile == False:
        pass
    else:
        # get the delimiter from the batch file (i.e. look for '.csv' file for comma or '.txt' for tab delimited
        delim = getPredictorInputFileDelim(batchPreFile)
        glmFileHeader = processGLMHeader(batchPreFile,delim)
        batchPredictorNames = glmFileHeader[1]

        # if there are no predictor names...
        if glmFileHeader[0].lower() == 'insufficentData':
            print("ERROR: There are no predictor names in "+userPredictorInput[0])
            predictorFileError = True
        # if there are predictor names...
        else:
            # get the discrete state names from the batch file
            batchDiscreteStateNames = getGLMdiscreteStateNames(batchPreFile, delim)

            # if there are different numbers of discrete states
            if len(XMLdiscreteStates) != len(batchDiscreteStateNames):
                predictorFileError = True
                print("ERROR: XML input and predictor input have different number of discrete states.")
                print("\tXML States:\t\t" + str(len(XMLdiscreteStates)))
                print("\tPredictor States:\t" + str(len(batchDiscreteStateNames)))
                print("New XML file for GLM specication not created.")

            # otherwise, try to match 1-to-1 from batch file to XML input
            else:
                unmatchedStateNames = []
                for j in range(len(XMLdiscreteStates)):
                    foundstate = False
                    for k in range(len(batchDiscreteStateNames)):
                        if XMLdiscreteStates[j] == batchDiscreteStateNames[k]:
                            foundstate = True
                            break
                    if foundstate == False:
                        unmatchedStateNames.append(XMLdiscreteStatesRaw[j])

                # if there are any unmatched state names in the XML file, print them and exit
                if len(unmatchedStateNames) > 0:
                    predictorFileError = True
                    print("ERROR: XML contains discrete state names unmatched in predictor input file.\n")
                    for j in range(len(unmatchedStateNames)):
                        print("\tState Name: " + unmatchedStateNames[j])
                        print("\nPlease verify that discrete state names from \"" + inputXMLfileName + "\" match the predictor names from \"" + batchPreFile + "\".")

                else:
                    # get the predictors from the batch file
                    # returns [batchPreNames, batchPredictorData, batchCoordinates, batchNegPredictors]
                    processBatchPredictorData = getPreDataFromBatch(batchPreFile,batchPredictorNames,delim,discreteTraitName)
                    batchPredictorNames = processBatchPredictorData[0]
                    batchPredictorData  = processBatchPredictorData[1]
                    batchCoordinates    = processBatchPredictorData[2]
                    batchNegPredictors  = processBatchPredictorData[3]
                    distanceBoolean     = processBatchPredictorData[4]

                    # from the batch file, see if there are any predictors with negative values
                    negativeDataPredictorNames = []
                    if len(batchNegPredictors) == 0:
                        preDirs = getOriginDestination(batchPredictorNames, batchPredictorData, distanceBoolean, discreteTraitName)      
                        gotBatchData = True
                    # if there are, list the predictors that do
                    elif len(batchNegPredictors) == len(batchPredictorNames):
                        predictorFileError = True
                        print('\nERROR: All predictors in '+batchPreFile+' are negative/invalid. GLM-ready XML file not created.')
                    else:
                        for j in range(len(batchNegPredictors)):
                            negativeDataPredictorNames.append(batchPredictorNames[batchNegPredictors[j]])

                        for j in negativeDataPredictorNames:
                            idx = batchPredictorNames.index(j)
                            batchPredictorNames.pop(idx)
                            
                            for k in range(len(batchPredictorData)):
                                batchPredictorData[k].pop(idx)                            

                        print("\nBatch file contains the following predictor(s) with negative data values that will not be included in the new XML:")
                        for j in negativeDataPredictorNames:
                            print('\t'+j)
                        print()
                        preDirs = getOriginDestination(batchPredictorNames, batchPredictorData, distanceBoolean, discreteTraitName)
                        gotBatchData = True

    # if there was no individual predictor directory                  
    if indivPreDir == False:
        pass
    else:
        for filename in os.listdir(indivPreDir):
            delim = getPredictorInputFileDelim(indivPreDir+'\\'+filename)
            singlePre = importPredictorMatrix(indivPreDir+'\\'+filename, delim, XMLdiscreteStates)
            if singlePre == 'ERROR':
                predictorFileError = True
                break
            else:
                singlePredictors.append(singlePre)

    if predictorFileError:
        return 'ERROR'
    elif gotBatchData:
        return [singlePredictors,batchPredictorNames,batchPredictorData,batchCoordinates,batchDiscreteStateNames,distanceBoolean,preDirs]
    else:
        return [singlePredictors]

def main():

    # python scriptName XMLfileName discreteTraitName -indiv individualFileDirectory
    # python scriptName XMLfileName discreteTraitName -indiv individualFileDirectory -batch batchFileName
    # python scriptName XMLfileName discreteTraitName -batch batchFileName
    # python scriptName XMLfileName discreteTraitName -batch batchFileName -indiv individualFileDirectory
    args = readCMDinputs()

    if args == 'ERROR':
        print("Please see \"README.md\" for correct usage of this script.")
    else:
        userInputFile = args[0]
        userTraitName = args[1]

        # if there is a batchFile, get its directory
        if args[2] == 'batch' and len(args) == 4:
            batchFilePath = args[3]        
            indivFilesDir = False
        elif args[2] == 'single' and len(args) == 4:
            indivFilesDir = args[3]
            batchFilePath = False
        elif args[2] == 'batch' and len(args) == 6:
            batchFilePath = args[3]
            indivFilesDir = args[5]
        elif args[2] == 'single' and len(args) == 6:
            batchFilePath = args[5]
            indivFilesDir = args[3]
          
        userXMLinput = getXMLinputFile(userInputFile)
        tree = userXMLinput[0]
        root = userXMLinput[1]    

        xmlInput = open(userInputFile,'r')
        
        inputXMLfilePath = userInputFile
        outputXMLfilePath = userInputFile[:len(userInputFile)-4] + '_GLMedits.xml'

        # check to see if the user's discrete trait is in the supplied XML
        foundDiscreteTrait = verifyXMLdiscreteTrait(inputXMLfilePath, userTraitName, root)

        # if the XML doesn't have that trait, quit
        if foundDiscreteTrait == False:
            print("ERROR: Discrete trait \""+userTraitName+"\" not found in " + inputXMLfilePath+".")

        # if it does, proceed
        else:
            traitName = foundDiscreteTrait

            # get the discrete state names
            # returns [discreteStateNames, discreteStateNames_raw, bssvs]
            XMLdiscreteData = getXMLDiscreteStateNames(inputXMLfilePath, tree, root, traitName)
            XMLdiscreteStateNames = XMLdiscreteData[0]
            bssvs_specified = XMLdiscreteData[2]

            # get all of the predictor data files from the user
            # return [singlePredictors,batchPredictorNames,batchFilePath]
            uploadedPreFiles = getAllPredictorData(traitName, XMLdiscreteStateNames, XMLdiscreteData[1], batchFilePath, indivFilesDir, inputXMLfilePath)

            # if there was an error in the uploaded predictor file(s) then print a message and kill the program
            if uploadedPreFiles == "ERROR":
                print("New GLM-ready XML file not created. Check your predictor file(s) for the specified error.")

            else:
                # only single predictor files were uploaded
                # returned [singlePreData]
                if len(uploadedPreFiles) == 1:
                    # add in createGLMXMLhere for just a single predictor file
                    singlePres = uploadedPreFiles[0]
                    createGLM_XML(inputXMLfilePath, outputXMLfilePath, bssvs_specified, [], [], [], len(XMLdiscreteStateNames), False, "distanceMatrix.txt", XMLdiscreteStateNames, traitName, singlePres)
                    print('\nDone. New XML file \"' + outputXMLfilePath + '\" created to model discrete trait \"' + traitName + '\" as a log-linear GLM has been created.')


                else:
                    # a batch file was uploaded (and possibly single predictor files)
                    # returned [singlePredictors,batchPredictorNames,batchPredictorData,batchCoordinates,batchNegPredictors,batchDiscreteStateNames]
                    singlePres          = uploadedPreFiles[0]
                    batchPreNames       = uploadedPreFiles[1]
                    batchPreData        = uploadedPreFiles[2]
                    batchCoords         = uploadedPreFiles[3]
                    batchStateNames     = uploadedPreFiles[4]
                    includeDistance     = uploadedPreFiles[5]
                    predictorDirections = uploadedPreFiles[6]

                    newPreNames = predictorDirections[0]
                    preDirections = predictorDirections[1]
                                     
                    # create new arrays of predictor data for coordinates (if desired) and other predictors
                    batchPredictorDataSorted = [] 
                    batchCoordsSorted = []

                    # check to see if discrete states are in the correct order in the GLM data
                    # sort them into the same order as the XML file if they are not
                    for k in range(len(XMLdiscreteStateNames)):
                        XMLstate = XMLdiscreteStateNames[k]
                        for j in range(len(batchStateNames)):
                            if batchStateNames[j] == XMLstate:
                                batchPredictorDataSorted.append(batchPreData[j])
                                if includeDistance:
                                    batchCoordsSorted.append(batchCoords[j])

                    # if the user wanted distance...
                    if includeDistance:
                        idx = newPreNames.index('Distance')

                        # if the name 'distance' exists in the predictor list and it was not maked for removal
                        # during the directionality editing, create a matrix of great circle distances "distanceMatrix.txt"
                        if idx >= 0 and preDirections[idx] != '** REMOVE **':
                            calculateDistances(batchCoordsSorted, "distanceMatrix.txt")
                            newPreNames.pop(idx)
                            preDirections.pop(idx)

                        # if they elected to remove it during directional editing, set the boolean false
                        else:
                            includeDistance = False

                    predictorsToStandardize = 0
                    predictorsToRemove = []
                    for j in range(len(batchPreNames)):
                        if preDirections[j] == '** REMOVE **':
                            predictorsToRemove.append(batchPreNames[j])
                        else:
                            predictorsToStandardize += 1

                    for j in range(len(predictorsToRemove)):
                        idx = batchPreNames.index(predictorsToRemove[j])
                        batchPreNames.pop(idx)
                        preDirections.pop(idx)
                        for k in range(len(batchPredictorDataSorted)):
                            batchPredictorDataSorted[k].pop(idx)

                    createGLM_XML(inputXMLfilePath, outputXMLfilePath, bssvs_specified, batchPredictorDataSorted, batchPreNames, preDirections, len(XMLdiscreteStateNames), includeDistance, "distanceMatrix.txt", XMLdiscreteStateNames, traitName, singlePres)
                    print('\nDone. New XML file \"' + outputXMLfilePath + '\" created to model discrete trait \"' + traitName + '\" as a log-linear GLM has been created.')


if __name__ == "__main__":
    main()

