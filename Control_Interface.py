# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 11:30:56 2018

@author: Dario
"""

import cv2
import numpy as np

class ux:
    """
    user interface class
    """
    def __init__(self, name):
        #load config settings
        self.name = name
        cv2.namedWindow(self.name)
    def nothing(self, x):
            pass


class fader_ux(ux):
    """
    gui class for faders
    """
    
    def __init__(self, name, slidernames, slidervalues, maxvalue=255):
        ux.__init__(self, name)
        self.slidernames = slidernames #list of names
        self.slidervalues = slidervalues #list of values
        
        for sname in self.slidernames:
            cv2.createTrackbar(sname,self.name, 0, maxvalue, self.nothing)
        
        #set initial vlaues
        self.set_all_values(self.slidervalues)
    
    def set_all_values(self, values):
        for (nam,val) in zip(self.slidernames, values):
            cv2.setTrackbarPos(nam, self.name, val)
    
    def update_values(self):
        """update slider values, should be done in a callback in the future..."""
        values = []
        for sname in self.slidernames:
            values.append(cv2.getTrackbarPos(sname,self.name))
        self.slidervalues = values
    
    def set_values_video(self, video):
        """ set values of video object """
        #maybe there is a way to do it in the callback???
        self.update_values()
        for sname, svalue in zip(self.slidernames, self.slidervalues):
            video.parameter_dict[sname] = svalue


class trigger(ux):
    """
    class that describes audio triggers
    call calc_output to get the output after the envelope
    """
    def __init__(self, name, audiorate, frequency_r=(20,20000), f_width=(1,2000), max_attack_release=(10,20), displayGUI=True):
        ux.__init__(self, name)
        
        self.audiorate=audiorate
        self.displayGUI = displayGUI
        
        #routing
        self.routing_t = 0
        self.routing_dict = {0: 'nothing',
                        1: 'dyn_hue1',
                        2: 'dyn_sat1',
                        3: 'dyn_val1',
                        4: 'dyn_hue2',
                        5: 'dyn_sat2',
                        6: 'dyn_val2',
                        7: 'osc_blend',
                        8: 'dyn_blur',
                        9: 'dyn_dilate',
                        10: 'dyn_frame'
                        }
        
        self.routing_options=len(self.routing_dict)-1
        
        if self.displayGUI:
            cv2.createTrackbar('Gain', self.name,0,200, self.nothing)
            cv2.createTrackbar('Frequency [Hz]', self.name, frequency_r[0], frequency_r[1], self.nothing) #frequency
            cv2.createTrackbar('Width [Hz]', self.name, f_width[0], f_width[1], self.nothing) #range
            cv2.createTrackbar('Route', self.name, 0,self.routing_options, self.nothing)
            cv2.createTrackbar('Attack', self.name, 0, max_attack_release[0], self.nothing)
            cv2.createTrackbar('Release', self.name, 0, max_attack_release[1], self.nothing)
        
        self.gain=1
        self.frequency=1000
        self.frequency_width=1000
        self.routing=1
        self.attack=1
        self.release=3
        
        # init for envelope
        self.en_baseline = 0
        self.en_value = 0
        self.en_timekeeper_a = 0
        self.en_timekeeper_r = 0
        self.en_vtrig = 0
        
        # init output
        self.dyn = 0

        
    def set_values(self, gain, frequency, frequency_width, routing, attack, release):
        cv2.setTrackbarPos('Gain', self.name, gain)
        cv2.setTrackbarPos('Frequency [Hz]', self.name, frequency)
        cv2.setTrackbarPos('Width [Hz]', self.name, frequency_width)
        cv2.setTrackbarPos('Route', self.name, routing)
        cv2.setTrackbarPos('Attack', self.name, attack)
        cv2.setTrackbarPos('Release', self.name, release)
    
    def get_values(self):
        """get values from trackbars"""
        self.gain = cv2.getTrackbarPos('Gain',self.name)
        self.frequency = cv2.getTrackbarPos('Frequency [Hz]',self.name)
        self.frequency_width = cv2.getTrackbarPos('Width [Hz]',self.name)
        self.routing = cv2.getTrackbarPos('Route',self.name)
        self.attack = cv2.getTrackbarPos('Attack',self.name)
        self.release = cv2.getTrackbarPos('Release',self.name)
        
        
    def envelope(self, sample):
        """calculate envelope output"""
        
        self.en_baseline = self.en_baseline*0.95+sample*0.05
        th = 0
        s_b = (sample-self.en_baseline)*self.gain
        if s_b > (th+self.en_value):
            self.en_timekeeper_a = self.attack+1
            self.en_timekeeper_r = self.release+1
            self.en_vtrig = s_b
        
        if self.en_timekeeper_a > 0:
            self.en_value = self.en_value +  (self.en_vtrig - self.en_baseline) * (1/(self.attack+1))
            self.en_timekeeper_a = self.en_timekeeper_a - 1
        elif self.en_timekeeper_r > 0:
            self.en_value = self.en_value -  (self.en_vtrig - self.en_baseline) * (1/(self.release+1))
            self.en_timekeeper_r = self.en_timekeeper_r - 1
        else:
            self.en_value = self.en_value - (self.en_value-self.en_baseline)*(1/(self.release+1))
            
        return self.en_value
        
    def calc_output(self, y_fft):
        if self.displayGUI: self.get_values() #otherwise change values within the program
        fac_from_hz = len(y_fft) / (self.audiorate/2)
        frequency_d = int(self.frequency * fac_from_hz)
        frequency_width_d= int(self.frequency_width * fac_from_hz)
        
        temp = y_fft[int(frequency_d):int(frequency_d+frequency_width_d+1)]
        if len(temp)>0:
            Amp_dynamic = np.mean(temp)*10.0
        else: Amp_dynamic = 0
        
        return self.envelope(Amp_dynamic)
    
    def set_values_video(self, video, y_fft):
        self.dyn = self.calc_output(y_fft)
        
        if(not(self.routing_t==self.routing)):
            video.parameter_dict[self.routing_dict[self.routing_t]] = 0
        video.parameter_dict[self.routing_dict[self.routing]] = self.dyn
        

class osc(ux):
    """
    oscillator class
    """
    
    def __init__(self, name, displayGUI=True):
        ux.__init__(self, name)
        
        self.displayGUI = displayGUI
        self.max_speed = 100
        self.max_amp = 1000
        
        #routing dictinaries
        self.routing_dict1 = {0: 'nothing',
                        1: 'osc_hue1',
                        2: 'osc_sat1',
                        3: 'osc_val1',
                        4: 'osc_blend',
                        5: 'osc_translation_x_img1',
                        6: 'osc_translation_x_img2',
                        7: 'osc_blur',
                        8: 'osc_frame',
                        9: 'osc_M1_img1',
                        10: 'osc_M2_img1',
                        }
        
        self.routing_dict2 = {0: 'nothing',
                        1: 'osc_hue2',
                        2: 'osc_sat2',
                        3: 'osc_val2',
                        4: 'osc_blend',
                        5: 'osc_translation_y_img1',
                        6: 'osc_translation_y_img2',
                        7: 'osc_dilate',
                        8: 'osc_frame',
                        9: 'osc_M4_img1',
                        10: 'osc_M5_img1'
                        }

        self.routing_options = len(self.routing_dict1)-1
        
        if self.displayGUI:
            cv2.createTrackbar('Speed 1', self.name,0, self.max_speed, self.nothing)
            cv2.createTrackbar('Amplitude 1', self.name,0, self.max_amp,self.nothing)
            cv2.createTrackbar('Routing 1', self.name,0,self.routing_options,self.nothing)
            cv2.createTrackbar('Speed 2', self.name,0,self.max_speed,self.nothing)
            cv2.createTrackbar('Amplitude 2', self.name,0,self.max_amp,self.nothing)
            cv2.createTrackbar('Routing 2', self.name,0,self.routing_options,self.nothing)
            
        self.speed1 = 0
        self.speed2 = 0
        self.amp1 = 0
        self.amp2 = 0
        self.routing1 = 0
        self.routing2 = 0
        
        self.osc_val1 = 0
        self.direction1 = 1
        self.osc_val2 = 0
        self.direction2 = 1
        
        self.routing1_t = 1
        self.routing2_t = 1
        
        
    def set_values(self, speed1, amp1, routing1, speed2, amp2, routing2):
        """sets values of the trackbars"""
        cv2.setTrackbarPos('Speed 1', self.name, speed1)
        cv2.setTrackbarPos('Amplitude 1', self.name, amp1)
        cv2.setTrackbarPos('Routing 1', self.name, routing1)
        cv2.setTrackbarPos('Speed 2', self.name, speed2)
        cv2.setTrackbarPos('Amplitude 2', self.name, amp2)
        cv2.setTrackbarPos('Routing 2', self.name, routing2)
        
        
    def get_values(self):
        """ get values from the trackbars """
        self.speed1 = cv2.getTrackbarPos('Speed 1',self.name)
        self.amp1 = cv2.getTrackbarPos('Amplitude 1',self.name)
        self.routing1 = cv2.getTrackbarPos('Routing 1',self.name)
        self.speed2 = cv2.getTrackbarPos('Speed 2',self.name)
        self.amp2 = cv2.getTrackbarPos('Amplitude 2',self.name)
        self.routing2 = cv2.getTrackbarPos('Routing 2',self.name)
        
        
    def oscillate(self):
        """ advances by speed until it hits amplitude where inverts direction, vise versa for negative side"""
        
        if self.displayGUI: self.get_values()
            
        # osc 1
        if abs(self.osc_val1) > self.amp1 and self.direction1==1:
            self.direction1 = 0
        elif abs(self.osc_val1) > self.amp1 and self.direction1==0:
            self.direction1 = 1
        
        if self.direction1 == 1:
            self.osc_val1 = self.osc_val1 + self.speed1
        elif self.direction1 == 0:
            self.osc_val1 = self.osc_val1 - self.speed1
            
        # osc 2
        if abs(self.osc_val2) > self.amp2 and self.direction2==1:
            self.direction2 = 0
        elif abs(self.osc_val2) > self.amp2 and self.direction2==0:
            self.direction2 = 1
        
        if self.direction2 == 1:
            self.osc_val2 = self.osc_val2 + self.speed2
        elif self.direction2 == 0:
            self.osc_val2 = self.osc_val2 - self.speed2
            
            
    def set_values_video(self, video):
        """
        osc 1 can set properties of img1 
        osc 2 can set properties of img2
        
        routing:
            see routing dict
        """
        
        self.oscillate()
        
        # for osc1
        if(not(self.routing1_t==self.routing1)):
            video.parameter_dict[self.routing_dict1[self.routing1_t]] = 0
        video.parameter_dict[self.routing_dict1[self.routing1]] = self.osc_val1 / 10

        # for osc2 
        if(not(self.routing2_t==self.routing2)):
            video.parameter_dict[self.routing_dict2[self.routing2_t]] = 0
        video.parameter_dict[self.routing_dict2[self.routing2]] = self.osc_val2 / 10
        
        #routing t-1, so it can be set to 0 when routing changes
        self.routing1_t = self.routing1
        self.routing2_t = self.routing2
