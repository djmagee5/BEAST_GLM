import numpy
path = "C://Users//dtman5//Dropbox//Prospectus//XML_GLM//GitHub//BEAST_GLM//fakeSinglePredictors//"
states = ['Arizona','California','Colorado','Connecticut','Florida','Georgia','Idaho','Illinois','Indiana','Louisiana','Mississippi','Nebraska','Nevada','New Mexico','New York','North Dakota','Ohio','South Dakota','Texas','Utah','Wisconsin']

for j in range(5):
    outfile = open(path+"fakeSinglePredictor"+str(j)+'.csv','w')
    outfile.write('fakeSinglePredictor'+str(j)+',')
    for j in range(len(states)):
        if j == len(states)-1:
            outfile.write(states[j]+'\n')
        else:
            outfile.write(states[j]+',')
    for j in range(len(states)):
        outfile.write(states[j]+',')
        for k in range(len(states)):
            if j == k:
                outfile.write('0,')
            if k == len(states)-1:
                outfile.write(str(numpy.random.uniform())+'\n')
            else:
                outfile.write(str(numpy.random.uniform())+',')
    outfile.close()

outfile = open(path+'fakeBatchFile.txt','w')
outfile.write('location\t')
for j in range(5):
    if j == 4:
        outfile.write('fakeBatchPredictor'+str(j)+'\n')
    else:
        outfile.write('fakeBatchPredictor'+str(j)+'\t')
for k in states:
    outfile.write(k+'\t')
    for j in range(5):
        if j == 4:
            outfile.write(str(numpy.random.uniform())+'\n')
        else:
            outfile.write(str(numpy.random.uniform())+'\t')
outfile.close()
