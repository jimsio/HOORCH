#!/usr/bin/env python3
# -*- coding: UTF8 -*-

import audio
import time
import rfidreaders
import leds
import os 
import pygame
import re

phones = []

def start():	
	print("Wir spielen Kakophonie")
	
	audio.play_full("TTS",64) #Wir spielen Kakophonie. Stelle die Zahlen 1 bis 6 auf die Spielfelder!
	leds.reset() #reset leds
		
	if not pygame.mixer.get_init():
		pygame.mixer.init()
		pygame.mixer.set_num_channels(6)
		for s in range(0,6):
			phones.append(pygame.mixer.Sound("data/phonie/00"+str(s+1)+".ogg"))
			phones[s].set_volume(0)
	else:
		pygame.mixer.unpause()

	for p in phones:
		p.play(loops = -1)
	leds.random_timer = True

	while True:
		found_digits = []
		for i, tag in enumerate(rfidreaders.tags):
			if tag is not None:
				if re.search("^[A-z]*[0-9]$", tag):
					found_digits.append(tag[-1]) #get digit
				
		for i in range(0,6):
			#if str(i+1) not in rfidreaders.tags:
			if str(i+1) not in found_digits:
				phones[i].set_volume(0)
			else: 
				phones[i].set_volume(1)

		if "ENDE" in rfidreaders.tags:
			pygame.mixer.pause()
			break

	leds.random_timer = False
	leds.reset()