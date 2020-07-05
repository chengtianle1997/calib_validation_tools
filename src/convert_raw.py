import camraw2xy
import os,getopt
import sys
import csv


def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]



# main entrance of this program

# execute only if run as a script
def main(argv):
    
    bUsingListFile = False
    bUsingIndexFile = False
    en_multi_thread_mode = False
    indexfilename = []

    bExtractAllValidData = False
    raw_subdir = ''

    dst_dir = 'cross_section_data'

    # get args
    help_str = '''
        convert_raw.py -h -l <list_file> -i <index_file> -t <time_tag> 
    '''
    try:
        opts, args = getopt.getopt(argv,"hamlit:",["help","multithread","all","list=","index=","timetag=","srcdir=","dstdir="])
    except getopt.GetoptError:
        print(help_str)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_str)
            sys.exit(2)

        elif opt in ("-a","--all"):
            bExtractAllValidData = True

        elif opt in ("-l", "--list"):
            bUsingListFile = True
            if len(arg) != 0:
                listfilename = getFiles(os.getcwd(),arg) 
            else:
                listfilename = getFiles(os.getcwd(),'cross_section_list.csv')  
            if len(listfilename)  == 0:
                print('list file not found, exiting...')  
                sys.exit(2)
           

        elif opt in ("-i", "--index"):
            bUsingIndexFile = True
            if len(arg) != 0:
                indexfilename = getFiles(os.getcwd(),arg)
            else:
                indexfilename = ''
            if len(indexfilename)  == 0:
                print('index file will be automatically searched...')  
                

        elif opt in ("-t","--timetag"):
            time_tag = int(arg)

        elif opt in ("--srcdir"):
            raw_subdir = arg

        elif opt in ("-m","--multithread"):
            en_multi_thread_mode = True
            
        elif opt in ("--dstdir"):
            dst_dir = arg

    cfg_file = getFiles(os.getcwd(),'Config.ini')


    if bUsingListFile:
        ws = csv.reader(open(listfilename[0], 'r'))
        sections = list(ws)

        # search for every subdirs for data from different test time
        subdir_list = []

        if raw_subdir != '':
            subdir_list.append(raw_subdir)
        else:
            for section in sections:
                if not section[1] in subdir_list:
                    subdir_list.append(section[1])

        # walk in each subdir
        for subdir in subdir_list:
            ref_tag_list = []
            # extract cross-sections in each subdir
            for section in sections:
                if len(section) == 1:
                    ref_tag_list.append(int(section[0]))

                else:
                    if section[1] == subdir:
                        ref_tag_list.append(int(section[0]))
                        
            raw_files = getFiles(os.getcwd(),'.csv')

            if len(indexfilename) == 0:
                indexfiles = getFiles(os.getcwd(),'cross_section_index.csv')
                for idxf in indexfiles:
                    if subdir in idxf:
                        indexfilename = idxf
                        break

            pointcloud_xys = []

            # check for result folder, if not exists, make dir
            result_path = os.getcwd() + '\\' + dst_dir + '\\'
            if not os.path.exists(result_path):
                os.mkdir(result_path)
            
            for raw in raw_files:
                filename = os.path.basename(raw)
                if "Result" in filename and subdir in raw:
                    # print("reading " + raw)

                    # get CAM_num
                    cam_idx,foo = filename.split('.csv')
                    foo,cam_idx = cam_idx.split('Result')
                    cam_idx = int(cam_idx) - 1

                    # according to ref_tag_list, retrieve tags for each CAM to generate section_tag_list
                    idx_ws = csv.reader(open(indexfilename, 'r'))
                    idx_records = list(idx_ws)

                    sec_list = []
                    for idx,idx_row in enumerate(idx_records):
                        if idx !=0 and int(idx_row[0]) in ref_tag_list and idx_row[1] == '1':
                            sec_list.append(int(idx_row[cam_idx+1]))

                    if len(idx_records) > 32 and en_multi_thread_mode:
                        pointcloud_xys=(camraw2xy.ConvertMultiSectionsMultiThreading(cfg_file,raw,sec_list))
                    else:
                        pointcloud_xys=(camraw2xy.ConvertMultiSections(cfg_file,raw,sec_list))

                    print('writting result file for CAM{:d}...'.format(cam_idx))
                    for cross_sec in sec_list:
                        for idx,idx_row in enumerate(idx_records): 
                            if idx !=0 and idx_row[1] == '1' and int(idx_row[cam_idx+1]) == cross_sec: 
                                sec_num = idx_row[0]
                                file_to_write = open(result_path + sec_num + '.csv','a',encoding='utf8',newline='')
                                writer = csv.writer(file_to_write)
                                print('Writting points for section '+ sec_num )
                                for pt in pointcloud_xys:
                                    if pt[1] == cross_sec:
                                        writer.writerow(pt[0])

                                file_to_write.close()

           


    else:
        raw_files = getFiles(os.getcwd()+raw_subdir,'.csv')

        pointcloud_xy = []
        dir_path = os.getcwd() + '\\cross_section_data\\'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
            
        for raw in raw_files:
            filename = os.path.basename(raw)
            if "Result" in filename:
                print("processing " + raw)
                pointcloud_xy.extend(camraw2xy.convert(cfg_file,raw,time_tag))

        file_to_write = open(dir_path + "{:08d}".format(time_tag) + '.csv','a',encoding='utf8',newline='')
        writer = csv.writer(file_to_write)
        writer.writerows(pointcloud_xy)

        file_to_write.close()
    print("process complete...")


    # execute only if run as a script
if __name__ == "__main__":
    main(sys.argv[1:])