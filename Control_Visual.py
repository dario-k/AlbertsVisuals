# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 11:33:41 2018

@author: Dario
"""

import cv2
import numpy as np


class visualize:
    """ class that displays the fft of the audio as well as indicators for the trigger frequency range and output"""
    
    def __init__(self, video):
        self.name = 'FFT visualisation'
        self.height = 300
        self.h_start_trig= 100
        self.width = 1000
        self.background = 100 # background color
        self.scal_eq = 1400
        self.scal_trig= 4
        
        self.rate = video.audiorate
        
        self.f_spaces = np.array([25, 50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1250, 1600,
                            2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000, 15000, 20000])
    
        self.bins = len(self.f_spaces) # number of bins
        self.w_bin = int((self.width*0.8)/self.bins) # width of bins
        self.x_values = (np.linspace(10, self.width-10-self.w_bin, self.bins)).astype(int)
        self.x_values_trig = [x for x in reversed(self.x_values)]

    
    def plot_fast(self, y_fft, triggers):
        """ plots fft of audio including indicators for different controls, so far it only works with 3 or less triggers """
    
        lfft = len(y_fft)
        fac_from_hz = len(y_fft) / (self.rate/2) #conversion factor
    
        f_spaces_t=(self.f_spaces*lfft/int(self.rate/2)).astype(int) #transformed frequency spaces
        
        plotFFT = np.zeros([self.height,self.width,3],dtype=np.uint8)
       
        y_fft_s = np.zeros(len(f_spaces_t))
        for i in range(1,len(f_spaces_t)):
            y_fft_s[i-1] = np.mean(y_fft[f_spaces_t[i-1]:f_spaces_t[i]])
        
    
        for i in range(0,len(f_spaces_t)):
            plotFFT[self.height-int(y_fft_s[i]*self.scal_eq):,self.x_values[i]:self.x_values[i]+self.w_bin,0] = self.background
            plotFFT[self.height-int(y_fft_s[i]*self.scal_eq):,self.x_values[i]:self.x_values[i]+self.w_bin,1] = self.background
            plotFFT[self.height-int(y_fft_s[i]*self.scal_eq):,self.x_values[i]:self.x_values[i]+self.w_bin,2] = self.background
            
            cv2.putText(plotFFT,str(self.f_spaces[i]),(self.x_values[i], self.height-3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1, cv2.LINE_AA)
            
            for idx, trig in enumerate(triggers): 
                f_start = int(trig.frequency*fac_from_hz) # start frequency of trigger
                f_end = f_start + int(trig.frequency_width*fac_from_hz) + 1 # end frequency of trigger
                if f_spaces_t[i]>=f_start and f_spaces_t[i]<f_end:
                    plotFFT[self.height-int(self.scal_eq*y_fft_s[i]):,self.x_values[i]:self.x_values[i]+self.w_bin,idx] = 200    
        
        for idx, trig in enumerate(triggers):
            plotFFT[self.height-int(trig.dyn*self.scal_trig):self.height-self.h_start_trig,self.x_values_trig[idx]:self.x_values_trig[idx]+self.w_bin,idx] = 255

        
        cv2.imshow(self.name, plotFFT)