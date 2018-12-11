# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 11:26:18 2018

@author: Dario

#    Feel_You_Near.wav'#Do.wav'#Feel_You_Near.wav' Fainting_Giants.wav'



"""
import cv2
import time
import pickle

from Audio import AudioFile
from Video import Vid
from Control_Interface import fader_ux, trigger, osc
from Control_Visual import visualize

def main(video_filename = '/Users/Dario/Pictures/Nebula.mp4', audio_filename = '/Users/Dario/Pictures/Vsitor/Feel_You_Near.wav'):
    """ audio should be a wav file, video should be mp4 other video formats might work as well"""
    
    #create albert object that contains audio and video processing
    albi = Albert(v_filename=video_filename, a_filename=audio_filename, number_of_triggers = 2, number_of_oscillators = 3, disp_fft=True)
    
    while albi.status:
        
        #compute next frame and display next frame and audio
        albi.update_frame()
        
        #wait to reach desired framerate
        while time.time()-albi.update_start_time<(1.0/albi.video_object.framerate):
            pass
        print('frames per second: '+str(1.0/(time.time()-albi.update_start_time)))



class Albert:
    """this class generates the video and audio objects and performs all the computations necessary to update a frame"""
    
    def __init__(self, v_filename, a_filename, number_of_triggers = 2, number_of_oscillators = 3, disp_fft=False):
        print('----------------------------------------------------------')
        print('-----------------HELLOOOOOO ------------------------------')
        print('--------------- I am Albert ------------------------------')
        print('--------------- ready to trip? ---------------------------')
        print('----------------------------------------------------------')
        
        self.disp_fft = disp_fft
        self.v_filename = v_filename
        self.a_filename = a_filename
        self.status = True # turns false when user exits the program
        
        # generat audio and video objects
        self.audio_object = AudioFile(self.a_filename)
        self.audio_object.apply_A_weighting = True # enable or disable A weighting of audio samples
    
        self.video_object = Vid(self.v_filename, resizefactor=0.5)
        self.video_object.interpolationfactor = 1.5
        self.video_object.audiorate = self.audio_object.rate
        self.video_object.framerate = 27 # desired framerate
        
        
        # generate fader objects
        self.faders = []
        self.faders.append(fader_ux('color', ['hue1', 'hue2', 'sat1', 'sat2', 'val1', 'val2'], [0, 0, 0, 0, 0, 0]))
        self.faders.append(fader_ux('static', ['zoom', 'static_dilate', 'static_blur', 'static_blend', 'static_translation_x_img1', 'static_translation_y_img1'], [5, 0, 0, 50, 30, 20], maxvalue=100))
        self.faders.append(fader_ux('transmixer', ['M1_t_factor', 'M2_t_factor', 'M4_t_factor', 'M5_t_factor', 'M1_t_add', 'M4_t_add'], [50, 50, 50, 50, 50, 50], maxvalue=100))
    
    
        # generate trigger objects
        self.triggers = []
        for i in range(0, number_of_triggers):
            self.triggers.append(trigger('trigger '+str(i), self.audio_object.rate, frequency_r=(20,8000), f_width=(1,4000), max_attack_release=(10,30), displayGUI=True))
    
        # generate oscillator objects
        self.oscillators = []
        for i in range(0,number_of_oscillators):
            self.oscillators.append(osc('OSC MODULE '+str(i), displayGUI=True))
            
        # generate fft visualisation
        if disp_fft: self.vis = visualize(self.video_object)
        
        # for timekeeping
        self.nrframes=0
        self.start_time = time.time()
        
        
    def update_frame(self):
        """compute audio fft and next frame"""
        
        self.update_start_time = time.time()
        
        #perform fft of audio
        y_fft, amp = self.audio_object.fft()
        print('time fft : '+str(time.time()-self.update_start_time))
        
        # get values from faders
        t_ui = time.time()
        for fad in self.faders:
            fad.set_values_video(self.video_object)
        print('time fader update : '+str(time.time()-t_ui))
        
        # get values from triggers
        t_ui = time.time()
        for trig in self.triggers:
            trig.set_values_video(self.video_object, y_fft)
        print('time trigger update : '+str(time.time()-t_ui))

        # get values from oscilators
        t_ui = time.time()
        for osci in self.oscillators:
            osci.set_values_video(self.video_object)
        print('time oscillator update : '+str(time.time()-t_ui))
        
        # display equalizer
        if self.disp_fft: self.vis.plot_fast(y_fft, self.triggers)
                
        # read, process and display frame
        t_ui = time.time()
        self.video_object.compute_and_disp_frame()
        print('time video update : '+str(time.time()-t_ui))
        
        #update frame count and call key control
        self.nrframes += 1        
        self.status = self.key_control()

        
    def key_control(self):
        """the user can press keys to trigger acctions"""
        
        k = cv2.waitKey(5) & 0xFF

        if k == ord('m'):
            #flips image
            self.video_object.flipimage = not(self.video_object.flipimage)
        elif k== ord('w'):
            #enable / disable audio sample A weighting
            self.audio_object.apply_A_weighting=not(self.audio_object.apply_A_weighting)
        elif k==ord('s'): 
            #save settings
            save_name = input('saving settings, enter filename: ')
            if save_name == 'd': save_name = 'Albert_settings_default'
            self.save_settings(filename=save_name)
        elif k==ord('S'): 
            #save default settings
            self.save_settings(filename='Albert_settings_default')
        elif k==ord('r'): 
            # recall settings
            load_name = input('loading settings, enter filename: ')
            self.recal_settings(filename=load_name)
        elif k==ord('R'):
            # recall default settings
            self.recal_settings(filename='Albert_settings_default')
        elif k==ord('+'):
            self.video_object.interpolationfactor+=0.1 #makes video larger
        elif k==ord('-'):
            self.video_object.interpolationfactor-=0.1
        if k == 27:
            #stop video and audio
            frame_rate = self.nrframes / (time.time() - self.start_time)
            print('average frame rate : '+str(frame_rate))
            
            self.audio_object.close()
            self.video_object.video.release()
            cv2.destroyAllWindows()
            
            return False
        
        return True


    def save_settings(self, filename):
        """save settings of ui (triggers, faders, oscillators)"""
        
        #make settings dict
        settings = {'faders': self.faders,
                   'triggers': self.triggers,
                   'oscillators': self.oscillators
                   }
        with open(str(filename)+'.pickle', 'wb') as handle:
            pickle.dump(settings, handle, protocol=pickle.HIGHEST_PROTOCOL)


    def recal_settings(self, filename):
        """load settings of ui (triggers, faders, oscillators)"""
        
        #open settings dict
        with open(str(filename)+'.pickle', 'rb') as handle:
            settings = pickle.load(handle)
        
        self.faders = settings['faders']
        self.triggers = settings['triggers']
        self.oscillators = settings['oscillators']
        
        #update settings
        for fad in self.faders:
                fad.set_all_values(fad.slidervalues)
        for trig in self.triggers:
            trig.set_values(trig.gain, trig.frequency, trig.frequency_width, trig.routing, trig.attack, trig.release)
        for osci in self.oscillators:
            osci.set_values(speed1=osci.speed1, amp1=osci.amp1, routing1=osci.routing1, speed2=osci.speed2, amp2=osci.amp2, routing2=osci.routing2)


if __name__ == "__main__":
    main()