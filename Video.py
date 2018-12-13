# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 11:38:27 2018

@author: Dario
"""

import cv2
import numpy as np
import copy
import collections



class Vid:
    """ video class that opens, manipulates and displays the video"""
    videobuffersize=80
    
    def __init__(self, file, resizefactor=1.0):
        self.videofile = file
        self.video = cv2.VideoCapture(self.videofile)
        self.videobuffer = collections.deque(maxlen=self.videobuffersize)
        self.resizefactor=resizefactor
        self.interpolationfactor = 1.0 # enables the processing with a lower resolution and upscales to show the image
        self.flipimage = False
        self.colmap = 0 # colormap applied to video (0 no colmalp, 1-4 different colormaps)
        

        # make videobuffer
        for i in range(0,self.videobuffersize):
            _, img = self.video.read()
            rows, cols = np.shape(img)[0:2]
            img = cv2.resize(img,(int(cols * self.resizefactor),int(rows*self.resizefactor)))
            if self.colmap!=0:
                if self.colmap==1:
                    img = cv2.applyColorMap(img, cv2.COLORMAP_JET)
                elif self.colmap==2:
                    img = cv2.applyColorMap(img, cv2.COLORMAP_SUMMER)
                elif self.colmap==3:
                    img = cv2.applyColorMap(img, cv2.COLORMAP_PINK)
                elif self.colmap==4:
                    img = cv2.applyColorMap(img, cv2.COLORMAP_BONE)
                    
            self.videobuffer.append(img)
        
        # size of image
        self.rows, self.cols = np.shape(self.videobuffer[0])[0:2]
        self.rows_raw, self.cols_raw = rows, cols

        
        # dict with all the parameters that can change the look of a frame
        # osc means they are modified by the oscillators
        # dyn means they are modified by the triggers
        self.parameter_dict = {
                          'nothing': 0,
                          'hue1': 0,
                          'hue2': 0,
                          'sat1': 0,
                          'sat2': 0,
                          'val1': 0,
                          'val2': 0,
                          'dyn_frame': 0,
                          'osc_frame': 0,
                          'dyn_translation': 0,
                          'x_speed': 0,
                          'y_speed': 0,
                          'dyn_hue1': 0,
                          'dyn_sat1': 0,
                          'dyn_val1': 0,
                          'dyn_hue2': 0,
                          'dyn_sat2': 0,
                          'dyn_val2': 0,
                          'dyn_blend':0,
                          'osc_hue1': 0,
                          'osc_sat1': 0,
                          'osc_val1': 0,
                          'osc_hue2': 0,
                          'osc_sat2': 0,
                          'osc_val2': 0,
                          'osc_blend':0,
                          'osc_translation_x_img1': 0,
                          'osc_translation_x_img2': 0,
                          'osc_translation_y_img1': 0,
                          'osc_translation_y_img2': 0,
                          'static_dilate':0,
                          'osc_dilate': 0,
                          'dyn_dilate':0,
                          
                          'static_blend':50,
                          'static_blur':0,
                          'zoom':0,
                          'static_translation_x_img1': 10,
                          'static_translation_y_img1': 20,
                          
                          'osc_blur':0,
                          'dyn_blur':0,
                          
                          'osc_M1_img1': 0,
                          'osc_M2_img1':0,
                          'osc_M4_img1': 0,
                          'osc_M5_img1': 0,
                          'dyn_M1_img1': 0,
                          'dyn_M2_img1':0,
                          'dyn_M4_img1': 0,
                          'dyn_M5_img1': 0,
                          
                          'M1_t_factor': 50,
                          'M2_t_factor': 50,
                          'M3_t_factor': 50, # not used yet
                          'M4_t_factor': 50,
                          'M5_t_factor': 50,
                          'M6_t_factor': 50, # not used yet
                          'M1_t_add': 50,
                          'M4_t_add': 50,
                          
                          'dyn_recursion_depth': 0,
                          'osc_recursion_depth': 0,
                          'static_recursion_depth': 1
                          }


    def compute_and_disp_frame(self):
        """this function calls all the functions neccessary to proceed to the next frame"""
        self.read_from_buffer()
        
        for i in range(0,int(self.parameter_dict['static_recursion_depth']+self.parameter_dict['osc_recursion_depth']+self.parameter_dict['dyn_recursion_depth'])):
            img1, img2 = self.afine_distortion()
            img1, img2 = self.color(img1, img2)
    
            img = self.blend(img1, img2)
            img = self.dilate_and_blur(img)
            self.img_hsv, self.img_hsv2 = img, copy.copy(img)
            
            
        self.show_frame(img)
        
        
    def blend(self, img_hsv1, img_hsv2):
        """ blends the two hsv images and returns a bgr image"""
        #blend between the two images        
        blend = self.parameter_dict['static_blend']+self.parameter_dict['osc_blend']+self.parameter_dict['dyn_blend']
        superimage_hsv = cv2.addWeighted(img_hsv1, blend/100.0,
                                         img_hsv2, (100-blend)/100.0,0)
        
        #convert hsv to bgr
        superimage_bgr = cv2.cvtColor(superimage_hsv,cv2.COLOR_HSV2BGR)
        
        return superimage_bgr
           
     
    def read_from_buffer(self):
        """ reads frames from file, appends them to buffer, reads from buffer"""
        #read and append to buffer
        ret, img_r = self.video.read()
        if ret:
#            img_r = cv2.resize(img_r,(self.cols,self.rows))
            img_r = self.zoom_and_resize(img_r)
            if self.colmap!=0:
                if self.colmap==1:
                    img_r = cv2.applyColorMap(img_r, cv2.COLORMAP_JET)
                elif self.colmap==2:
                    img_r = cv2.applyColorMap(img_r, cv2.COLORMAP_SUMMER)
                elif self.colmap==3:
                    img_r = cv2.applyColorMap(img_r, cv2.COLORMAP_PINK)
            self.videobuffer.append(img_r)
        else:
            self.video.release()
            self.video = cv2.VideoCapture(self.videofile)
        
        # read from buffer
        dynFrame = int(np.maximum(0,np.minimum(self.videobuffersize-1, self.parameter_dict['dyn_frame'] + self.parameter_dict['osc_frame']))) 
        img = self.videobuffer[self.videobuffersize-1-dynFrame]
        
        self.img_hsv = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        self.img_hsv2 = copy.copy(self.img_hsv)


    def afine_distortion(self):
        """
        performs afine transform distortions on both images
        the parameters for the transform matrix M2 derived from M1 by multiplication with a factor
        """
         #parameters for transform matrix
        M1_1 = 1 + (self.parameter_dict['osc_M1_img1'] + self.parameter_dict['dyn_M1_img1'])/100
        M1_2 = (self.parameter_dict['osc_M2_img1'] + self.parameter_dict['dyn_M2_img1'])/100
        M1_3 = self.parameter_dict['static_translation_x_img1']+self.parameter_dict['osc_translation_x_img1']+self.parameter_dict['dyn_translation']
        M1_4 = (self.parameter_dict['osc_M4_img1'] + self.parameter_dict['dyn_M4_img1'])/100
        M1_5 = 1 + (self.parameter_dict['osc_M5_img1'] + self.parameter_dict['dyn_M5_img1'])/100
        M1_6 = self.parameter_dict['static_translation_y_img1']+self.parameter_dict['osc_translation_y_img1']+self.parameter_dict['dyn_translation']
        
        M1 = np.float32([[M1_1,M1_2,M1_3],
                         [M1_4,M1_5,M1_6]])
        M2 = np.float32([[M1_1 * ((self.parameter_dict['M1_t_factor']-50)/100 + 1) + ((self.parameter_dict['M1_t_add']-50)/100),
                          M1_2 * ((self.parameter_dict['M2_t_factor']-50)/100 + 1),
                          self.parameter_dict['osc_translation_x_img2']],
                         [M1_4 * ((self.parameter_dict['M4_t_factor']-50)/100 + 1) + ((self.parameter_dict['M4_t_add']-50)/100),
                          M1_5 * ((self.parameter_dict['M5_t_factor']-50)/100 + 1),
                          self.parameter_dict['osc_translation_y_img2']]])

        #transform img 1 and 2
        img_hsv2 = cv2.warpAffine(self.img_hsv2,M1,(self.cols,self.rows))
        img_hsv = cv2.warpAffine(self.img_hsv,M2,(self.cols,self.rows))
        
        return img_hsv, img_hsv2


    def perspective_distortion(self):
        """
        perform perspective distorition
        NOT IMPLEMENTED YET, MAYBE FOR LATER...
        """
        bias = 10
        pts11 = pts12 = np.float32([[self.cols//2-bias,self.rows//2-bias],[self.cols//2+bias,self.rows//2-bias],[self.cols//2-bias,self.rows//2+bias],[self.cols//2+bias,self.rows//2+bias]])
        pts12[0,0] = pts12[0,0] + self.parameter_dict['static_perspecitive_x_p1_img1']
        pts12[0,1] = pts12[0,1] + self.parameter_dict['static_perspecitive_y_p1_img1']


        M1 = cv2.getPerspectiveTransform(pts11,pts12)

        dst = cv2.warpPerspective(self.img_hsv2, M1, (int(self.cols*self.resizefactor),int(self.rows*self.resizefactor)))
        
        return dst


    def color(self, img_hsv1, img_hsv2):
        """ just calls the adjust color function, there is no real need for this other than making the top function look less crowded ... """
        # adjust color
        img_hsv_processed1 = self.adjust_color(img_hsv1, self.parameter_dict['hue1']+self.parameter_dict['osc_hue1']+self.parameter_dict['dyn_hue1'],
                                                   self.parameter_dict['sat1']+self.parameter_dict['osc_sat1']+self.parameter_dict['dyn_sat1'],
                                                   self.parameter_dict['val1'] +self.parameter_dict['osc_val1']+ self.parameter_dict['dyn_val1'])
        img_hsv_processed2 = self.adjust_color(img_hsv2, self.parameter_dict['hue2']+self.parameter_dict['osc_hue2']+self.parameter_dict['dyn_hue2'],
                                                    self.parameter_dict['sat2'] + self.parameter_dict['osc_sat2'] + self.parameter_dict['dyn_sat2'],
                                                    self.parameter_dict['val2'] + self.parameter_dict['osc_val2'] + self.parameter_dict['dyn_val2'])
        
        return img_hsv_processed1, img_hsv_processed2
        

    def adjust_color(self, img_hsv, hue, sat=0, value=0):
        """ adjust hue, saturation and value of hsv image"""
        img_hsv[:,:,0] = img_hsv[:,:,0]+hue
        img_hsv[:,:,1] = img_hsv[:,:,1]+sat
        img_hsv[:,:,2] = img_hsv[:,:,2]+value
        
        return img_hsv
        
    
    def dilate_and_blur(self, frame):
        """dilation and gaussian smoothing as an effect"""
        
        makeodd = lambda x: x+1 if x % 2 == 0 else x
#                nice_frame = cv2.dilate(nice_frame, (5,5), iterations=self.dilate)
        dilate = int(self.parameter_dict['static_dilate']+abs(self.parameter_dict['osc_dilate'])+self.parameter_dict['dyn_dilate'])
        blur = int(self.parameter_dict['static_blur']+abs(self.parameter_dict['osc_blur'])+self.parameter_dict['dyn_blur'])
        if dilate>0:
            frame = cv2.dilate(frame, (makeodd(5*dilate), makeodd(5*dilate)), iterations=dilate)
        if blur>0:
            frame = cv2.GaussianBlur(frame, (makeodd(5*blur), makeodd(5*blur)) , 0) 
       
        return frame
    
    
    def show_frame(self, frame):
        """ shows frame, mirrors on y axis if flipimage is set"""
        if self.flipimage:
            frame_flipped = cv2.flip(frame, 1)
            frame[0:self.rows, 0:int(self.cols/2)] = frame_flipped[0:self.rows, 0:int(self.cols/2)]
        
        frame = cv2.resize(frame,(int(self.cols * self.interpolationfactor),int(self.rows * self.interpolationfactor)), interpolation = cv2.INTER_LINEAR)
        cv2.imshow('Visuals',frame)

    
    def zoom_and_resize(self, image):
        """
        zoom into image and resizes it to whatever is set in self.cold and self.rows
        it is applied to a frame before resizing, if it needs to be applied after resizing self.rows_raw and self.cols_raw 
        needs to be replaced with self.rows and self.cols
        """
        zoom_x = self.parameter_dict['zoom'] * 4
        zoom_y = self.parameter_dict['zoom'] * 4 * self.rows/self.cols
        croped = image[int(zoom_y/2.0):int(self.rows_raw - (zoom_y/2.0)), int(zoom_x/2.0):int(self.cols_raw -(zoom_x/2.0))]
        
        return cv2.resize(croped,(int(self.cols),int(self.rows)))