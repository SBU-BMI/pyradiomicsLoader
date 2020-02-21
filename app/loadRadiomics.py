from __future__ import print_function
import datetime
import csv
import glob
import json
import os
import random
import collections


from multiprocessing import Pool

from geojson import Point, Polygon

from pathdbapi import *

import quipargs
import quipdb

pathdb = False
pdb = {}


def is_blank(myString):
    if myString and myString.strip():
        # myString is not None AND myString is not empty or blank
        return False
    # myString is None OR myString is empty or blank
    return True


def check_args_pathdb(args):
    if not args['user'] or not args['passwd'] or not args['collectionname']:
        eprint("dependency error")
        eprint("when in pathdb mode, must provide: url, username, and password")
        exit(1)
    pdb["collection"] = args["collectionname"]
    pdb["url"] = args["url"]
    pdb["user"] = args["user"]
    pdb["passwd"] = args["passwd"]
    pdb["slide"] = ""
    # pdb["uuid"] = ""

def chech_segment_record(slide_id):
  dbhost = quipargs.args["dbhost"]
  dbport = quipargs.args["dbport"]
  dbname = quipargs.args["dbname"]
  myclient = quipdb.connect(dbhost, dbport)
  mydb = quipdb.getdb(myclient, dbname)  
  count=quipdb.getRecordCount(mydb,slide_id)   
  myclient.close()
  return count;


def read_radiomics_feature_selected():
  #read radiomics_feature_selected.txt file   
  feature_array=[]; 
  radiomics_feature_selected = "radiomics_features_selected.txt"
  feature_selected_file_path = os.path.join("/data/", radiomics_feature_selected); 
  with open(feature_selected_file_path,) as f:
    reader = csv.reader(f, delimiter=',')
    my_list = list(reader);    
    for each_row in my_list:                      
      feature=str(each_row[0]);
      yes_no=str(each_row[1]);      
      if yes_no == "yes":   
        feature_array.append(feature);    
  return  feature_array;              


def loadRadiomics(pdb,feature_array,file_loc):  
  csv_file=os.path.join(file_loc, 'patch_level_radiomics_features.csv');  
  if not os.path.isfile(csv_file):
    eprint("patch_level_radiomics_features.csv is not found!")
    exit(1)   
  patch_position=["image_width","image_height","mpp_x","mpp_y","patch_x","patch_y","patch_width","patch_height"];   
  combined_feature_array=[]
  for feature in patch_position:
    combined_feature_array.append(feature);
  for feature in feature_array:
    combined_feature_array.append(feature);  
  
  feature_value_total_array=[];
  feature_index_dict={};
  with open(csv_file,newline='') as csvFile:
    csv_reader = csv.reader(csvFile) ;   
    for line_count, row in enumerate(csv_reader):
      feature_value = {};
      for feature in combined_feature_array:        
        if line_count == 0:# This is the title row
          feature_id=row.index(feature);
          feature_index_dict[feature]=feature_id                                  
        else:# rest of data rows
          feature_value['line_count'] = line_count;
          feature_id=feature_index_dict[feature];
          value= row[feature_id];           
          if value!='None' and value!='0.0':              
            try:
              float_value=float(value);
              float_value = round(float_value,3);               
              feature_value[feature] = float_value;
            except Exception as e: 
              print (e);
              print (value);
              continue;   
          else:
            value="none"  
            feature_value[feature] = value; 
      if line_count != 0:                                                    
        feature_value_total_array.append(feature_value);                          
  
  for feature in feature_array:                     
    save2Heatmap(pdb,feature_value_total_array,feature);
    
          
def save2Heatmap(pdb,feature_value_total_array,feature):   
  case_id=pdb['imageid'] ; 
  subject_id = pdb['subject']  
  specimen = "";
  study=""
  study_id = pdb['study'] 
  pathdb_id = pdb['slide']
  execution_id = "PL_Pyradiomics_" + str(feature);     
  
  min_value=0.0;
  max_value=0.0;  
  feature_value_list=[];
  for mata_data in feature_value_total_array:
    feature_value=mata_data[feature]; 
    if feature_value !='none':
      feature_value_list.append(feature_value);
  min_value=min(feature_value_list);    
  max_value=max(feature_value_list); 
  min_value=float("{0:.2f}".format(min_value))
  max_value=float("{0:.2f}".format(max_value))    
   
  dict_img = {}
  dict_img['case_id'] = case_id
  dict_img['subject_id'] = subject_id
  dict_img['slide'] = str(pathdb_id);
  dict_img['specimen'] = specimen
  dict_img['study'] = study  
    
  dict_analysis = {}
  dict_analysis['study_id'] = study_id
  dict_analysis['computation'] = 'heatmap';
  dict_analysis['heatmap_type'] = 'pyradiomics_feature';
  dict_analysis['setting'] = {"mode" : "gradient", "field" : feature};
  
  image_width=0;
  image_height=0;
  patch_width=0;
  patch_height=0;
  for mata_data in feature_value_total_array[0:1]:
    image_width=mata_data['image_width'];
    image_height=mata_data['image_height']
    patch_width = mata_data['patch_width'];
    patch_height = mata_data['patch_height'];  
    
  size_x=float(patch_width)/float(image_width);
  size_y=float(patch_height)/float(image_height); 
  dict_analysis['size'] = [size_x,size_y]
  dict_analysis['fields'] = [{"name":feature,"range":[min_value,max_value],"value":[min_value,max_value]}]    
  dict_analysis['execution_id'] = execution_id
  dict_analysis['source'] = 'computer'      
    
  dict_patch = collections.OrderedDict();    
  dict_provenance = {}
  dict_provenance['image'] = dict_img
  dict_provenance['analysis'] = dict_analysis   
  dict_patch['provenance'] = dict_provenance   
 
  data_array=[];  
  for mata_data in feature_value_total_array:  
    feature_value= mata_data[feature] ;
    if feature_value !='none':
      tmp_item=[];
      imageW=mata_data['image_width']; 
      imageH=mata_data['image_height'];
      patch_x=mata_data['patch_x']; 
      patch_y=mata_data['patch_y'];        
      x1=float(patch_x)/float(imageW);
      y1=float(patch_y)/float(imageH);       
      tmp_item.append(x1);
      tmp_item.append(y1);
      tmp_item.append(feature_value);      
      data_array.append(tmp_item); 
    
  dict_patch['data'] = data_array;   
    
  dbhost = quipargs.args["dbhost"]
  dbport = quipargs.args["dbport"]
  dbname = quipargs.args["dbname"]
  myclient = quipdb.connect(dbhost, dbport)
  mydb = quipdb.getdb(myclient, dbname)  
  mydb.heatmap.insert_one(dict_patch);  
  myclient.close()          
         
             
          
if __name__ == "__main__":
    quipargs.args = vars(quipargs.parser.parse_args())
    pathdb = quipargs.args["pathdb"]

    random.seed(a=None)
    csv.field_size_limit(sys.maxsize)
    
    total_checked_count=0;
    if pathdb:
        check_args_pathdb(quipargs.args)

    dirpath = os.path.join('/data', quipargs.args['src'])
    manifest = os.path.join(dirpath, 'manifest.csv')
    if not os.path.exists(manifest):
        eprint('Manifest file not found:', manifest)
        exit(1)
    
    feature_array= read_radiomics_feature_selected(); 
    print (feature_array);
    
    try:
        token_string = get_auth_token(pdb["url"], pdb["user"], pdb["passwd"])

        with open(manifest) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            for row in csv_reader:
                file_loc = os.path.join(dirpath, row[0])                 
                if not os.path.exists(file_loc):
                  eprint('File location not found:', file_loc)
                  exit(1)                
                print (file_loc);
                
                if pathdb:
                    pdb["study"] = row[1]
                    pdb["subject"] = row[2]
                    pdb["imageid"] = row[3]

                    try:
                        _id = get_slide_unique_id(token_string, pdb["url"], pdb["collection"], pdb["study"],pdb["subject"], pdb["imageid"])
                        pdb["slide"] = _id
                        if is_blank(_id):
                            eprint('Slide not found ' + pdb["imageid"])
                            exit(1)
                        print (_id);    
                    except MyException as e:
                        details = e.args[0]
                        eprint(details)
                        print(token_string,pdb["url"],pdb["collection"],pdb["study"],pdb["subject"], pdb["imageid"])
                        continue
                        #exit(1)
                '''
                #check whether segment result is availavle or not
                count=chech_segment_record(pdb["slide"]);   
                if count !=1:
                  eprint('slide_id is not available.')
                  exit(1) 
                print (file_loc,pdb["slide"],count);    
                '''                              
                print (file_loc,pdb["slide"]);                                
                loadRadiomics(pdb,feature_array,file_loc);                   
    except MyException as e:
        eprint(e.args[0])
        exit(1)
