import configparser
import os
import sys
import csv
from decimal import Decimal
import numpy as np
import math
import threading
import queue
from multiprocessing import cpu_count

pi = Decimal(3.1415926536)

class CameraParams:
    camera_count = 0
    BP1 = 0.0
    BP2 = 0.0
    BP3 = 0.0
    GDcor = Decimal('0.0')
    GRcor = Decimal('0.0')
    GHYcor = Decimal('0.0')
    bUsingGlocalDistCor = True

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
        self.Dcorb = Decimal('0.0')
        self.Dcork = Decimal('0.0')
        CameraParams.camera_count += 1

# end of class CameraParams definition



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
        key_name = name + 'Dcorb'
        CAMParams[idx-1].Dcorb = cfg.get('CameraParam', key_name)
        key_name = name + 'Dcork'
        CAMParams[idx-1].Dcork = cfg.get('CameraParam', key_name)

    CameraParams.BP1 = cfg.get('ParamDetail', 'BP1')
    CameraParams.BP2 = cfg.get('ParamDetail', 'BP2')
    CameraParams.BP3 = cfg.get('ParamDetail', 'BP3')

    CameraParams.GRcor = cfg.get('ParamDetail', 'GlobalRotateCorr')

    CameraParams.GDcor = cfg.get('ParamDetail', 'GlobalDistCorr')

    if cfg.get('ParamDetail', 'DistCorrUsing') == 'GLOBAL':
        CameraParams.bUsingGlocalDistCor = True
        
    else:
        CameraParams.bUsingGlocalDistCor = False


    CameraParams.GHYcor = cfg.get('ParamDetail', 'GlobalHorizonYawCorr')
    return CAMParams
    # end of ReadCfg()



def convert(param_file, rawdata_file, time_tag):
    # load camera params
    CAMParams = ReadCfg(param_file)

    cam_idx = 0
    #time_tags = []
    #BasicDegreeWorld = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    #BasicDegree = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
    BasicDegreeWorld = Decimal('0.0')
    BasicDegree = Decimal('0.0')

    # PCloud_ds = []
    PCloud_xy = []

    ws = csv.reader(open(rawdata_file, 'r'))
    #lines = ws.line_num()
    row = list(ws)

    # find the camera serial in the rawdata_file
    for idx in range(0, CAMParams.__len__()):
        if row[0][0] == CAMParams[idx].SerialNum:
            cam_idx = CAMParams[idx].position-1

    # initial degree value for each camera
    deg = Decimal(CAMParams[idx].Degree) + Decimal(CAMParams[idx].GRcor)
    BasicDegreeWorld = deg * pi / Decimal('180.0')
    BasicDegree = pi / Decimal('2.0') + BasicDegreeWorld

    CAMParams[cam_idx].bExist = 1

    # x-y coordinates of points in camera system for single camera
    cam_coordinates = []

    # these two list consists polar-coordinates of points in world system
    world_ds = []  # polar coordinates of points for single camera
    world_xy = []  # x-y of points in world system

    # load common params for single camera
    degree = (Decimal(CAMParams[cam_idx].Degree)+Decimal(CAMParams[cam_idx].GRcor)) * pi / Decimal(180)
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

    Dcorb = Decimal(CAMParams[cam_idx].Dcorb)
    Dcork = Decimal(CAMParams[cam_idx].Dcork)
    # search for time_tag
    index = 0
    for idx in range(0,len(row)-1):
        if idx <(len(row)-2) and abs(time_tag - int(row[idx][1])) < (int(row[idx+1][1]) - int(row[idx][1])):
            index = idx
    
    #if verbose_mode == 1:
    #    print('time_tag = ' + str(time_tag))          
    #    print('current idx = ' + str(index))    

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
        Num = Scor * Bmm + (Scor - M) * BP1
        Den = Bmm + (M - Scor)*(BP2 * Decimal(math.cos(alpha)) +
                                BP3*Decimal(math.sin(alpha)))
        
        # calculate static error for single camera
         
        # correct static error using global distance correction
        if CAMParams[cam_idx].bUsingGlocalDistCor:
            world_S = (Num/Den) + Decimal(CAMParams[cam_idx].GDcor)

        else:
            origin_S = Num/Den
            world_S = origin_S + (origin_S * Dcork + Dcorb)

        if world_S > 2000 and world_S < 5000:
            world_ds.append([world_degree, world_S])

            # calculate horizon yaw correction
            ghy_rad = Decimal(CAMParams[cam_idx].GHYcor) * pi / Decimal(180)            
            ghy_corr = Decimal(math.cos(ghy_rad))
            # convert to world coordinates in x-y
            world_x = (world_S) * Decimal(math.cos(world_degree))
            world_y = (world_S) * Decimal(math.sin(world_degree)) * ghy_corr
            world_xy.append([world_x, world_y])
        else:
            pass

    return world_xy


def ConvertMultiSections(param_file, rawdata_file, time_tags):
    # load camera params
    CAMParams = ReadCfg(param_file)

    cam_idx = 0

    BasicDegreeWorld = Decimal('0.0')
    BasicDegree = Decimal('0.0')

    PCloud_xy = []

    ws = csv.reader(open(rawdata_file, 'r'))
    rows = list(ws)

    # find the camera serial in the rawdata_file
    for idx in range(0, CAMParams.__len__()):
        if rows[0][0] == CAMParams[idx].SerialNum:
            cam_idx = CAMParams[idx].position-1

    # initial degree value for each camera
    #deg = Decimal(CAMParams[cam_idx].Degree) + Decimal(CAMParams[cam_idx].GRcor)
    #BasicRadianWorld = deg * pi / Decimal('180.0')

    #BasicRadian = pi / Decimal('2.0') + BasicRadianWorld
    # BasicRadian =  BasicRadianWorld

    CAMParams[cam_idx].bExist = 1

    # x-y coordinates of points in camera system for single camera
    # cam_coordinates = []

    # these two list consists polar-coordinates of points in world system
    # world_ds = []  # polar coordinates of points for single camera
    world_xys = []  # x-y-s of points in world system

    # load common params for single camera
    radian = (Decimal(CAMParams[cam_idx].Degree)+Decimal(CAMParams[cam_idx].GRcor)) * pi / Decimal(180)
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
    Dcorb = Decimal(CAMParams[cam_idx].Dcorb)
    Dcork = Decimal(CAMParams[cam_idx].Dcork)

    # search for time_tag
    point_cnt = 0
    for idx,row in enumerate(rows):
        if int(row[1]) in time_tags:
            #read raw data from csv
            point_cnt += 1
            print('.',end='')
            for col in range(2,len(row),2):
                cam_x = row[col]         #get x cam-coordinate of a point
                cam_y = str((col / 2)-1)    #get y cam-coordinate of a point
                # cam_coordinates.append([cam_x,cam_y])       #add to cam-coordinate list

                x = Decimal(cam_x)          #convert string to decimal
                y = Decimal(cam_y)

                # convert to world coordinates in polar
                Cd = Decimal(math.atan((Vo - y)/Fy))
                Ay = K00 + K10 * Cd + K01 * x + K11 * Cd * x + K02 * x * x

                world_radian = radian + Ay

                alpha = radian + Ay
                Fxcor = P00 + P10 * x + P01 * Cd + P20 * x * x + P11 * Cd * x + P02 * Cd * Cd
                tmp1 = Phi + Decimal(math.atan((Uo - x) / Fx))
                Scor = (Bmm * Decimal(math.tan(tmp1)) + M) / Fxcor
                Num = Scor * Bmm + (Scor - M) * BP1
                Den = Bmm + (M - Scor)*(BP2 * Decimal(math.cos(alpha)) +
                                        BP3*Decimal(math.sin(alpha)))
                
                # correct static error using global distance correction
                if CAMParams[cam_idx].bUsingGlocalDistCor:
                    world_S = (Num/Den) + Decimal(CAMParams[cam_idx].GDcor)

                else:
                    origin_S = Num/Den
                    world_S = origin_S + (origin_S * Dcork + Dcorb)

                if world_S > 2000 and world_S < 5000:
                    # world_ds.append([world_radian, world_S])
                    # convert to world coordinates in x-y
                    world_x = round(float((world_S) * Decimal(math.cos(world_radian))),3)
                    world_y = round(float((world_S) * Decimal(math.sin(world_radian))),3)
                    world_xys.append([[world_x, world_y],int(row[1])])
                else:
                    pass
    print('\n{:d} points processed..'.format(point_cnt))
    return world_xys

# end of TransformCoordinates function

def ConvertOneSection(CAMParams,cam_idx,rawdata_row):
    world_xys = []
    BasicDegreeWorld = Decimal('0.0')
    BasicDegree = Decimal('0.0')
    # load common params for single camera
    radian = (Decimal(CAMParams[cam_idx].Degree)+Decimal(CAMParams[cam_idx].GRcor)) * pi / Decimal(180)
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
    Dcorb = Decimal(CAMParams[cam_idx].Dcorb)
    Dcork = Decimal(CAMParams[cam_idx].Dcork)

    
    for col in range(2,len(rawdata_row),2):
        cam_x = rawdata_row[col]         #get x cam-coordinate of a point
        cam_y = str((col / 2)-1)    #get y cam-coordinate of a point
        # cam_coordinates.append([cam_x,cam_y])       #add to cam-coordinate list

        x = Decimal(cam_x)          #convert string to decimal
        y = Decimal(cam_y)

        # convert to world coordinates in polar
        Cd = Decimal(math.atan((Vo - y)/Fy))
        Ay = K00 + K10 * Cd + K01 * x + K11 * Cd * x + K02 * x * x

        world_radian = radian + Ay

        alpha = radian + Ay
        Fxcor = P00 + P10 * x + P01 * Cd + P20 * x * x + P11 * Cd * x + P02 * Cd * Cd
        tmp1 = Phi + Decimal(math.atan((Uo - x) / Fx))
        Scor = (Bmm * Decimal(math.tan(tmp1)) + M) / Fxcor
        Num = Scor * Bmm + (Scor - M) * BP1
        Den = Bmm + (M - Scor)*(BP2 * Decimal(math.cos(alpha)) +
                                BP3*Decimal(math.sin(alpha)))
        
        # correct static error using global distance correction
        if CAMParams[cam_idx].bUsingGlocalDistCor:
            world_S = Num/Den + Decimal(CAMParams[cam_idx].GDcor)
        else:
            #world_S = Num/Den + CAMParams[cam_idx].Dcor
            origin_S = Num/Den
            world_S = origin_S + (origin_S * Dcork +Dcorb )

        if world_S > 2000 and world_S < 5000:
            # world_ds.append([world_radian, world_S])

            # calculate horizon yaw correction
            ghy_rad = Decimal(CAMParams[cam_idx].GHYcor) * pi / Decimal(180)            
            ghy_corr = Decimal(math.cos(ghy_rad))

            # convert to world coordinates in x-y
            world_x = round(float((world_S) * Decimal(math.cos(world_radian))),3)
            world_y = round(float((world_S) * Decimal(math.sin(world_radian))* ghy_corr),3) 
            world_xys.append([[world_x, world_y],int(rawdata_row[1])])
        else:
            pass
    return world_xys


class ConvertThread (threading.Thread):
    def __init__(self, threadID, q, param, cam_idx):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.q = q
        self.param = param
        self.cam_idx = cam_idx
        # these two list consists polar-coordinates of points in world system
        self.world_xys = []  # x-y-s of points in world system

    def run(self):
        CAMParams = self.param
        cam_idx = self.cam_idx
        while True:
            queueLock.acquire()
            if not self.q.empty():
                rawdata_row = self.q.get()
                queueLock.release()
                # print('Thread'+ self.threadID + 'processing...')
                self.world_xys.extend(ConvertOneSection(CAMParams,cam_idx,rawdata_row))
                print ('.',end='')
            else:
                queueLock.release()
                print('\nThread '+ str(self.threadID) + ' process complete...')
                break

    def getResult(self):
        return self.world_xys

queueLock = threading.Lock()

def ConvertMultiSectionsMultiThreading(param_file, rawdata_file, time_tags):
    # load camera params
    CAMParams = ReadCfg(param_file)

    cam_idx = 0

    PCloud_xy = []

    print('Reading rawfile: '+ rawdata_file)
    ws = csv.reader(open(rawdata_file, 'r'))
    rows = list(ws)
    print('Start processing...')
    # find the camera serial in the rawdata_file
    for idx in range(0, CAMParams.__len__()):
        if rows[0][0] == CAMParams[idx].SerialNum:
            cam_idx = CAMParams[idx].position-1

    CAMParams[cam_idx].bExist = 1

    # search for time_tag
    point_cnt = 0
    
    max_thread = cpu_count() - 1
    #max_thread = 1

    # queueLock = threading.Lock()
    WorkQueue = queue.Queue(len(time_tags))
    Threads = []
    point_cnt = len(time_tags)
    queueLock.acquire()
    for idx,row in enumerate(rows):
        if int(row[1]) in time_tags:
            WorkQueue.put(row)
    queueLock.release()

    for cnt in range(0,max_thread):
        th=ConvertThread(cnt,WorkQueue,CAMParams,cam_idx)
        th.start()
        Threads.append(th) 

    while not WorkQueue.empty():
        pass   

    for t in Threads:
        t.join()
        PCloud_xy.extend(t.getResult())

    print('\n{:d} points processed..'.format(point_cnt))
    return PCloud_xy