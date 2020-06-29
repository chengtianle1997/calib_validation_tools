import numpy as np


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

