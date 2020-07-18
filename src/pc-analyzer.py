import os,getopt
import sys
import configparser
import csv
from decimal import Decimal
import numpy as np
import math
import matplotlib.pyplot as plt
import camraw2xy
import pcfilter
import linefit
import weight_center

# import cv2 as cv
# import ellipsefitting as elfit
from matplotlib.patches import Ellipse

select_boxes = []
select_pts = []
highlight_pts = []
pc_filtered = []
fitline = []
title_str = ''
function_mode = ''
filename = ''
filter_thresholds = [0.05,0.2]
select_enable = True

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


def getFiles(path, suffix):
    return [os.path.join(root, file) for root, dirs, files in os.walk(path) for file in files if file.endswith(suffix)]




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
    global select_enable
    if event.button==1 and select_enable:   #鼠标左键点击
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
    global pc_filtered
    # global select_pts
    # global highlight_pts
    global function_mode
    global select_enable
    global fitline

    if event.button == 1 and select_enable:  # 鼠标左键释放
        if function_mode == 'fitline':
            if select_boxes[SelectBox.box_count-1].finished == 0:
                select_boxes[SelectBox.box_count-1].x2 = event.xdata
                select_boxes[SelectBox.box_count-1].y2 = event.ydata
                select_boxes[SelectBox.box_count-1].finished = 1
                print("add box end position:", event.button,
                    event.xdata, event.ydata)

                # processing data
                for box in select_boxes:
                    [S_intercept,poly_coef] = linefit.calculate_intercept(
                        pc_filtered, [[box.x1, box.y1], [box.x2, box.y2]])

                    poly_fit = np.poly1d(poly_coef)
                    x = [-5000, 5000]
                    
                    fitline.append(plt.gca().plot(x, poly_fit(
                        x), lw=0.5, alpha=0.5, color='green'))
                    plt.gca().figure.canvas.draw()

                    result_string = filename + "  Intercept = {:.3f}".format(S_intercept)
                    plt.title(result_string)
                    plt.gca().figure.canvas.draw()
                    if SelectBox.box_count > 0:
                        select_boxes.pop()
                        # print('select_box_count='+str(SelectBox.box_count))
                    print(result_string)

        elif function_mode == 'weight_center':
            if select_boxes[SelectBox.box_count-1].finished == 0:
                select_boxes[SelectBox.box_count-1].x2 = event.xdata
                select_boxes[SelectBox.box_count-1].y2 = event.ydata
                select_boxes[SelectBox.box_count-1].finished = 1
                #print("add box end position:", event.button,
                #    event.xdata, event.ydata)

                # processing data
                for box in select_boxes:

                    [rho_avg,theta_avg] = weight_center.calculate_inbox(pc_filtered, [[box.x1, box.y1], [box.x2, box.y2]])
                    result_string = filename + " polar coordinates of weight = {:.2f},{:.5f}".format(rho_avg,theta_avg)
                    plt.title(result_string)
                    pt_wc = pcfilter.ConvertPolar2XY([[rho_avg,theta_avg]],[0,0])
                    plt.scatter(pt_wc[0][0], pt_wc[0][1], c="r", marker='.', s=2) 
                    plt.gca().figure.canvas.draw()
                    if SelectBox.box_count > 0:
                        select_boxes.pop()
                        # print('select_box_count='+str(SelectBox.box_count))
                    print(result_string)

        elif function_mode == 'fitellipse':
            if select_boxes[SelectBox.box_count-1].finished == 0:
                select_boxes[SelectBox.box_count-1].x2 = event.xdata
                select_boxes[SelectBox.box_count-1].y2 = event.ydata
                select_boxes[SelectBox.box_count-1].finished = 1
                
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
                print("add box end position:", event.button,
                    event.xdata, event.ydata)
            
            


def getLongAxisLine(Xc,Yc,Theta):

    x_bias = 5000.0 * math.cos(math.pi * Theta / 180.0)
    y_bias = 5000.0 * math.sin(math.pi * Theta / 180.0)
    return [Xc - x_bias,Xc + x_bias,Yc - y_bias,Yc + y_bias]


def on_keypressed(event):
    global filter_thresholds
    global pc_filtered
    global select_boxes
    global select_pts
    global highlight_pts
    global filename
    global bShowBox
    #global axis_pt_x
    #global axis_pt_y
    global tims_str
    global select_enable
    boxes = []

    if event.key in " cxrb":
        if event.key == ' ':    #do ellipse fitting
            # processing data
            # add pts inside select_box to select_pts list
            plt.ion()
            if len(select_boxes) == 0:
                # select_pts = pc_filtered
                pcloud_xy_filtered = pcfilter.ProcessXY(pc_filtered,[0,0],tims_str)
            else:
                for box in select_boxes:
                    if box.finished == 1:
                        pts_to_add = SelectPts(pc_filtered, [[box.x1, box.y1], [box.x2, box.y2]])
                
                        for pt in pts_to_add:
                            pt_highlight,= plt.gca().plot(pt[0],pt[1],'ro', ms=1, lw=0.2)
                            highlight_pts.append(pt_highlight)

                        select_pts.extend(pts_to_add) 
                pcloud_xy_filtered = select_pts

            pc_x = []
            pc_y = []
            for pt in pcloud_xy_filtered:
                pc_x.append(float(pt[0]))
                pc_y.append(float(pt[1]))

            plt.scatter(pc_x, pc_y, c='r', marker='.', s=0.1)

            if function_mode == 'fitline':
                pass
            elif function_mode == 'range':
                pass
            elif function_mode == 'fitellipse':
                # start first ellipse fitting
                [Xc,Yc,MA,SMA,Theta] = pcfilter.FittingEllipse(pcloud_xy_filtered)
                print('First run ellipse fitting result:')
                print('Long Axis = {:.2f}'.format(MA*2))
                print('Short Axis = {:.2f}'.format(SMA*2))
                print('Center = ({:.2f},{:.2f})'.format(Xc,Yc))
                print('Theta(short axis angle) = {:.2f}'.format(Theta))
                print('')

                # second run fitting
                print('Second run ellipse fitting...')
                Result = pcfilter.FineFittingEllipse(pcloud_xy_filtered,[Xc,Yc,MA,SMA,Theta],tims_str + '_2')
                
                min_sdev = 10000
                best_idx = 0
                for idx,item in enumerate(Result):
                    if item[2][2] < min_sdev:
                        min_sdev = item[2][2]
                        best_idx = idx

                print('result of lease error is:')
                print(Result[best_idx])

                [Xc,Yc,MA,SMA,Theta] = Result[best_idx][3]
                print('Final ellipse fitting result:')
                print('Long Axis = {:.2f}'.format(MA*2))
                print('Short Axis = {:.2f}'.format(SMA*2))
                print('Center = ({:.2f},{:.2f})'.format(Xc,Yc))
                print('Theta(short axis angle) = {:.2f}'.format(Theta))
                print('')


                # display ellipse
                ell = Ellipse([Xc,Yc], MA*2,SMA*2, Theta + 90)
                ell.set_facecolor("white")
                ell.set_edgecolor("gray")
                ell.set_alpha(0.3)
                elle_patch = plt.gca().add_patch(ell)

                # plot center of ellipse
                elle_center_dot = plt.plot(Xc, Yc, "o", ms=1, lw=1, color='green')

                # plot long axis
                [ma_x1,ma_x2,ma_y1,ma_y2] = getLongAxisLine(Xc,Yc,Theta+90)
                elle_axis_line = plt.plot([ma_x1,ma_x2], [ma_y1, ma_y2],label='Long Axis', lw=0.5, alpha=0.8, linestyle="-.")



                # plt.gca().figure.canvas.draw()
                result_string = filename + '\n' + 'Long Axis = {:.2f}, Short Axis = {:.2f}'.format(MA*2,SMA*2)
                plt.title(result_string) 

            select_pts = []
            plt.ioff()

        if event.key == 'c':        #clear select points and curves
            for pt in highlight_pts:
                pt.remove()

            plt.gca().figure.canvas.draw()

        if event.key == 'x':        #clear select boxes
            for pt in highlight_pts:
                pt.remove()

        if event.key == 'b':        #show select_boxes
            if select_enable:
                select_enable = False
                result_string = 'Select Box OFF'
                
            else:
                select_enable = True
                result_string = 'Select Box ON'
            print(result_string)
            plt.title(result_string)                  



def SelectPts(pc_xy, box):
    pts_selected = []
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
  
        # select points in box range
    for pt in pc_xy:
        if float(pt[0]) > topleft_x and float(pt[0]) < botright_x and float(pt[1]) > botright_y and float(pt[1]) < topleft_y:
            pts_selected.append([round(float(pt[0]),2),round(float(pt[1]),2)])

    return pts_selected



# main entrance of this program

# execute only if run as a script
def main(argv):
    global pc_filtered
    global filter_thresholds
    global filename
    global select_pts
    global highlight_pts
    # silent_mode = False
    # auto_mode = False
    # verbose_mode = False
    write_result = False
    apply_prefilter = False
    global function_mode
    function_mode = ''
    mode_list = ['fitline','fitellipse','fitellipse_auto','nofit','weight_center']
    srd_dir = ''
    global tims_str
    num_to_process = 1000000

    help_str = '''
        'cs-analyzer.py -h -i -t <time_tag> -p [-l <section_length_in_ms> | -s <number_of_sections>]'
    '''
    try:
        opts, args = getopt.getopt(argv,"hsfvmwn:t:",["write_result","srcdir=","help","silent","verbose","filter","mode=","threshold="])
    except getopt.GetoptError:
        print(help_str)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_str)
            sys.exit()

        elif opt in ("-w","--write_result"):
            write_result = True

        elif opt in ("--srcdir"):
            srd_dir = arg

        # elif opt in ("-a", "--auto"):
        #     auto_mode = True

        # elif opt in ("-s", "--silent"):
        #     silent_mode = True

        # elif opt in ("-v", "--verbose"):
        #     verbose_mode = True

        elif opt in ("-f", "--filter"):
            apply_prefilter = True

        elif opt in ("-m", "--mode"):
            if arg in mode_list:
                function_mode = arg
        
        elif opt in ("-t","--threshold"):
            th_l,th_h = arg.split(',',1)
            filter_thresholds = [float(th_l),float(th_h)]

        elif opt in ("-n"):
            num_to_process = int(arg)
            

    pcloud_files = getFiles(os.getcwd()+'\\' + srd_dir,'.csv')
    cfg_file = getFiles(os.getcwd(),'Config.ini')

    if write_result:
        result_file = 'result.csv' 
        file_to_write = open(result_file,'w',encoding='utf8',newline='')
        writer = csv.writer(file_to_write)
        head = ['TIMG_TAG','LONG_AXIS','SHORT_AXIS','CENTER_X','CENTER_Y','THETA']
        writer.writerow(head)
        file_to_write.close()

    process_cnt = 0
    for pcf in pcloud_files:
        if not 'intermidiate' in pcf and not 'result' in pcf:
            if process_cnt >= num_to_process:
                break
            process_cnt += 1

            print('processing ' + pcf)
            select_pts = []
            highlight_pts = []
            bShowBox = False
            filename = os.path.basename(pcf)
            ws = csv.reader(open(pcf, 'r'))
            pc_xy = list(ws)
            PointCloud_xy = []
            for pt in pc_xy:
                PointCloud_xy.append([float(pt[0]),float(pt[1])])

            timetag,foo = filename.split('.csv')
            time_val = int(timetag)
            tims_str = '{:0>8d}'.format(time_val)

            # apply filter
            if apply_prefilter:
                pc_filtered = pcfilter.ClusterFilterXY(PointCloud_xy,15,15,15)
            else:
                pc_filtered = PointCloud_xy
            
            #pcfilter.SaveToDataFile(PointCloud_xy, 'pcloud_xy_origin.csv') 
            #pcfilter.SaveToDataFile(pc_filtered, 'pcloud_xy_prefiltered.csv') 

            pc_x = []
            pc_y = []
            for pt in pc_filtered:
                pc_x.append(float(pt[0]))
                pc_y.append(float(pt[1]))

            fig = plt.figure(figsize=(10, 10.5))
            
            plt.ion()

            if function_mode == 'fitline':
                plt.xlim(-4000, 4000)
                plt.ylim(-4000, 4000)
            else:
                plt.xlim(-3000, 3000)
                plt.ylim(-3000, 3000)

            plt.gca().set_aspect('equal', adjustable='box')

            plt.scatter(0, 0, c="g", marker='.', s=0.5) 
            #add lines for camera axis
            CAMParams = camraw2xy.ReadCfg(cfg_file)

            for idx in range(0, CAMParams.__len__()):
                axis_angle = (float(CAMParams[idx].Degree) + float(CAMParams[idx].GRcor)) * 3.1415926 / 180.0
                axis_pt_x = math.cos(axis_angle) * 5000
                axis_pt_y = math.sin(axis_angle) * 5000
                label_str = 'CAM' + str(idx+1)
                
                plt.plot([0,axis_pt_x], [0, axis_pt_y],label=label_str, lw=0.4, alpha=0.4)

            
            plt.scatter(pc_x, pc_y, c='b', marker='.', s=0.1)

            plt.title(filename)  
            plt.xlabel("X axis in milimeter") 
            plt.ylabel("Y axis in milimeter") 
            plt.legend()


            if function_mode in ['fitline','fitellipse','weight_center']:

                fig.canvas.mpl_connect('button_press_event', on_press)
                fig.canvas.mpl_connect('button_release_event', on_release)
                fig.canvas.mpl_connect('motion_notify_event', on_mouse_motion)
                fig.canvas.mpl_connect('key_press_event', on_keypressed)

                plt.ioff()
                plt.show()

            elif function_mode == 'fitellipse_auto':
                # auto mode
                plt.ion()
                pcloud_xy_filtered = pcfilter.ProcessXY(pc_filtered,[20,0],tims_str)
                pc_x = []
                pc_y = []
                for pt in pcloud_xy_filtered:
                    pc_x.append(float(pt[0]))
                    pc_y.append(float(pt[1]))

                plt.scatter(pc_x, pc_y, c='r', marker='.', s=0.1)

                # start first ellipse fitting
                [Xc,Yc,MA,SMA,Theta] = pcfilter.FittingEllipse(pcloud_xy_filtered)
                print('First run ellipse fitting result:')
                print('Long Axis = {:.2f}'.format(MA*2))
                print('Short Axis = {:.2f}'.format(SMA*2))
                print('Center = ({:.2f},{:.2f})'.format(Xc,Yc))
                print('Theta(short axis angle) = {:.2f}'.format(Theta))
                print('')


                # second run fitting
                print('Second run ellipse fitting...')
                Result = pcfilter.FineFittingEllipse(pcloud_xy_filtered,[Xc,Yc,MA,SMA,Theta],tims_str + '_2')
                
                min_sdev = 10000
                best_idx = 0
                for idx,item in enumerate(Result):
                    if item[2][2] < min_sdev:
                        min_sdev = item[2][2]
                        best_idx = idx

                print('result of lease error is:')
                print(Result[best_idx])

                [Xc,Yc,MA,SMA,Theta] = Result[best_idx][3]
                print('Final ellipse fitting result:')
                print('Long Axis = {:.2f}'.format(MA*2))
                print('Short Axis = {:.2f}'.format(SMA*2))
                print('Center = ({:.2f},{:.2f})'.format(Xc,Yc))
                print('Theta(short axis angle) = {:.2f}'.format(Theta))
                print('')


                # display ellipse
                ell = Ellipse([Xc,Yc], MA*2,SMA*2, Theta + 90)
                ell.set_facecolor("white")
                ell.set_edgecolor("gray")
                ell.set_alpha(0.3)
                elle_patch = plt.gca().add_patch(ell)

                # plot center of ellipse
                elle_center_dot = plt.plot(Xc, Yc, "o", ms=1, lw=1, color='green')

                # plot long axis
                [ma_x1,ma_x2,ma_y1,ma_y2] = getLongAxisLine(Xc,Yc,Theta+90)
                elle_axis_line = plt.plot([ma_x1,ma_x2], [ma_y1, ma_y2],label='Long Axis', lw=0.5, alpha=0.8, linestyle="-.")



                # plt.gca().figure.canvas.draw()
                result_string = filename + '\n' + 'Long Axis = {:.2f}, Short Axis = {:.2f}'.format(MA*2,SMA*2)
                plt.title(result_string) 
  
                file_to_write = open(result_file,'a',encoding='utf8',newline='')
                writer = csv.writer(file_to_write)
                # head = ['TIMG_TAG','LONG_AXIS','SHORT_AXIS','CENTER_X','CENTER_Y','THETA']
                item = [tims_str,str(MA*2),str(SMA*2),str(Xc),str(Yc),str(Theta)]
                writer.writerow(item)
                file_to_write.close()

                pic_name = tims_str + '.png'
                plt.savefig(pic_name)

                plt.pause(3)  #显示秒数
                plt.close()

            else:
                print('select funtion mode in [\'fitline\',\'fitellipse\',\'fitellipse_auto\']')


    print("process complete!")


# execute only if run as a script
if __name__ == "__main__":
    main(sys.argv[1:])