# Voicely #
----------------------------------
Voicely is a voice command interface for Linux, and a fork of the Voximp 
project. Voicely uses Gstreamer and CMU Sphinx to provide speech recognition,
and acts simply as a framework for triggering scripts or other code execution
with a keyword or keyphrase spoken to an active audio input device.

The main change which this project makes to the original Voximp project is the
reworking of the configuration file from a .py into a .conf with a more sane
syntax.

## Configuration
---------------------------------
Voicely is designed to be easy to configure, and to offer as much flexibility
as possible to users in terms of what commands can do. At present, Voicely
supports only one execution mode: shell. By editing voicely.conf, users can
create their own commands which when recognized will be executed on a
sub-process shell.

Future versions of voicely will also support embedded python in the config
file (which will be executed via the eval() function so take care) and commands
which require user verification before they execute.

#### voicely.conf command syntax
~~~
# Sample config file entry
[MUTE ALL AUDIO]
cmd = for i in $(pacmd list-sinks | grep index | sed s/"[index \*:]"/""/g); do; pacmd set-sink-mute $i 1; done;
msg = "Muting all audio devices"
confirm = no 
# truth would present a warning dialog before cmd   [OPTIONAL] [IN DEV]
python  = no 
# truth will eval() cmd within voicely              [OPTIONAL, DEFAULTS TO FALSE] [IN DEV]
~~~

#### voicely.conf __settings__ keywords


## Installation ##
---------------------------------
Installing Voicely is easy, just run the included install.sh

If you want to do the installation by hand you must
~~~
- create the directory ~/.config/voicely/
- move the contents of config/ to the newly created directory
- move voicely.py to /usr/bin/voicely
- chmod it +x
- know you have all the dependencies satisfied
~~~

### Arch packages upon which this project depends ###
----------------------------------
~~~~
* python2
* python-gobject
* pygtk
* python-wnck
* gstreamer0.10-python
* xdotool
* sphinxbase
* pocketsphinx
~~~~

## Getting the Most out of Voicely ##
--------------------------------
Due to limitations of voice recognition, for Voicely or even CMU Sphinx to work
you will probably need to keep your microphone at maximum volume at all times
for the computer to "hear" you.

Because of this, the computer will also "hear" everything you say and your
command phrases should be chosen to prevent accidental action on the part of
the computer. One tool which Voicely provides to assist in this is the
keyphrase noted in voicely.conf. As its name suggests, the keyphrase emulates
keying a microphone to speak to the computer by auto-magically prefixing all
commands with the keyphrase.

Say for instance one command is "Google". The odds that you say the word Google
aloud in a way which you did not intend Voicely to interpret is probably high.
However by adding a keyphrase to the config file and setting the 
"use keyphrase" flag you would have to say for instance... "Hal google" to
achieve the same effect.

Also due to limitations of speech recognition technology, the response time
of recognizing a command while under half a second is noticeable. This means
that in most cases for my fellow productivity nuts keyboard hot keys and a good
desktop will offer better reaction times than Voicely. However as evidenced by
my example command MUTE ALL AUDIO, for some more involved tasks which could be
achieved via complicated commands, scripts or GUI voice command proves a viable
wrapper on top of shell scripting.
