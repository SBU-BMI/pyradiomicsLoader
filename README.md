# pyradiomicsLoader
a docker container utility to load pyradiomics feature data set (as csv file) to quip instance

Step 1: download source code from github repository;

     git clone https://github.com/SBU-BMI/pyradiomicsLoader.git
     
Step 2: build and run docker container ;
  cd pyradiomicsLoader folder;
  
  docker-compose -f docker-compose.yml build
  
  docker-compose -f docker-compose.yml up
  
Step 3: copy pyradiomics to folder ./data/radiomics_results/ 
  each image with one individual subfolder.
  
Step 4: create manifest.csv file in  folder ./data/radiomics_results/ 
  sample:
  radiomicsdir,studyid,clinicaltrialsubjectid,imageid
  xxxxxxxxxxx10-multires.tif,Rutgers:Lung,10,xxxxxxxxxxx10
  xxxxxxxxxxx20-multires.tif,Rutgers:Lung,20,xxxxxxxxxxx20
  
Step 5: run command to load pyradiomics

  docker exec quip-radiomicsloader loadPyradiomics --src radiomics_results --collectionname collectionname --user username --passwd password
