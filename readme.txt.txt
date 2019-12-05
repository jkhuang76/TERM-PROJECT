**Project Description**
This project is Geometry Sprint! It is a basic rhythm platformer game that allows you to play levels built from your own music files!
It uses aubio's beat detection to create appropriate places for platforms and other obstacles. 
Scrolling speed is based on the beats per minute of the song
There is also another mode in the level that is not directly platforming for change of pace. 
The game can be played in single player or local multiplayer mode. 

**Running the Game**
Install required libraries below 
Install the Pusab, Open Sans Regular, Lato Regular, and Solomon fonts for maximum visual appeal :)
Please put Threaded_Visual.py, Portal.py, GameObject.py, Surface.py, score.txt, Level_Generation.py, cmu_112_graphics.py into one location 
Extract the Images folder to the same location
Put your desired Music file (in .wav format!!!) in the same location (also find out sampling rate of the music file) 
Open Threaded_Visual.py in the python IDE of your choice (VSCode, Pyzo, e.t.c)
Build/Run the file and play! 

**REQUIRED LIBRARIES** 
aubio - beat detection and volume analysis 
pyaudio - music stream for the game 
numpy - math operations regarding bpm 
tkinter - essential graphics module 


**Shortcuts**
"W" - skip to the end of the level 
"P" - skip to first/on portal 
"p" - skip to off portal 
"S" - increase scrolling, essentially skipping ahead of the level
"t" - increase time counter

