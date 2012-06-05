# Voicely #
----------------------------------

A voice command interface for Linux, and a fork of the Voximp project. This
project uses Gstreamer and CMU Sphinx to provide a framework for ordering
script execution by voice over an audio input device.

The main change which this project makes to the original Voximp project is the
reworking of the configuration file from a .py into a .conf with a more sane
syntax.

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
