import numpy as np
import math
import pcfilter

def calculate_inbox(pc_xy, box):

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

    rho_avg = 0.0
    theta_avg = 0.0
    rho_sum = 0.0
    theta_sum = 0.0

    # select points in box range
    pt_sel_xy = []
    for pt in pc_xy:
        if pt[0] > topleft_x and pt[0] < botright_x and pt[1] > botright_y and pt[1] < topleft_y:
            pt_sel_xy.append([float(pt[0]),float(pt[1])])

    pt_polar = pcfilter.ConvertXY2Polar(pt_sel_xy,[0,0])

    for pt in pt_polar:
        rho_sum = rho_sum + pt[0]
        theta_sum = theta_sum + pt[1]

    if len(pt_polar) > 0:
        rho_avg = rho_sum/len(pt_polar)
        theta_avg = theta_sum/len(pt_polar)
  
    #print('distance = ' + str(distance))
    print("The Average of {} points.".format(len(pt_polar)))
    return [rho_avg,theta_avg]