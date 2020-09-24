#!/usr/bin/env python3
# -*- coding: UTF8 -*-

import audio
import time
import rfidreaders
import leds
import os
import random
import copy

defined_figures = rfidreaders.gamer_figures
defined_animals = rfidreaders.animal_figures

def start():
	audio.play_full("TTS",192) #Wir lernen jetzt Tiernamen auf Englisch.
	leds.reset() #reset leds
	
	audio.play_full("TTS",193) #Wenn ihr die Tiernamen auf Englisch lernen wollt, stellt die Fragezeichenfigur auf ein Spielfeld. Wenn ihr sie in einem Spiel erraten wollt, stellt eure Spielfiguren auf die Spielfelder.
	
	audio.play_file("sounds","waiting.mp3") # play wait sound
	leds.rotate_one_round(1.11)
	
	#check for figures on board, filter other tags
	players = copy.deepcopy(rfidreaders.tags)
	
	isthefirst = True
	
	if "FRAGEZEICHEN" in players:
		audio.play_full("TTS",192)
		audio.play_full("TTS",195) # Stelle einen Tier-Spielstein auf ein Spielfeld, ich sage dir dann den englischen Namen.
		while True:
			figures_on_board = copy.deepcopy(rfidreaders.tags)
			if "ENDE" in figures_on_board:
				leds.random_timer = False
				leds.reset()
				audio.kill_sounds()
				break
				
			for i, animal in enumerate(figures_on_board):
				animal = animal[:-1] #remove digit at end
				if animal in defined_animals:
					leds.led_value[i] = 1
					if not audio.file_is_playing(animal+".mp3"):
						audio.play_file("TTS/animals_en",animal+".mp3")
						time.sleep(2)
					leds.reset()
	
	else:
		for i,p in enumerate(players):
			if p not in defined_figures:
				players[i] = None

		figure_count = sum(x is not None for x in players) 

		time.sleep(1)
		if figure_count is 0:
			audio.play_full("TTS",59) #Du hast keine Spielfigure auf das Spielfeld gestellt.
			return

		audio.play_full("TTS",5+figure_count) # Es spielen x Figuren mit

		rounds = 5 # 1-5 rounds possible
		audio.play_full("TTS",20+rounds) #Wir spielen 1-5 Runden
		points = [0,0,0,0,0,0]
		
		for r in range(0,rounds):
			#print(players)
			for i,p in enumerate(players):
				if p is not None:
					leds.reset()
					leds.led_value[i] = 100
					
					if r == 0 and isthefirst == True: #first round
						isthefirst = False
						audio.play_full("TTS",12+i) #Es beginnt die Spielfigur auf Spielfeld x
						audio.play_full("TTS",194) #Ich spiele dir jetzt die englischen Namen eines Tiers vor. Wenn du das Tier weisst, tausche deine Spielfigur gegen den Tier-Spielstein aus.
					elif figure_count == 1:
						audio.play_full("TTS",67) # Du bist nochmal dran
					else:
						audio.play_full("TTS",48+i) # Die nächste Spielfigur steht auf Spielfeld x

					animal = random.choice(defined_animals)
					audio.play_file("TTS/animals_en",animal+".mp3")
					time.sleep(2)
					
					if "ENDE" in rfidreaders.tags:
						return

					while True:
						if "ENDE" in rfidreaders.tags:
							return
						
						if not audio.file_is_playing(animal+".mp3"):
							audio.play_file("TTS/animals_en",animal+".mp3")
							time.sleep(3)

						figure_on_field = copy.deepcopy(rfidreaders.tags[i])
						figure_on_field = figure_on_field[:-1] #remove digit at end
						
						if figure_on_field != None and figure_on_field != p and figure_on_field in defined_animals:
							audio.kill_sounds()
							
							if figure_on_field == animal:
								time.sleep(0.2)
								audio.play_full("TTS",27)
								print("richtig")
								audio.play_file("sounds","winner.mp3")
								time.sleep(0.2)
								points[i] += 1
								print("Du hast schon "+str(points[i])+" richtige Antworten")
								rfidreaders.tags[i] = None
								break
							else:
								time.sleep(0.2)
								audio.play_full("TTS",26)
								print("falsch")
								audio.play_file("sounds","loser.mp3")
								time.sleep(0.2)
								rfidreaders.tags[i] = None
								break
	
	if not isthefirst:
	
		# tell the points
		audio.play_full("TTS",80) #Ich verlese jetzt die Punkte
		for i, p in enumerate(players):
			if p is not None:
				leds.reset()
				leds.led_value[i] = 100
				audio.play_full("TTS",74+i) #Spielfigur auf Spielfeld 1,2...6
				time.sleep(0.2)
				print("Du hast "+str(points[i])+" Antworten richtig")
				audio.play_full("TTS",68+points[i])
				time.sleep(1)
	
	leds.reset()
