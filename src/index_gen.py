import os
import xlrd,xlwt
import sys,getopt
import csv
import re
import threading

MAX_TIME_DIVETION = 5
result_dir = ""

def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]

class ReadRawTagsThread (threading.Thread):
   def __init__(self, threadID, filename):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.filename = filename
      self.result = []
   def run(self):
      print ("processing " + self.filename + '...')
      ws = csv.reader(open(self.filename, 'r'))
      items = list(ws)
      for item in items:
         self.result.append(item[1])

      print ("exiting thread {:d}...".format(self.threadID))

   def get_result(self):
      try:
         return self.result
      except Exception:
         return None


def TakeElementTwo(elem):
   return elem[1]

def CreateListFile(WorkMode,start_tag,sample_num,sample_interval):
   idx_files = getFiles(os.getcwd(),'cross_section_index.csv')
   if len(idx_files) >0:
      idxf = idx_files[0]
   else:
      return

   if WorkMode == 'None':
      return

   elif WorkMode == 'All':
      # extract all valid tag to list file
      idx_ws = csv.reader(open(idxf, 'r'))
      idx_records = list(idx_ws)

      sec_list = []
      for idx,idx_row in enumerate(idx_records):
         if idx !=0 and idx_row[1] == '1':
               sec_list.append([idx_row[0]])

      file_to_write = open(os.getcwd()+'\\' + 'cross_section_list.csv','w',encoding='utf8',newline='')
      writer = csv.writer(file_to_write)
      print('Writting tag_list.csv')

      writer.writerows(sec_list)
      file_to_write.close()
      

   elif WorkMode == 'partial_section':
      # extract desinated tag to list file
      idx_ws = csv.reader(open(idxf, 'r'))
      idx_records = list(idx_ws)

      sec_list = []
      sample_cnt = 0
      last_tag = 0
      # check sample_number, if =0 means all valid samples
      if sample_num == 0:
         sample_num = len(idx_records)

      for idx,idx_row in enumerate(idx_records):
         if idx !=0 and idx_row[1] == '1' and idx > start_tag and sample_cnt <= sample_num:
            if int(sample_interval) > 0:    # interval mode
               if int(idx_row[0]) - last_tag >= int(sample_interval):
                  sec_list.append([idx_row[0]])
                  last_tag = int(idx_row[0])
                  sample_cnt+=1
            else:
               sec_list.append([idx_row[0]])
               sample_cnt+=1
               last_idx = idx
      
      file_to_write = open(os.getcwd()+'\\' + 'cross_section_list.csv','w',encoding='utf8',newline='')
      writer = csv.writer(file_to_write)
      print('Writting tag_list.csv')

      writer.writerows(sec_list)
      file_to_write.close()      


def CreateIndexFile(srcdir):
   raw_files = []
   sub_dirs = []
   
   csv_files = getFiles(os.getcwd() + srcdir,'.csv')

   for csvf in csv_files:
      filename = os.path.basename(csvf)
      dirname = os.path.dirname(csvf)
      cwd = os.getcwd()
      pos = dirname.find(cwd) +len(cwd)
      subdir = dirname[pos:]

      if "Result" in filename:
         if not subdir in sub_dirs:
            sub_dirs.append(subdir)
            print("adding " + subdir + ' to search list...')
      
 
   #in each search directories process Resultx.csv file
   
   for subdir in sub_dirs:
      result_tag = []
      raw_files = getFiles(os.getcwd()+subdir,'.csv')
     
      for idx,raw in enumerate(raw_files):
         print ("processing " + raw + '...')
         rawname = os.path.basename(raw)
         if "Result" in rawname:
            cam_num = int(re.sub("\D","", rawname))-1
            result = []
            ws = csv.reader(open(raw, 'r'))
            items = list(ws)
            for item in items:
               result.append([cam_num,int(item[1]),0])

            result_tag.extend(result)

      print('read process in folder ' + subdir + ' complete...')
      #flush tags
      print('flushing time tags...')

      result_tag.sort(key=TakeElementTwo)

      # create index file in csv
      
      # delete index file if exists
      if not os.path.exists(os.getcwd() + subdir + result_dir):
         os.mkdir(os.getcwd() + subdir + result_dir)

      indexfile = os.getcwd() + subdir + result_dir + '\\cross_section_index.csv'
      if os.path.isfile(indexfile):
         os.remove(indexfile)

      header = ["REF_TAG","VALID","tag_CAM1","tag_CAM2","tag_CAM3","tag_CAM4","tag_CAM5","tag_CAM6","tag_CAM7","tag_CAM8",'CONTA_ID','TUBE_ID','MILEAGE']
      with open(indexfile, 'w', newline='') as f: 
         writer = csv.writer(f)
         writer.writerow(header)

      # for i in range(0,len(row0)):
      #    sheet1.col(i).width = 3000
      #    sheet1.write(0,i,row0[i],style)
      
      # read from Raw file
      xls_rows = []
      
      for idx,tag_item in enumerate(result_tag):
         xls_row = ['','','','','','','','','','','','','']
         if tag_item[2] == 0:
            ref_tag = tag_item[1]
            xls_row[0] = "{:0>8d}".format(ref_tag) 
            ref_cam_idx = tag_item[0]
            xls_row[ref_cam_idx+1] = "{:0>8d}".format(ref_tag)
            # search for con-current frame tags
            for inc in range(1,min(16,len(result_tag)-idx)):
               if result_tag[idx+inc][0] != ref_cam_idx and (result_tag[idx+inc][1] - ref_tag) < MAX_TIME_DIVETION and result_tag[idx+inc][2] == 0:
                  cam_idx = result_tag[idx+inc][0]
                  xls_row[cam_idx+1] = "{:0>8d}".format(result_tag[idx+inc][1])
                  result_tag[idx+inc][2] = 1

            tag_item[2] = 1
            xls_rows.append(xls_row)

      # check for valid tags
      for idx,row_item in enumerate(xls_rows):
         valid = True
         for i in range(2,10):
            if row_item[i] == '':
               valid = False
               break
         if valid:
            row_item[1] = '1'
         else:
            row_item[1] = ''
         
      # write 
      # font.bold = False # 黑体
      # style.font = font # 设定样式

      # for idx,row_item in enumerate(xls_rows):
      #    for i,col_item in enumerate(xls_rows[idx]):
      #       sheet1.write(idx+1,i,col_item,style)   
      with open(indexfile, 'a', newline='') as f: 
         writer = csv.writer(f)
         writer.writerows(xls_rows)
      
      # idxf.save(indexfile)
      print('index file created successfully...')

   print('All process complete...')

   


# main function of this program
# index_gen.py will generate index files for further processing
# 1. cross-section-index is the tag index for all original data
# 2. sample_index is the index list according to parameters

def main(argv):
   bCreateIndex = False
   bCreateList = False
   bIndexExist = False
   WorkMode = 'None'
   start_tag = 0
   sample_interval = 1
   sample_num = 1
   src_dir = ''
   sample_num = 0

   try:
      opts, args = getopt.getopt(argv,"hial:v:s:",["index","all","tag=","len=","interval=","srcdir=","start="])
   except getopt.GetoptError:
      print('cs_split.py -h -i -t <time_tag> -p [-l <section_length_in_ms> | -s <number_of_sections>]')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('cs_split.py -h -i -t <time_tag> -p [-l <section_length_in_ms> | -s <number_of_sections>]')
         sys.exit()

      # create index file
      elif opt in ("-i", "--index"):
         bCreateIndex = True

      # extract all tags to list file
      elif opt in ("-a","--all"):
         WorkMode = 'All'
         bCreateList = True

      # start tag of samples, default is the first valid tag
      elif opt in ("-s","--start"):
         WorkMode = 'partial_section'
         start_tag = arg

      # number of samples
      elif opt in ("-l","--len"):
         WorkMode = 'partial_section'
         sample_num = arg

      # interval of samples in milisec
      elif opt in ("-v","--interval"):
         WorkMode = 'partial_section'
         sample_interval = arg

      # source directory
      elif opt in ("--srcdir") :
         src_dir = arg

   index_files = getFiles(os.getcwd(),'cross_section_index.csv')
   if len(index_files) == 0 or bCreateIndex:
      CreateIndexFile(src_dir)
      bIndexExist = True
   else:
      bIndexExist = True

   if bIndexExist and WorkMode!= "None":
      CreateListFile(WorkMode,start_tag,sample_num,sample_interval)


# execute only if run as a script
if __name__ == "__main__":
    main(sys.argv[1:])
