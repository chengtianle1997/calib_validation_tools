import configparser
import os
import sys
import csv
from decimal import Decimal
import numpy as np
import math
import matplotlib.pyplot as plt
from threading import Thread


pi = Decimal(3.1415926536)
# BOX=[[0,0],[0,0]]
PointCloud_xy = []
DataIndex = 0
fitline = []
time_shift = 0
time_step = 20
option_data_persist = 0
title_info_str = ''


def calculate_intercept(pc_xy, box):
    pts_x = []
    pts_y = []
    topleft_x = box[0][0]
    topleft_y = box[0][1]
    botright_x = box[1][0]
    botright_y = box[1][1]

    if topleft_x > botright_x:
        tmp = topleft_x
        topleft_x = botright_x
        botright_x = tmp

    if topleft_y < botright_y:
        tmp = topleft_y
        topleft_y = botright_y
        botright_y = tmp    
    distance = 0

    # select points in box range
    for pt in pc_xy:
        if pt[0] > topleft_x and pt[0] < botright_x and pt[1] > botright_y and pt[1] < topleft_y:
            pts_x.append(float(pt[0]))
            pts_y.append(float(pt[1]))

    # linear regression
    if pts_x.__len__() > 0 and pts_y.__len__() > 0:
        x_array = np.array(pts_x)
        y_array = np.array(pts_y)
        coef = np.polyfit(x_array, y_array, 1)
        poly_fit = np.poly1d(coef)

        k = coef[0]
        t = coef[1]
        global verbose_mode
        if verbose_mode == 1:
            print('k='+str(k))
            print('d='+str(t))

        x = [-5000, 5000]
        global fitline
        fitline.append(plt.gca().plot(x, poly_fit(
            x), lw=0.5, alpha=0.5, color='green'))
        plt.gca().figure.canvas.draw()

        # print(poly_fit)
        distance = abs(-t/math.sqrt(k*k+1))
    #print('distance = ' + str(distance))
    return distance


def on_mouse_motion(event):
    global select_boxes
    #global line1,line2,line3,line4
    if select_boxes.__len__() > 0:
        if select_boxes[SelectBox.box_count-1].finished == 0:
            x1 = select_boxes[SelectBox.box_count-1].x1
            y1 = select_boxes[SelectBox.box_count-1].y1
            x2 = event.xdata
            y2 = event.ydata

            line1 = (plt.gca().plot([x1, x1], [y1, y2],
                                    lw=0.5, alpha=0.5, color='red'))
            line2 = (plt.gca().plot([x1, x2], [y2, y2],
                                    lw=0.5, alpha=0.5, color='red'))
            line3 = (plt.gca().plot([x2, x2], [y2, y1],
                                    lw=0.5, alpha=0.5, color='red'))
            line4 = (plt.gca().plot([x2, x1], [y1, y1],
                                    lw=0.5, alpha=0.5, color='red'))
            plt.gca().figure.canvas.draw()

            l = line1.pop(0)
            l.remove()
            l = line2.pop(0)
            l.remove()
            l = line3.pop(0)
            l.remove()
            l = line4.pop(0)
            l.remove()
            del l


def on_press(event):
    global select_boxes
    if event.button==1:   #鼠标左键点击
        #if select_boxes.__len__() == 0:
        select_boxes.append(SelectBox([event.xdata,event.ydata]))
        print("add box start position:" ,event.button,event.xdata, event.ydata)




    elif event.button==3:   
        #鼠标右键点击
        plt.gca().figure.canvas.draw()
        if SelectBox.box_count > 0:
            select_boxes.pop()
            print("clear positions")


def on_release(event):
    #global BOX
    global PointCloud_xy
    if event.button == 1:  # 鼠标左键释放
        if select_boxes[SelectBox.box_count-1].finished == 0:
            select_boxes[SelectBox.box_count-1].x2 = event.xdata
            select_boxes[SelectBox.box_count-1].y2 = event.ydata
            select_boxes[SelectBox.box_count-1].finished = 1
            print("add box end position:", event.button,
                  event.xdata, event.ydata)

            # processing data
            for box in select_boxes:
                S_intercept = calculate_intercept(
                    PointCloud_xy, [[box.x1, box.y1], [box.x2, box.y2]])
                result_str = "Intercept = " + str(S_intercept)
                plt.title(result_str)
                plt.gca().figure.canvas.draw()

                print(result_str)


def on_keypressed(event):
    global select_boxes
    global PointCloud_xy
    global DataIndex
    global valid_length
    global time_shift
    global time_step
    global option_data_persist

    if event.key in "asdwrc":
        if event.key == 'a':
            # switch to previous data_line
            if time_shift - time_step >= 0:
                time_shift -= time_step

        if event.key == 'd':
            #switch to next data_line
            
            if time_shift + time_step < valid_length:
                time_shift += time_step
                print('go to next data line:' + str(time_shift))

        if event.key == 's':
            # save result
            pass
        if event.key == 'w':
            # ---
            pass
        if event.key == 'c':
            global fitline
            for fl in fitline:
                l = fitline.pop()
                l.remove()
                del l

            plt.gca().figure.canvas.draw()

        if event.key == 'r':
            # switch refresh option
            if option_data_persist == 0:
                option_data_persist = 1
            else:
                option_data_persist = 0

        if option_data_persist == 0:
            option_str = "  Data Persist = OFF"
            PointCloud_xy = []
        else:
            option_str = "  Data Persist = ON"
            
        cord_calc.calc_step(time_shift)
        plt.cla()

        pc_x = []
        pc_y = []
        for pt in PointCloud_xy:
            pc_x.append(pt[0])
            pc_y.append(pt[1])

        #fig = plt.figure(figsize=(10, 10.5))
        plt.xlim(-5000, 5000)
        plt.ylim(-5000, 5000)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.plot(0, 0, "ob", ms=2, lw=2, color='green')
        plt.plot(pc_x, pc_y, "ob", ms=0.1, lw=0.1)
        time_str = "  Timestamp = " + str(time_shift)
        plt.title(time_str+option_str)
        plt.gca().figure.canvas.draw()


def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]

def getSubdirs(path):
    subdirs = []
    for root,dirs,files in os.walk(path):
        for name in dirs:
            subdirs.append(os.path.join(root,name))
    return subdirs


class CameraParams:
    camera_count = 0
    BP1 = 0.0
    BP2 = 0.0
    BP3 = 0.0

    def __init__(self, name):
        self.name = name
        self.position = 0
        self.SerialNum = ''
        self.Degree = Decimal('0.0')
        self.bExist = 0
        self.Uo = Decimal('0.0')
        self.Vo = Decimal('0.0')
        self.Fx = Decimal('0.0')
        self.Fy = Decimal('0.0')
        self.Bmm = Decimal('0.0')
        self.Phi = Decimal('0.0')
        self.M = Decimal('0.0')
        self.P00 = Decimal('0.0')
        self.P10 = Decimal('0.0')
        self.P01 = Decimal('0.0')
        self.P20 = Decimal('0.0')
        self.P11 = Decimal('0.0')
        self.P02 = Decimal('0.0')
        self.K00 = Decimal('0.0')
        self.K10 = Decimal('0.0')
        self.K01 = Decimal('0.0')
        self.K11 = Decimal('0.0')
        self.K02 = Decimal('0.0')
        CameraParams.camera_count += 1


class SelectBox:
    box_count = 0
    mode = 0

    def __init__(self, point_list):
        if point_list.__len__() == 2:
            self.x1 = point_list[0]
            self.y1 = point_list[1]
            self.x2 = 0
            self.y2 = 0
            self.finished = 0
        elif point_list.__len__() == 4:
            self.x1 = point_list[0]
            self.y1 = point_list[1]
            self.x2 = point_list[2]
            self.y2 = point_list[3]
            self.finished = 1

            if self.x1 < self.x2:
                tmp = self.x1
                self.x1 = self.x2
                self.x2 = tmp

            if self.y1 < self.y2:
                tmp = self.y1
                self.y1 = self.y2
                self.y2 = tmp

        if self.x1 != self.x2 or self.y1 != self.y2:
            self.index = SelectBox.box_count
            SelectBox.box_count+=1
        
         
    def __del__(self):
        if SelectBox.box_count > 0:
            SelectBox.box_count -= 1


def ReadCfg(filename):
    CAMParams = []
    cfg = configparser.ConfigParser()
    cfg.read(filename, encoding="utf-8")
    sections = cfg.sections()
    for idx in range(1, 9):
        name = 'Camera'+str(idx)
        CAMParams.append(CameraParams(name))
        CAMParams[idx-1].position = idx
        CAMParams[idx-1].SerialNum = cfg.get('CameraSerial', name)
        CAMParams[idx-1].Degree = cfg.get('CameraDegree', name)
        key_name = name + 'Uo'
        CAMParams[idx-1].Uo = cfg.get('CameraParam', key_name)
        key_name = name + 'Vo'
        CAMParams[idx-1].Vo = cfg.get('CameraParam', key_name)
        key_name = name + 'Fx'
        CAMParams[idx-1].Fx = cfg.get('CameraParam', key_name)
        key_name = name + 'Fy'
        CAMParams[idx-1].Fy = cfg.get('CameraParam', key_name)
        key_name = name + 'Bmm'
        CAMParams[idx-1].Bmm = cfg.get('CameraParam', key_name)
        key_name = name + 'Phi'
        CAMParams[idx-1].Phi = cfg.get('CameraParam', key_name)
        key_name = name + 'M'
        CAMParams[idx-1].M = cfg.get('CameraParam', key_name)
        key_name = name + 'P00'
        CAMParams[idx-1].P00 = cfg.get('CameraParam', key_name)
        key_name = name + 'P10'
        CAMParams[idx-1].P10 = cfg.get('CameraParam', key_name)
        key_name = name + 'P01'
        CAMParams[idx-1].P01 = cfg.get('CameraParam', key_name)
        key_name = name + 'P20'
        CAMParams[idx-1].P20 = cfg.get('CameraParam', key_name)
        key_name = name + 'P11'
        CAMParams[idx-1].P11 = cfg.get('CameraParam', key_name)
        key_name = name + 'P02'
        CAMParams[idx-1].P02 = cfg.get('CameraParam', key_name)
        key_name = name + 'K00'
        CAMParams[idx-1].K00 = cfg.get('CameraParam', key_name)
        key_name = name + 'K10'
        CAMParams[idx-1].K10 = cfg.get('CameraParam', key_name)
        key_name = name + 'K01'
        CAMParams[idx-1].K01 = cfg.get('CameraParam', key_name)
        key_name = name + 'K11'
        CAMParams[idx-1].K11 = cfg.get('CameraParam', key_name)
        key_name = name + 'K02'
        CAMParams[idx-1].K02 = cfg.get('CameraParam', key_name)

    CameraParams.BP1 = cfg.get('ParamDetail', 'BP1')
    CameraParams.BP2 = cfg.get('ParamDetail', 'BP2')
    CameraParams.BP3 = cfg.get('ParamDetail', 'BP3')

    return CAMParams
    # end of ReadCfg()


def GetRawTagInfo(rawdata_path):
    time_tags = []
    raw_files = getFiles(rawdata_path, 'csv')
    for csv_file in raw_files:
        ws=csv.reader(open(csv_file,'r'))
        row = list(ws)  
        lines = len(row)
        tags = []
        tags.append(csv_file.__str__())
        for idx in range(0, lines-1):
            tags.append(int(row[idx][1]))

        time_tags.append(tags)

    return time_tags


# transfor coordinates for a single camera
def TransformCoordinates(param_file, rawdata_file, time_tag):
    # load camera params
    CAMParams = ReadCfg(param_file)

    cam_idx = 0
    #time_tags = []
    #BasicDegreeWorld = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    #BasicDegree = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    BasicDegreeWorld = Decimal('0.0')
    BasicDegree = Decimal('0.0')

    PCloud_ds = []
    PCloud_xy = []

    ws = csv.reader(open(rawdata_file, 'r'))
    #lines = ws.line_num()
    row = list(ws)

    # find the camera serial in the rawdata_file
    for idx in range(0, CAMParams.__len__()):
        if row[0][0] == CAMParams[idx].SerialNum:
            cam_idx = CAMParams[idx].position-1

    # initial degree value for each camera
    deg = Decimal(CAMParams[idx].Degree)
    BasicDegreeWorld = deg * pi / Decimal('180.0')
    BasicDegree = pi / Decimal('2.0') + BasicDegreeWorld

    CAMParams[cam_idx].bExist = 1

    # x-y coordinates of points in camera system for single camera
    cam_coordinates = []

    # these two list consists polar-coordinates of points in world system
    world_ds = []  # polar coordinates of points for single camera
    world_xy = []  # x-y of points in world system

    # load common params for single camera
    degree = Decimal(CAMParams[cam_idx].Degree) * pi / Decimal(180)
    BP1 = Decimal(CAMParams[cam_idx].BP1)
    BP2 = Decimal(CAMParams[cam_idx].BP2)
    BP3 = Decimal(CAMParams[cam_idx].BP3)
    Uo = Decimal(CAMParams[cam_idx].Uo)
    Vo = Decimal(CAMParams[cam_idx].Vo)
    Fx = Decimal(CAMParams[cam_idx].Fx)
    Fy = Decimal(CAMParams[cam_idx].Fy)
    Bmm = Decimal(CAMParams[cam_idx].Bmm)
    Phi = Decimal(CAMParams[cam_idx].Phi)
    M = Decimal(CAMParams[cam_idx].M)
    P00 = Decimal(CAMParams[cam_idx].P00)
    P01 = Decimal(CAMParams[cam_idx].P01)
    P10 = Decimal(CAMParams[cam_idx].P10)
    P11 = Decimal(CAMParams[cam_idx].P11)
    P20 = Decimal(CAMParams[cam_idx].P20)
    P02 = Decimal(CAMParams[cam_idx].P02)

    K00 = Decimal(CAMParams[cam_idx].K00)
    K01 = Decimal(CAMParams[cam_idx].K01)
    K10 = Decimal(CAMParams[cam_idx].K10)
    K11 = Decimal(CAMParams[cam_idx].K11)
    K02 = Decimal(CAMParams[cam_idx].K02)

    # search for time_tag
    index = 0
    for idx in range(0,len(row)-1):
        if idx <(len(row)-2) and abs(time_tag - int(row[idx][1])) < (int(row[idx+1][1]) - int(row[idx][1])):
            index = idx
    
    if verbose_mode == 1:
        print('time_tag = ' + str(time_tag))          
        print('current idx = ' + str(index))    

    #read raw data from csv
    for col in range(2,row[0].__len__(),2):
        cam_x = row[index][col]         #get x cam-coordinate of a point
        cam_y = str((col / 2)-1)    #get y cam-coordinate of a point
        cam_coordinates.append([cam_x,cam_y])       #add to cam-coordinate list

        x = Decimal(cam_x)          #convert string to decimal
        y = Decimal(cam_y)

        # convert to world coordinates in polar
        Cd = Decimal(math.atan((Vo - y)/Fy))
        Ay = K00 + K10 * Cd + K01 * x + K11 * Cd * x + K02 * x * x

        world_degree = degree + Ay

        alpha = degree + Ay
        Fxcor = P00 + P10 * x + P01 * Cd + P20 * x * x + P11 * Cd * x + P02 * Cd * Cd
        tmp1 = Phi + Decimal(math.atan((Uo - x) / Fx))
        Scor = (Bmm * Decimal(math.tan(tmp1)) + M) / Fxcor
        Num = Scor * Bmm + (Scor - M * BP1)
        Den = Bmm + (M - Scor)*(BP2 * Decimal(math.cos(alpha)) +
                                BP3*Decimal(math.sin(alpha)))
        world_S = Num/Den

        if world_S < 5000:
            world_ds.append([world_degree, world_S])
            # convert to world coordinates in x-y
            world_x = (world_S) * Decimal(math.cos(world_degree))
            world_y = (world_S) * Decimal(math.sin(world_degree))
            world_xy.append([world_x, world_y])
        else:
            pass

    return world_xy

# end of TransformCoordinates function


class CalculateThread (Thread):
    tag_result = []

    def __init__(self, threadID, threadName, param_file, rawdata_file, timetag):
        Thread.__init__(self)
        self.threadID = threadID
        self.threadName = threadName
        self.param_file = param_file
        self.rawdata_file = rawdata_file
        self.timetag = timetag
        self.pcloud_xy = []

    def run(self):
        #print('processing ' + self.rawdata_file + '...')
        self.pcloud_xy = TransformCoordinates(
            self.param_file, self.rawdata_file, self.timetag)

    def get_result(self):
        try:
            return self.pcloud_xy
        except Exception:
            return None

#PointCloud_xy = GetCoordinates(param_files,rawdata_path,DataIndex)

def CalcSampleCoordinates(param_file,subdir):
    pcloud = []
    start_tags = []
    end_tags = []
    tag_start = 0
    tag_end = 10000000000
    sample_files = getFiles(subdir, '.csv')
    for sample_file in sample_files:
        ws = csv.reader(open(sample_file, 'r'))
        row = list(ws)
        lines = len(row)
        if lines > 0:
            start_tags.append(int(row[0][1]))
            end_tags.append(int(row[lines-1][1]))

    for tag in start_tags:
        if tag > tag_start:
            tag_start = tag

    for tag in end_tags:
        if tag < tag_end:
            tag_end = tag    

    #TODO: search for nearby samples for sufficient data
    #sample_tag = tag_start

    for sample_file in sample_files: 
        pcloud.extend(TransformCoordinates(param_file, sample_file, tag_start))

    return pcloud

class CoordinatesCalculator:
    
    start_tags = []
    end_tags = []
    tag_start = 0
    tag_end = 1000000000
    current_tag = 0
    param_file = ''
    rawdata_path = ''
    raw_files = []

    def __init__(self, param_file, rawdata_path):
        global PointCloud_xy
        self.param_file = param_file
        self.rawdata_path = rawdata_path
        self.raw_files = getFiles(rawdata_path, '.csv')
        CoordinatesCalculator.tag_start = 0
        CoordinatesCalculator.tag_end = 1000000000
        CoordinatesCalculator.tag_start = 0
        CoordinatesCalculator.start_tags = []
        CoordinatesCalculator.end_tags = []
        for raws in self.raw_files:
            ws = csv.reader(open(raws, 'r'))

            row = list(ws)
            lines = len(row)
            if lines > 0:
                CoordinatesCalculator.start_tags.append(int(row[0][1]))
                CoordinatesCalculator.end_tags.append(int(row[lines-1][1]))

        for tag in CoordinatesCalculator.start_tags:
            if tag > CoordinatesCalculator.tag_start:
                CoordinatesCalculator.tag_start = tag

        for tag in CoordinatesCalculator.end_tags:
            if tag < CoordinatesCalculator.tag_end:
                CoordinatesCalculator.tag_end = tag

        CoordinatesCalculator.current_tag = CoordinatesCalculator.tag_start
        PointCloud_xy = []

    def calc_step(self, step):
        if (CoordinatesCalculator.current_tag + step) >= CoordinatesCalculator.tag_start and (CoordinatesCalculator.current_tag + step) < CoordinatesCalculator.tag_end:
            CoordinatesCalculator.current_tag += step
        elif (CoordinatesCalculator.current_tag + step) < CoordinatesCalculator.tag_start:
            CoordinatesCalculator.current_tag = CoordinatesCalculator.tag_start
        elif (CoordinatesCalculator.current_tag + step) > CoordinatesCalculator.tag_end:
            CoordinatesCalculator.current_tag = CoordinatesCalculator.tag_end

        threads = []
        for idx in range(0, len(self.raw_files)):
            thread_name = 'ProcessThread' + str(idx)
            threads.append(CalculateThread(idx,thread_name, self.param_file,self.raw_files[idx],CoordinatesCalculator.current_tag))
            threads[idx].start()

        for th in threads:
            th.join()
            PointCloud_xy.extend(th.get_result())

    def calc_shift(self, shift):
        if shift < CoordinatesCalculator.tag_end - CoordinatesCalculator.tag_start :
            threads = []
            for idx in range(0,len(self.raw_files)):
                thread_name = 'ProcessThread' + str(idx)
                threads.append(CalculateThread(idx,thread_name, self.param_file,self.raw_files[idx],CoordinatesCalculator.tag_start+shift))
                threads[idx].start()

            
            for th in threads:
                th.join()
                PointCloud_xy.extend(th.get_result())


#main entry
rawdata_path = os.getcwd() + '\\samples\\'
result_path = os.getcwd() + '\\result\\'
cfg_path = os.getcwd()

param_file = getFiles(cfg_path, 'Config.ini')
enable_outfile = 0
mode_str = 'gui'
verbose_mode = 0
select_boxes = []

# get args
for idx in range(1, len(sys.argv)):
    if sys.argv[idx] == '-o' and idx < len(sys.argv):
        # enable output file
        enable_outfile = 1
    
    if sys.argv[idx] == '-m' and idx < len(sys.argv):
        #enable gui mode
        mode_str = sys.argv[idx+1]      #mode = gui/auto/shock

    if sys.argv[idx] == '-g':
        # enable gui mode
        gui_mode = 1

    if sys.argv[idx] == '-v':  # verbose mode for debug
        # enable verbose mode
        verbose_mode = 1

    if sys.argv[idx] == '-i' and idx < len(sys.argv):  # verbose mode for debug
        # get interval
        time_step = int(sys.argv[idx+1])

    if sys.argv[idx] == '-b' and idx < len(sys.argv):  # verbose mode for debug
        # enable verbose mode
        box_str = sys.argv[idx+1]
        box_coordinate = box_str.split(',')
        for idx in range(0,int(len(box_coordinate)/4)):
            select_boxes.append(SelectBox([int(box_coordinate[idx+0]),int(box_coordinate[idx+1]),int(box_coordinate[idx+2]),int(box_coordinate[idx+3])]))
        SelectBox.mode = 1      #external args mode

if verbose_mode == 1:
    print(param_file)



valid_length = 100000000

#save point-cloud data to csv file

# if enable_outfile == 1:
#     ds_result_file_path = result_path + 'ds_result_' + str(time_tag) + '.csv'
#     xy_result_file_path = result_path + 'xy_result_' + str(time_tag) + '.csv'
#     ds_file = open(ds_result_file_path, 'w', encoding='utf-8', newline='')
#     ds_writer = csv.writer(ds_file)
#     ds_writer.writerows(PointCloud_ds)
#     ds_file.close()
#     if verbose_mode == 1:
#         print('ds_result written!')

if mode_str == 'shock':
    cord_calc = CoordinatesCalculator(param_file, rawdata_path)
    time_tags = GetRawTagInfo(rawdata_path)
    first_tags = []
    last_tags = []
    for tag in time_tags:
        first_tags.append(tag[1])
        last_tags.append(tag[len(tag)-1])

    start_tag = 0
    for tag in first_tags:
        if int(tag) > start_tag:
            start_tag = int(tag)

    end_tag = 0
    for tag in last_tags:   
        if end_tag == 0:
            end_tag = int(tag)
        elif int(tag) < end_tag:
            end_tag = int(tag)

    if verbose_mode == 1:
        print('start_tag = ' + str(start_tag))
        print('end_tag = ' + str(end_tag))

    sample_numbers = int((end_tag - start_tag) / time_step)

    ds_item = []

    for sample_idx in range(0,sample_numbers):
        #calculate sample data
        PointCloud_xy = []  #clear point cloud data
        cord_calc.calc_shift(sample_idx*time_step)       #calculate new
        #calculate section intercept distance
        result_item=[]
        for box in select_boxes:
            S_intercept = calculate_intercept(PointCloud_xy,[[box.x1,box.y1],[box.x2,box.y2]])
            result_str = "Timeshift = " + str(sample_idx*time_step) + "  SelectBOX" + str(box.index) + "--Intercept = " + str(S_intercept)
            print(result_str)
            result_item.append("%.3f"%(S_intercept))
            
        ds_item.append([str(sample_idx*time_step),result_item[0],result_item[1]])

    ds_result_file_path = result_path + 'ds_result.csv'
    ds_file = open(ds_result_file_path,'w',encoding='utf-8',newline='')
    ds_writer = csv.writer(ds_file)
    ds_writer.writerow(['time_shift','intercept-box0','intercept-box1'])
    ds_writer.writerows(ds_item)
    ds_file.close()


elif mode_str == 'gui':
    cord_calc = CoordinatesCalculator(param_file, rawdata_path)
    cord_calc.calc_shift(0)
    pc_x = []
    pc_y = []
    for pt in PointCloud_xy:
        pc_x.append(pt[0])
        pc_y.append(pt[1])

    fig = plt.figure(figsize=(10, 10.5))
    plt.xlim(-5000, 5000)
    plt.ylim(-5000, 5000)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.plot(0, 0, "ob", ms=2, lw=2, color='green')
    #add lines for camera axis
    CAMParams = ReadCfg(param_file)
    for idx in range(0, CAMParams.__len__()):
        axis_angle = float(CAMParams[idx].Degree) * 3.1415926 / 180.0
        axis_pt_x = math.cos(axis_angle) * 5000
        axis_pt_y = math.sin(axis_angle) * 5000
        label_str = 'CAM' + str(idx+1)
        #plt.plot([0,0], [axis_pt_x, axis_pt_y],'b-.',label=label_str,lw=0.5, alpha=0.5)
        plt.plot([0,axis_pt_x], [0, axis_pt_y],label=label_str, lw=0.5, alpha=0.5, color='black')

    plt.plot(pc_x, pc_y, "ob", ms=0.1, lw=0.1)
    time_str = "  Timestamp = " + str(time_shift)

    if option_data_persist == 0:
        option_str = "  Data Persist = OFF"
    else:
        option_str = "  Data Persist = ON"

    title_info_str = time_str + option_str
    plt.title(title_info_str)   

    for box in select_boxes:
        plt.plot([box.xl, box.yh], [box.xh, box.yh],
                 lw=0.5, alpha=0.5, color='red')
        plt.plot([box.xh, box.yh], [box.xh, box.yl],
                 lw=0.5, alpha=0.5, color='red')
        plt.plot([box.xh, box.yl], [box.xl, box.yl],
                 lw=0.5, alpha=0.5, color='red')
        plt.plot([box.xl, box.yl], [box.xl, box.yh],
                 lw=0.5, alpha=0.5, color='red')

    else:
        fig.canvas.mpl_connect('button_press_event', on_press)
        fig.canvas.mpl_connect('button_release_event', on_release)
        fig.canvas.mpl_connect('motion_notify_event', on_mouse_motion)
        fig.canvas.mpl_connect('key_press_event', on_keypressed)
    #fig.canvas.mpl_connect('scroll_event', scroll_zoom)

    plt.show()

    print("wait for quit")

elif mode_str == 'gui_samples':
    subdirs = getSubdirs(rawdata_path)

    for subdir in subdirs:
        #PointCloud_xy = []
        pcloud = CalcSampleCoordinates(param_file, subdir)
        
        pc_x = []
        pc_y = []
        for pt in pcloud:
            pc_x.append(pt[0])
            pc_y.append(pt[1])
        
        fig = plt.figure(figsize=(10, 10.5))
        mngr = plt.get_current_fig_manager()
        mngr.window.wm_geometry("+100+100")
        plt.xlim(-5000, 5000)
        plt.ylim(-5000, 5000)

        plt.gca().set_aspect('equal', adjustable='box')
        plt.plot(0, 0, "ob", ms=2, lw=2, color='green') 
        #add lines for camera axis
        CAMParams = ReadCfg(param_file)
        for idx in range(0, CAMParams.__len__()):
            axis_angle = float(CAMParams[idx].Degree) * 3.1415926 / 180.0
            axis_pt_x = math.cos(axis_angle) * 5000
            axis_pt_y = math.sin(axis_angle) * 5000
            label_str = 'CAM' + str(idx+1)
            #plt.plot([0,0], [axis_pt_x, axis_pt_y],'b-.',label=label_str,lw=0.5, alpha=0.5)
            plt.plot([0,axis_pt_x], [0, axis_pt_y],label=label_str, lw=0.5, alpha=0.5, color='black')

        dots = plt.plot(pc_x, pc_y, "ob", ms=0.1, lw=0.1)
        dir_names=subdir.split('\\')

        time_str = "  Timestamp = " + dir_names[len(dir_names)-1]

        title_info_str = time_str 
        plt.title(title_info_str)   

        fig.canvas.mpl_connect('button_press_event', on_press)
        fig.canvas.mpl_connect('button_release_event', on_release)
        fig.canvas.mpl_connect('motion_notify_event', on_mouse_motion)
        fig.canvas.mpl_connect('key_press_event', on_keypressed)
        #fig.canvas.mpl_connect('scroll_event', scroll_zoom)

        plt.show()
       
        print("wait for quit")