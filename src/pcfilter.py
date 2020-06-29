import numpy as np
import math
import os
import csv
import ellipsefitting as elfit

fig = []


def SaveToDataFile(pcloud_in,filename):

    file_to_write = open(filename,'w',encoding='utf8',newline='')
    writer = csv.writer(file_to_write)
    writer.writerows(pcloud_in)

    file_to_write.close()

def FittingEllipse(pcloud_xy):
    [Xc,Yc,MA,SMA,Theta] = elfit.fit(pcloud_xy)
    return [Xc,Yc,MA,SMA,Theta]


def GetDeviarationPolar(pcloud_in, search_range):
    data_out = []
    for idx,pt in enumerate(pcloud_in):
        if idx < search_range:
            continue
        if len(pcloud_in) - idx < search_range:
            continue
        else:
            nearby_pts = pcloud_in[idx - search_range : idx + search_range]
            sum = 0.0
            for npt in nearby_pts:
                sum += float(npt[0])
            avg = sum / (search_range*2)
            deviaration = float(pt[0]) - avg
            data_out.append([deviaration,pt[1]])
    return data_out


def GlobalDeviationFilterPolar(pcloud_polar,deviation_list,threshold):
    data_out = []
    for idx,pt in enumerate(pcloud_polar): 
        if abs(deviation_list[idx][0]) <= threshold:
            data_out.append(pt)

    return data_out

def GlobalDeviationFilterPolarPro(pcloud_polar,deviation_list,threshold):
    data_out = []
    tmp_list = []
    # merge list
    for idx,pt in enumerate(pcloud_polar): 
        item = [float(pt[0]),abs(deviation_list[idx][0]),float(pt[1])]
        tmp_list.append(item)

    tmp_list.sort(key=takeSecond) 

    if threshold > 1.0:
        threshold = 1.0

    if threshold < 0:
        threshold = 0

    total_pt = len(tmp_list)
    valid_pt = int(total_pt * threshold)

    tmp_list = tmp_list[0:valid_pt -1]

    for item in tmp_list:
        data_out.append([item[0],item[2]])
    return data_out


def LocalDeviationFilterPolar(pcloud_in, search_range,threshold):
    data_out = []
    for idx,pt in enumerate(pcloud_in):
        if idx < search_range:
            nearby_pts = pcloud_in[0 : idx + search_range]
            sum = 0.0
            for npt in nearby_pts:
                sum += float(npt[0])
            avg = sum / (search_range*2)
            deviaration = float(pt[0]) - avg
            if math.fabs(deviaration) < threshold:
                data_out.append([pt[0],pt[1]])

        if len(pcloud_in) - idx < search_range:
            nearby_pts = pcloud_in[idx - search_range : len(pcloud_in) - 1]
            sum = 0.0
            for npt in nearby_pts:
                sum += float(npt[0])
            avg = sum / (search_range*2)
            deviaration = float(pt[0]) - avg
            if math.fabs(deviaration) < threshold:
                data_out.append([pt[0],pt[1]])

        else:
            nearby_pts = pcloud_in[idx - search_range : idx + search_range]
            sum = 0.0
            for npt in nearby_pts:
                sum += float(npt[0])
            avg = sum / (search_range*2)
            deviaration = float(pt[0]) - avg
            if math.fabs(deviaration) < threshold:
                data_out.append([pt[0],pt[1]])

    return data_out

def ClusterFilterPolar(pcloud_in, idx_range, radius, threshold):
    pcloud_out = []

    for idx,pt in enumerate(pcloud_in):
        if idx < idx_range:
            continue
        if len(pcloud_in) - idx < idx_range:
            continue
        else:
            nearby_pts = pcloud_in[idx - idx_range : idx + idx_range]
            cnt_inrange = 0
            for npt in nearby_pts:
                x_pt = float(pt[0])
                y_pt = float(pt[1])
                x_npt = float(npt[0])
                y_npt = float(npt[1])
                distance = math.sqrt((x_pt-x_npt)**2 + ((y_pt - y_npt)*1000)**2)
                if distance < radius:
                    cnt_inrange += 1
            if cnt_inrange > threshold:
                pcloud_out.append(pt)
                
    return pcloud_out


def ClusterFilterXY(pcloud_in, idx_range, radius, threshold):
    pcloud_out = []

    for idx,pt in enumerate(pcloud_in):
        if idx < idx_range:
            pass
        if len(pcloud_in) - idx < idx_range:
            pass
        else:
            nearby_pts = pcloud_in[idx - idx_range : idx + idx_range]
            cnt_inrange = 0
            for npt in nearby_pts:
                x_pt = float(pt[0])
                y_pt = float(pt[1])
                x_npt = float(npt[0])
                y_npt = float(npt[1])
                distance = math.sqrt((x_pt-x_npt)**2 + (y_pt - y_npt)**2)
                if distance < radius:
                    cnt_inrange += 1
            if cnt_inrange > threshold:
                pcloud_out.append(pt)
                
    return pcloud_out

def takeFirst(elem):
    return elem[0]

def takeSecond(elem):
    return elem[1]


def ProcessXY(pcloud_in,center,id_str):

    dir_path = os.getcwd() + '\\intermidiate\\' + id_str + '\\'
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    # SaveToDataFile(pcloud_in, dir_path +'0_pcloud_xy_origin.csv')

    pcloud_pol_work = ConvertXY2Polar(pcloud_in,center)
    SaveToDataFile(pcloud_pol_work, dir_path + '1_pcloud_pol_origin.csv')

    print('using AverageFilter...')
    pcloud_pol_work = AvgFilterPolar(pcloud_pol_work,9)
    #SaveToDataFile(pcloud_pol_work, dir_path + '2_pcloud_pol_avgf.csv')

    print('using ClusterFilter...')
    pcloud_pol_work = ClusterFilterPolar(pcloud_pol_work, 40, 50, 50)
    #SaveToDataFile(pcloud_pol_work, dir_path + '3_pcloud_pol_clust1.csv')

    print('using DeviationFilter...')
    pcloud_pol_work = LocalDeviationFilterPolar(pcloud_pol_work, 30, 10)
    #SaveToDataFile(pcloud_pol_work, dir_path + '4_pcloud_pol_deviat1.csv')

    print('using ClusterFilter 2nd round...')
    pcloud_pol_work =  ClusterFilterPolar(pcloud_pol_work, 50, 50, 50)
    # SaveToDataFile(pcloud_pol_work, dir_path + '5_pcloud_pol_clust2.csv')

    print('using DeviationFilter 2nd round...')
    pcloud_pol_work = LocalDeviationFilterPolar(pcloud_pol_work, 200, 10)
    SaveToDataFile(pcloud_pol_work, dir_path + '6_pcloud_pol_deviat2.csv')

    print('using GlobalMCCFilter...')
    pcloud_pol_work = MCCFilterPolar(pcloud_pol_work, [0.0,0.92])
    SaveToDataFile(pcloud_pol_work, dir_path + '7_pcloud_pol_mccf.csv')

    print('using ClusterFilter 3rd round...')
    pcloud_pol_work = ClusterFilterPolar(pcloud_pol_work, 50, 50, 50)
    SaveToDataFile(pcloud_pol_work, dir_path + '8_pcloud_pol_cluster3.csv')
    
    # print('First ellipse fitting using filtered data...')
    pcloud_xy_filtered = ConvertPolar2XY(pcloud_pol_work,center)
    SaveToDataFile(pcloud_xy_filtered, dir_path + '8_pcloud_xy_filtered.csv')

    return pcloud_xy_filtered


def EllipseFormationPolar(theta_in,ellipse_param):
    [Xc,Yc,MA,SMA,delta_Theta] = ellipse_param

    if isinstance(theta_in,float):
        defr = SMA**2 + MA**2 + (SMA**2 - MA**2)*math.cos(2*(theta_in - delta_Theta + math.pi/2))
        rho = math.sqrt(2*MA**2 *SMA**2 /defr)
        return rho
    elif isinstance(theta_in,str):  
        defr = SMA**2 + MA**2 + (SMA**2 - MA**2)*math.cos(2*(float(theta_in) - delta_Theta + math.pi/2))
        rho = math.sqrt(2*MA**2 *SMA**2 /defr)
        return rho          
    elif isinstance(theta_in,list):
        rho_list = []
        for theta in theta_in:
            defr = SMA**2 + MA**2 + (SMA**2 - MA**2)*math.cos(2*(theta - delta_Theta + math.pi/2))
            rho = math.sqrt(2*MA**2 *SMA**2 /defr)
            rho_list.append(rho)
        return rho_list
    else:
        return None

def GenerateEllipseDataListPolar(ellipse_param,theta_list):
    result = []
    for theta in theta_list:
        rho = EllipseFormationPolar(theta,ellipse_param)
        result.append([rho,theta])
    
    return result

def GetEllipseFittingDeviationPolar(ellipse_param,pcloud_in):
    
    theta_list = []
    result_list = []
    for pt in pcloud_in:
        theta_list.append(float(pt[1]))  

    elli_list = GenerateEllipseDataListPolar(ellipse_param,theta_list) 

    for idx,pt in enumerate(pcloud_in):
        divar = float(pt[0]) -  elli_list[idx][0]
        result_list.append([divar,float(pt[1])]) 

    return result_list

def CalcFittingCost(ellipse_param,pcloud_in):
    deviation_list = GetEllipseFittingDeviationPolar(ellipse_param,pcloud_in) 
    sum = 0.0
    dev_sum = 0.0
    sq_sum = 0.0
    avg = 0.0
    num = len(deviation_list)

    for dev in deviation_list:
        sum += dev[0]
        dev_sum += abs(dev[0])
        sq_sum += dev[0] **2

    avg = sum / num
    sdev = dev_sum / num
    sqdev = math.sqrt(sq_sum)

    return [avg,sdev,sqdev]



def FineFittingEllipse(pcloud_in,ellipse_param,id_str):
    

    dir_path = os.getcwd() + '\\intermidiate\\' + id_str + '\\'
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    # SaveToDataFile(pcloud_in, dir_path +'20_pcloud_xy_origin.csv')

    [Xc,Yc,MA,SMA,Theta] = ellipse_param

    # PC_work_xy = ConvertPolar2XY(PointCloud_pol,[0,0])
    PC_work_xy = pcloud_in
    filtered_list = ConvertXY2Polar(pcloud_in,[Xc,Yc])
    Result = []
    for i in range(0,5):
        theta_list = []
        samples = 0
        PC_work_pol = filtered_list
        for pt in PC_work_pol:
            theta_list.append(float(pt[1]))
            samples += 1

        print('Fitting round{:d}...'.format(i))
        [Xc,Yc,MA,SMA,delta_Theta] = FittingEllipse(PC_work_xy)
        print([Xc,Yc,MA*2,SMA*2,delta_Theta])
        ellipse_param = [Xc,Yc,MA,SMA,delta_Theta * math.pi / 180.0]

        #generate ellipse data
        elli_list = GenerateEllipseDataListPolar(ellipse_param,theta_list)

        #calculate deviation
        deviation_list = GetEllipseFittingDeviationPolar(ellipse_param,PC_work_pol)

        file_to_write = open(dir_path+ 'deviation_-bef_rnd'+ str(i) +'.csv','w',encoding='utf8',newline='')
        writer = csv.writer(file_to_write)
        writer.writerows(deviation_list)
        file_to_write.close()
        #calculate cost
        cost = CalcFittingCost(ellipse_param,PC_work_pol)
        print('Cost of round{:d} before filtering...'.format(i))
        print(cost)

        # using deviation filter based on probability
        filtered_list = GlobalDeviationFilterPolarPro(PC_work_pol,deviation_list,0.90)

        # re-calc deviation
        deviation_list = GetEllipseFittingDeviationPolar(ellipse_param,filtered_list)
        # re-calc cost
        cost = CalcFittingCost(ellipse_param,filtered_list)
        print('Cost of round{:d} after filtering...'.format(i))
        print(cost)

        file_to_write = open(dir_path+ 'deviation_-aft_rnd'+ str(i) +'.csv','w',encoding='utf8',newline='')
        writer = csv.writer(file_to_write)
        writer.writerows(deviation_list)
        file_to_write.close()

        # save
        Result.append([i,samples,cost,ellipse_param])

        # convert to x-y coordinate
        PC_work_xy = ConvertPolar2XY(filtered_list,[Xc,Yc])

    return Result



def ConvertXY2Polar(pcloud_in, center):
    pcloud_rt = []
    xc = center[0]  # invert x to make curve continuous
    yc = center[1]
    # convert to polar coordinate, original is center
    for pt_xy in pcloud_in:
        x = float(pt_xy[0])
        y = float(pt_xy[1])
        rho = math.sqrt((x - xc)**2 + (y - yc)**2)
        if x == xc:
            if y > yc:
                theta = math.pi / 2
            else:
                theta = 3 * math.pi / 2

        else:
            theta = math.atan((y - yc) / (x - xc))  
            if x < xc:
                theta = theta + math.pi 
            elif x > xc and y < yc:
                theta = theta + 2*math.pi
                    
        
        pcloud_rt.append([rho,theta])
    return pcloud_rt

def ConvertPolar2XY(pcloud_in, center):
    pcloud_out = []

    xc = center[0]
    yc = center[1]

    for pt in pcloud_in:
        x = float(pt[0]) * math.cos(float(pt[1])) + xc  
        y = float(pt[0]) * math.sin(float(pt[1])) + yc
        pcloud_out.append([x,y])

    return pcloud_out   


def AvgFilterPolar(pcloud_in, window_size):
    pcloud_out = []
    pcloud_work = pcloud_in
    pcloud_work.sort(key=takeSecond)
    for idx,pt in enumerate(pcloud_work):
        if idx < window_size/2 or idx > len(pcloud_work) - window_size/2:
            #print(' ')
            pcloud_out.append(pt)
        else:
            window_list = pcloud_work[idx - int(window_size/2):idx + int(window_size)]
            window_list.sort(key=takeFirst)
            sum = 0.0
            for val in window_list:
                sum += val[0]
            rho_avg = sum / len(window_list)
            pcloud_out.append([rho_avg,pt[1]])
    
    return pcloud_out


def getDeviaration(pcloud_in, search_range):
    data_out = []
    for idx,pt in enumerate(pcloud_in):
        if idx < search_range:
            continue
        if len(pcloud_in) - idx < search_range:
            continue
        else:
            nearby_pts = pcloud_in[idx - search_range : idx + search_range]
            sum = 0.0
            for npt in nearby_pts:
                sum += float(npt[0])
            avg = sum / (search_range*2)
            deviaration = float(pt[0]) - avg
            data_out.append([deviaration,pt[1]])
    return data_out


# Maximum Circumscribed Circle filter algorithm
def MCCFilterPolar(pcloud_in, thresholds):
    pcloud_out = []
    pcloud_rt = pcloud_in

    pcloud_rt.sort(key=takeSecond)
    # DisplayPolarData(pcloud_rt)

    # sort according to rho (distance to origin point)
    pcloud_rt.sort(key=takeFirst,reverse=True)

    if thresholds[0] > thresholds[1]:
        tmp = thresholds[0]
        thresholds[0] = thresholds[1]
        thresholds[1] = tmp
        
    if thresholds[0] >= 0 and thresholds[1] >0 and thresholds[0] < 1.0 and thresholds[1] <= 1.0:
        ptidx_high = int(len(pcloud_rt) * thresholds[1])
        ptidx_low = int(len(pcloud_rt) * thresholds[0])
        pcloud_rt = pcloud_rt[ptidx_low : ptidx_high]
    else:
        print('[ERR-MCCFilter]:invalid threshold value!')

    # DisplayPolarData(pcloud_rt)

    return pcloud_rt


