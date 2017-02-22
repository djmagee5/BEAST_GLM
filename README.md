***************************
***************************
**   create_glm_xml.py   **
***************************
***************************

Prepared by: 	Daniel Magee
		Arizona State University
		Department of Biomedical Informatics
		djmagee@asu.edu
		
Last Updated: 	16 November 2016

This document describes the usage of the Python 3.4.3 script "BSSVS_to_GLM.py".
The general use of the script is to identify a discrete trait contained within a 
BEAUti-generated XML file and model the trait using the generalized linear model
(GLM) framework [Faria (2013), Lemey (2014)]. A tutorial for the manual version
of the required changes is available for download from following link:

https://perswww.kuleuven.be/~u0036765/crashcourse/BEAST_files/discretePhylogeography_RABV_1.8.1_1.zip


Program Summary
------------------
The program takes in a BEAST-ready XML file that models some discrete trait, and also file(s) (batch file and/or individual file(s)) 
of predictor data to model that discrete trait. The program then converts the XML file to model the discrete trait as a 
log-linear GLM of the specified predictors. It will allow users to visualize the list of predictors and decide 
whether they should be modeled from both <trait> of origin and <trait> of destination (by default), or one particular direction.
If two of the predictors in a batch predictor input file appear to be coordinates, the program will ask if a 
"distance" predictor is desired. If not, the predictors will be used in raw form. Individual predictors may also be uploaded
as a square matrix of the discrete states, perhaps in cases where exact values are known for each transition and the matrix
is asymmetric. Predictor files of this type must be contained in a single directory. The program will process each of the files
in the directory individually. All predictors (whether from the batch file or individual files) will be added to a 'design matrix'.
BEAST will not execute XML files with the GLM specification if the design matrix is not of full rank. Therefore, this program 
will check the rank of the GLM design matrix to ensure that it is of full rank. This value will be echoed to the user along with a 
message of whether or not the predictor data will (likely) cause a BEAST crash. The program also exports a .txt file listing the 
predictors that were written to the new XML file. This file can be used to reference the BEAST output (via Tracer) which 
only annotates predictors as 'coefIndicator<number>' and 'glmCoefficients<number>', respectively.


Program Requirements
--------------------
This program requires a BEAST-ready XML file, likely created by BEAUti. This script will modify BEAST XML files through 
BEAST version 1.8.4. The latest releases are available from the following link: 
https://github.com/beast-dev/beast-mcmc/releases

The program BSSVS_to_GLM.py is written in Python v3.4.3, available from:
https://www.python.org/downloads/release/python-343/

The built-in 'xml' and 'math' packages are used. Also required is the 'numpy' package. 
Documentation and download instructions for 'numpy' can be found at the following link:	
http://docs.scipy.org/doc/numpy-1.10.1/user/install.html


Command Line Execution
----------------------
General use:
	$ python create_glm_xml.py <xmlFilePath> <discreteTraitName> single <singlePredictorDir> batch <batchFilePath>

<xmlFilePath>			A BEAST-ready XML document that specifies some discrete trait.
<discreteTraitName>		The name of the discrete trait from the XML file that you wish to transform in to a GLM.
single				Indicates that you have at least one individual predictor matrix file.
<singlePredictorDirectory>	Name of directory that contains ONLY individual predictor matrices.
batch				Indicates that you have a file of batch predictors.
<batchFilePath>			The name of the batch predictor file.

You may specify that only individual predictor files used, only a batch file is used, or both are used. It is REQUIRED that if you wish
to upload individual predictor files that they are all contained in a single directory. Each file in this directory must be an individual
predictor file.

Predictor Data File Requirements
--------------------------------
The predictor file(s) MUST be comma delimited (.csv) or tab delimited (.txt).

	BATCH FILE
	(i)  A batch file of predictor data for the discrete trait that you wish to modify to the GLM specification.
   	     These are the requirements for this batch file of predictor data:

		1. The first value in the first line should be the name of the discrete trait that you wish to model as a GLM.
	  	2. The remaining values in the first line MUST be the names of the predictors.
		3. The first value in all remaining lines must be the names of the discrete states in the XML file. 
		   The order of the states does not matter as the program will sort them according to the order specified in the XML file.
		4. The remaining values in each line MUST be the values of the predictor in the column for the line's discrete state.
		5. A predictor will be created for each predictor name in the first row.
	
			BATCH EXAMPLE: "batchPredictorData.csv"
				state,temperature,precipitation,latitude,population_density,vaccination_rate
				state1,38.4,11.3,14.5,96.7,0.61
				state2,43.1,15.4,17.9,1052.0,0.68
				state3,33.1,30.0,19.0,433.1,0.55
				state4,27.4,10.9,14.3,356.4,0.51

	INDIVDIUAL FILE
	(ii) An individual file of predictor data for a single predictor. Each of these files must be in a single directory <singlePredictorDir>
	     These are the requirements for the files of individual predictor data:
	     
	     	1. The first value in the first line should be the name of the predictor.
	     	2. The remaining values in the first line MUST be the names of the discrete states for the discrete trait.
	     	3. The first value in all remaining lines MUST be the names of the discrete states for the discrete trait.
	     	4. The remaining values in each line MUST represent the value in the matrix corresponding to the transition from
	     	   the <discrete state in the row> to the <discrete state in the column>.
	     	5. Note: Values in the diagonal places should be 0.
   	     
			INDIVIDUAL EXAMPLE: "individualPredictorData.txt"
				humidity	state1	state2	state3	state4
				state1	0	1.5	6.8	3.5
				state2	3.5	0	1.8	2.9
				state3	8.8	6.4	0	7.9
				state4	27.4	10.9	14.3	0

The program will check for any invalid values (i.e. data that are not float-able) and inform you where incorrect
points in the file are (line/column). The program WILL AUTOMATICALLY LOG TRANSFORM YOUR DATA (natural log). 
There is no need to do this prior to running the program. Any predictor data that you upload that has already been log-tranformed 
will thus be incorrect in the new XML file.

Program Output
--------------
The program will output a new XML file with the discrete trait modeled as a log-linear GLM of the specified predictor data. The name
of this XML file will be as follows:
	
	Input: 	name_of_input_file.xml
	Output:	name_of_input_file_GLMedits.xml

Furthermore, all logfiles, treefiles, operator analysis files, marginal likelihood estimator files, etc. that were in the original
XML input file will be renamed accordingly (e.g. bat_rabies.log --> bat_rabies_GLMedits_state.log). This allows the original XML
file and the GLM file to both be executed without conflicting logfile names.


Example
-------
Contained in the package "WNV_Example" is a BEAST XML file for West Nile Virus that models "location" as a discrete trait.
Also included is a batch predictor file "fakeBatchFile.txt" and a directory "fakeSinglePredictorDir" that contains five single
predictor files. These files should provide examples of proper formatting of your data files. The program can create a new XML file
for the discrete "location" trait from any of the following four arguments:


1. $ python create_glm_xml.py wnvtest.xml location single .\fakeSinglePredictorDir
2. $ python create_glm_xml.py wnvtest.xml location single .\fakeSinglePredictorDir batch fakeBatchFile
3. $ python create_glm_xml.py wnvtest.xml location batch fakeBatchFile single .\fakeSinglePredictorDir
4. $ python create_glm_xml.py wnvtest.xml location batch fakeBatchFile

Here, (1) uses only the four single predictors in "fakeSinglePredictorDir".
      (2)/(3) are functionally equivalent and use both the single predictors in "fakeSinglePredictorDir" and the batch predictor file "fakeBatchFile.txt".
      (4) uses only the batch predictor file "fakeBatchFile.txt".

Support
-------
Please email me at djmagee@asu.edu with any problems that you experience. Please report specific error messages. 
It would helpful to send me your XML file, predictor data file(s) and program inputs so that I can trace the bug.


Tips
----
1. Ensure that all predictor data is valid (i.e. can be converted to floating points). 
2. DO NOT log-transform your data prior. The program will perform this operation.
3. Per (2), all predictor data will be log-transformed, and thus must be positive.
   EXCEPTION: 
   	Coordinate data are permitted if a "distance" predictor is desired. If this is the case,
   	name your coordinate predictors either "latitude" and "longitude" (or "lat" and "long")
   	in the predictor input file. The program will detect these predictors and ask if a 
   	"distance" predictor is desired. The great circle distance will be calculated for all coordinates.
   If a "distance" predictor is not desired, ensure that your coordinate data (e.g. latitude) is positive.
   Relative coordinates may be appropriate in this case.
4. Remember, you may also upload an individual predictor file (like distance) directly from the <singlePredictorDir>.
5. Ensure that you know which direction that you want each predictor to be modeled. By default, all predictors
   will be set to model from both <discreteTraitName> of origin and <discreteTraitName> of destination. The user will be prompted to 
   customize the list until they are satisfied with the direction of all predictors. If a predictor is no longer
   desired, it can be removed from the list.
6. The program is generally NOT case sensitive.
7. The names of the discrete states in the predictor data file MUST match the names of the discrete states
   in the input XML file that you wish to model as a GLM.
8. Feel free to contact me at djmagee@asu.edu with any questions on the program requirements, inputs, or bugs.
	
	
Citations	
---------
(1) Faria NR, Suchard MA, Rambaut A, Streicker DG, Lemey P. Simultaneously reconstructing 
	viral cross-species transmission history and identifying the underlying 
	constraints. Philos Trans R Soc Lond B Biol Sci. 2013 Feb 4;368(1614):20120196. 
	doi: 10.1098/rstb.2012.0196

(2) Lemey P, Rambaut A, Bedford T, Faria N, Bielejec F, Baele G, Russell CA, Smith DJ, 
	Pybus OG, Brockmann D, Suchard MA. Unifying viral genetics and human 
	transportation data to predict the global transmission dynamics of human 
	influenza H3N2. PLoS Pathog. 2014 Feb 20;10(2):e1003932. 
	doi: 10.1371/journal.ppat.1003932