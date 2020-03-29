import os
import sys
import csv
from threading import Thread

def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]

def getSubdirs(path):
    subdirs = []
    for root,dirs,files in os.walk(path):
        for name in dirs:
            subdirs.append(os.path.join(root,name))
    return subdirs

def Data_split(raw_file,sample_path,mode,param):
    lines = len(open(raw_file).readlines())
    ws=csv.reader(open(raw_file,'r'))
    row = list(ws)

    if mode == 'sample_mode':       #time sample mode
        start = int(param[0])
        end = start + int(param[1])
        intv = int(param[2])
        sample_len =int(param[3])  
        
        path,name=os.path.split(raw_file)
        file_name,file_ext = name.split('.')
        file_to_write = open(path + sample_path + file_name + '_intv' + str(intv) + '-len' + str(sample_len) + '.csv','a',encoding='utf8',newline='')
        sample_time = start

        for idx in range(0,lines-1):
            timestamp = int(row[idx][1])

            if timestamp >= sample_time and timestamp <= sample_time + sample_len:
                writer = csv.writer(file_to_write)
                writer.writerow(row[idx])
                sample_time += intv

        file_to_write.close()

    elif mode == 'snap_mode':
        start = int(param[0] + param[1])
        end = start + int(param[3])

        #print('start at:{0} ms'.format(start))
        # 分离文件名与扩展名os.path.split(filename)
        path,name=os.path.split(raw_file)
        file_name,file_ext = name.split('.')
        file_to_write = open(sample_path + file_name + '_' + str(start) + '-' + str(end) + '.csv','a',encoding='utf8',newline='')
        sample_time = start

        for idx in range(0,lines-1):
            timestamp = int(row[idx][1])

            if timestamp >= start and timestamp <= end:
                writer = csv.writer(file_to_write)
                writer.writerow(row[idx])

        file_to_write.close()



class Timetag:
    start = 0
    end = -1
    current = 0

    def __init__(self, file):
        lines = len(open(file).readlines())
        ws=csv.reader(open(file,'r'))
        row = list(ws)
        self.start = int(row[0][1])
        self.end = int(row[lines-1][1])


class AnalyzingThread (Thread):   
    tag_result = []
    def __init__(self, threadID, threadName, raw_name, sample_path):
        Thread.__init__(self)
        self.threadID = threadID
        self.threadName = threadName
        self.raw_name = raw_name  
        self.sample_path = sample_path
    def run(self):  
        print('analyzing ' + self.raw_name + '...')
        tag = Timetag(self.raw_name)
        self.tag_result = [tag.start,tag.end]
        print(self.raw_name + " start at " + str(tag.start) + 'ms, end at' + str(tag.end))
        #print('processing data sample in ' + self.raw_name + '...') 

    def get_result(self):
        try:
            return [self.tag_result]
        except Exception:
            return None 



class SampleThread (Thread):   
    
    def __init__(self, threadID, threadName, raw_file, sample_dir,tag_list,sample_len,search_range):
        Thread.__init__(self)
        self.threadID = threadID
        self.threadName = threadName
        self.raw_name = raw_file  
        self.sample_dir = sample_dir
        self.tag_list = tag_list.copy()
        self.search_range = search_range
        self.sample_len = sample_len
    def run(self):  
        print('Spliting ' + self.raw_name + '...')
        ws=csv.reader(open(self.raw_name,'r'))
        rows = list(ws)

        path,name=os.path.split(self.raw_name)

        for idx in range(0,len(rows)):
            timestamp = int(rows[idx][1])
            if len(self.tag_list) > 0 and timestamp >= self.tag_list[0] and (timestamp - self.tag_list[0]) < self.search_range:
                file_to_write = open(self.sample_dir + '\\' + str(self.tag_list[0]) + '\\' + name ,'a',encoding='utf8',newline='')   
                writer = csv.writer(file_to_write)

                if (len(rows) - idx) > self.sample_len:
                    valid_len =  self.sample_len
                else:
                    valid_len = len(rows) - idx

                for inc in range(0,valid_len):
                    writer.writerow(rows[idx+inc])
                file_to_write.close()
                if len(self.tag_list) > 0:
                    self.tag_list.pop(0)
        print('split complete')
            
    def get_result(self):
        try:
            return [self.tag_result]
        except Exception:
            return None 



#main entry
#path = os.getcwd()
path = os.getcwd() + '\\raw_data'
raw_files = getFiles(path,'.csv')
time_tags = []
AnalyzingThreads = []
mode = ''
interval=1
bias=0
length=1

for idx in range(1,len(sys.argv)):
    if sys.argv[idx] == '-m' and idx < len(sys.argv):
        #get mode
        mode = sys.argv[idx+1]

    if sys.argv[idx] == '-i' and idx < len(sys.argv) and mode == 'sample_mode':
        #get sample interval
        interval = int(sys.argv[idx+1])

    if sys.argv[idx] == '-b' and idx < len(sys.argv) and mode == 'snap_mode':
        #get start bias
        bias = int(sys.argv[idx+1])

    if sys.argv[idx] == '-l' and idx < len(sys.argv):
        #get sample length
        length = int(sys.argv[idx+1])

#delete exist csv file
prev_csv_path = os.getcwd() + '\\samples'
prev_csv_files = getFiles(prev_csv_path,'.csv')
for file in prev_csv_files:
    if os.path.isfile(file):           
        os.remove(file)
prev_dirs = getSubdirs(prev_csv_path)
for dir in prev_dirs:
    if os.path.exists(dir):
        os.rmdir(dir)

#search for valid time tag range
for idx in range(0,len(raw_files)):
    thread_name = 'AnalyzingThread' + str(idx)
    # print(thread_name)
    AnalyzingThreads.append(AnalyzingThread(idx,thread_name,raw_files[idx],os.getcwd() + '\\samples\\'))
    AnalyzingThreads[idx].start()

for th in AnalyzingThreads:
    th.join()
    time_tags.append(th.get_result())

valid_start_tag = 0
valid_end_tag = 1000000000
for tag in time_tags:
    if valid_start_tag < tag[0][0]:
        valid_start_tag = tag[0][0]

    if valid_end_tag > tag[0][1]:
        valid_end_tag = tag[0][1]

print('valid_start='+str(valid_start_tag)+'  '+ 'valid_end='+str(valid_end_tag) + '  ' + 'valid_length=' + str(valid_end_tag-valid_start_tag))

if mode == 'snap_mode':
    for idx in range(0,len(raw_files)):
        dir_path = os.getcwd() + '\\samples\\' + str(valid_start_tag + bias)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        Data_split(raw_files[idx],dir_path + '\\',mode,[valid_start_tag,bias,interval,length])
elif mode == 'sample_mode':
    #create tag list for samples
    tag_list = []
    for tag in range(valid_start_tag,valid_end_tag,interval):
        tag_list.append(tag)
        #creating subdirs for individual sample tags
        dir_path = os.getcwd() + '\\samples\\' + str(tag)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    # thread_name = 'SplitThread' + str(0)
    # th = SampleThread(idx,thread_name,raw_files[0],os.getcwd() + '\\samples\\',tag_list,length)
    # th.start()
    # th.join()
    SampleThreads = []

    for idx in range(0,len(raw_files)):
        thread_name = 'SplitThread' + str(idx)
        SampleThreads.append(SampleThread(idx,thread_name,raw_files[idx],os.getcwd() + '\\samples\\',tag_list,length,100))
        SampleThreads[idx].start()
        
    for th in SampleThreads:
        th.join()
        

print('finished')
