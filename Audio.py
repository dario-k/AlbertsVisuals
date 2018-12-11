# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 12:20:52 2018

@author: Dario
"""

import time
import numpy as np

import pyaudio
import wave
from matplotlib import pyplot as plt
from scipy.fftpack import fft
import collections


class AudioFile:
    chunk = 1024*4 # frame_count of callback is 1024
    # chunk is now dynamic so this is just the initial value

    def __init__(self, file):
        """ Init audio stream """ 
        self.file = file
        self.wf = wave.open(self.file, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True,
            stream_callback=self.playingCallback
        )
        self.rate = self.wf.getframerate()
        self.channels = self.wf.getnchannels()
        self.window = np.hamming(self.chunk)#blackman(self.chunk)
        self.time = time.time()
        self.FFTaudiobuffer = collections.deque(maxlen=4)
        for i in range(0,4): self.FFTaudiobuffer.append(np.zeros(1024))
        print('Audio rate ', self.rate)
        self.nr_appends_since_read = 0
        self.calc_A_weighting()
        self.apply_A_weighting=True
        
    
    def playingCallback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        #data = self.wf.readframes(self.chunk)
        self.FFTaudiobuffer.append(data)
        self.nr_appends_since_read += 1
        return (data, pyaudio.paContinue)


    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.chunk)
        while data != '':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)


    def init_justplot(self):
        self.fig, (ax1, ax2) = plt.subplots(2, figsize=(15, 7))
        
        audio_x = np.arange(0, 2*self.chunk,2)
        #fft_x = np.linspace(0, self.rate, self.chunk)
        self.xfft = np.linspace(0.0, self.rate/2.0, self.chunk//2)
        
        self.line, = ax1.plot(audio_x, np.random.rand(self.chunk), '-', lw=2)
        self.line_fft, = ax2.semilogx(self.xfft, np.random.rand(self.chunk//2), '-',lw=2)
        ax1.set_title('AUDIO WAVEFORM')
        ax1.set_xlabel('samples')
        ax1.set_ylabel('volume')
        #ax1.set_ylim(-2**15, 2**15)
        ax1.set_ylim(-1, 1)
        ax1.set_xlim(0, 2 * self.chunk)
        plt.setp(ax1, xticks=[0, self.chunk, 2 * self.chunk])
        
        ax2.set_xlim(0, self.rate / 2)
        ax2.set_ylim(0, 1)
        ax2.set_xlabel('Frequency [Hz]')
        ax2.set_ylabel('Amplitude')


    def justplot(self, yfft, ytime): 
        self.line.set_ydata(ytime)
        self.line_fft.set_ydata(yfft)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def fft(self):
        """ fft of audio, if audio ended, open the file again"""
        
        print('nr appends (audio) : ', self.nr_appends_since_read)
        # this is the new implementation with dynamic chunk size, still kind of stupid, will make a better one sometime...
        # it can deal with with chunk sizes of 1024 to 4096 and up, this allows to deal with different framerates or variation in computation time,
        # however it would be better if it was continous and not bound to chunk size
        # it will fail if its called before a whole chunk of at least 1024 samples is read
        if self.nr_appends_since_read==0:
            #if the framerate is set too high, the audio chunk is not ready yet. need to wait a bit...
            print('zero audio appends!! something went wrong, likely framerate is too high!!!')
            time.sleep(0.02)
            return self.fft()
        elif self.nr_appends_since_read==1:
            nr_appends_backup = 1
            self.nr_appends_since_read=0 # imideately reset because the audio thread might read samples while this is happening
            data = self.FFTaudiobuffer[3]
            amplitude = np.fromstring(data, np.int16)[::self.channels] /2.0**15
            self.chunk = 1024
        elif self.nr_appends_since_read==2:
            nr_appends_backup = 2
            self.nr_appends_since_read=0 # imideately reset because the audio thread might read samples while this is happening
            data = [self.FFTaudiobuffer[2], self.FFTaudiobuffer[3]]
            amplitude = np.fromstring(self.FFTaudiobuffer[2], np.int16)[::self.channels] /2.0**15
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[3], np.int16)[::self.channels] /2.0**15)
            self.chunk = 2048
        elif self.nr_appends_since_read==3:
            nr_appends_backup = 3
            self.nr_appends_since_read=0 # imideately reset because the audio thread might read samples while this is happening
            data = [self.FFTaudiobuffer[1], self.FFTaudiobuffer[2], self.FFTaudiobuffer[3]]
            amplitude = np.fromstring(self.FFTaudiobuffer[1], np.int16)[::self.channels] /2.0**15
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[2], np.int16)[::self.channels] /2.0**15)
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[1], np.int16)[::self.channels] /2.0**15)
            self.chunk = 1024*3
        elif self.nr_appends_since_read>=4:
            nr_appends_backup = 4
            self.nr_appends_since_read=0 # imideately reset because the audio thread might read samples while this is happening
            data = [self.FFTaudiobuffer[0], self.FFTaudiobuffer[1], self.FFTaudiobuffer[2], self.FFTaudiobuffer[3]]
            amplitude = np.fromstring(self.FFTaudiobuffer[0], np.int16)[::self.channels] /2.0**15
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[1], np.int16)[::self.channels] /2.0**15)
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[2], np.int16)[::self.channels] /2.0**15)
            amplitude = np.append(amplitude, np.fromstring(self.FFTaudiobuffer[3], np.int16)[::self.channels] /2.0**15)
            
            self.chunk = 4096
            if len(amplitude)>self.chunk:
                amplitude = amplitude[:self.chunk]
                print('amplitude was longer than chunk!!')
        
        # compute FFT and update line
        self.window = np.hamming(self.chunk)
        
        # check if audio file ended --> reopen
        if len(amplitude) != len(self.window):
            print('Audio File ended!')
            self.close()
            self.__init__(self.file)
            return self.fft()

        yf = fft(amplitude*self.window) 
        yfft = np.abs(yf[0:self.chunk//2])  * (12.0 / (self.chunk))
        
        if self.apply_A_weighting:
            yfft = np.multiply(yfft,self.A_weighting_factors[nr_appends_backup-1])

        return yfft, amplitude


    def A_weighting(self, f):
        fo = (np.power(12194,2)*np.power(f,4))/((np.power(f,2)+np.power(20.6,2))
        *np.sqrt((np.power(f,2)+np.power(107.7,2))*(np.power(f,2) +np.power(737.9,2)))
        *(np.power(f,2)+np.power(12194,2)))
        return fo


    def calc_A_weighting(self):
        fr=np.arange(0.0,self.rate)
        af=[self.A_weighting(i) for i in fr]
#        fac = np.linspace(10,int((self.rate/2)-1),2048).astype(int)
        self.A_weighting_factors = []
        for i in [1024, 2048, 3072, 4096]:
            fac = np.linspace(10,int((self.rate/2)-1),i//2).astype(int)
            af = np.asarray(af)
            self.A_weighting_factors.append(af[fac])


    def close(self):
        """ beautiful shutdown """ 
        self.stream.close()
        self.p.terminate()
        
        