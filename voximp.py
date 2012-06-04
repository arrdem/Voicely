#!/usr/bin/env python2

# Copyright (c) 2008 Ben Duffield
# Licensing - no idea
# Probably w/e sphinx is, think it's MIT
# Be nice!

#######
#REQUIRES:
# gstreamer
# pygtk
# pocketsphinx
# xdotool
#########

import pygtk
pygtk.require('2.0')
import gtk

import gobject
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst
from subprocess import Popen
import os
import sys
import getopt


config_dir = os.path.join(os.path.expanduser("~"), '.config/voximp/')
try:
	os.makedirs(config_dir)
except:
	pass
sys.path.append(config_dir)
from voximpconf import *
	
language_file = os.path.join(config_dir, str(languagemodel))

config = {
	'hmm': '/usr/share/pocketsphinx/model/hmm/wsj1',
	'lm': '%s.lm' % language_file,
	'dict': '%s.dic' % language_file
	}

class Voximp(object):
    dial = None
    def __init__(self):
        self.init_gst()
	self.pipeline.set_state(gst.STATE_PLAYING)

    def init_gst(self):
        self.pipeline = gst.parse_launch('alsasrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
	asr.set_property('lm', config['lm'])
	asr.set_property('dict', config['dict'])
	asr.set_property('configured', True)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)

        self.pipeline.set_state(gst.STATE_PAUSED)

    def asr_partial_result(self, asr, text, uttid):
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def asr_result(self, asr, text, uttid):
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.partial_result(msg.structure['hyp'], msg.structure['uttid'])
        elif msgtype == 'result':
            self.final_result(msg.structure['hyp'], msg.structure['uttid'])
            #self.pipeline.set_state(gst.STATE_PAUSED)
            #self.button.set_active(False)

    def partial_result(self, hyp, uttid):
	print "partial: %s" % hyp

    def final_result(self, hyp, uttid):
	print "final: %s" % hyp
	prog = ''
	command = None
	if self.dial is not None:
		if hyp == 'YES':
			self.dial.response(gtk.RESPONSE_YES)
		else:
			self.dial.response(gtk.RESPONSE_NO)
	elif hyp in programcommand:
		prog = programcommand[hyp]
		command = hyp
	elif hyp in keycommand:
		prog = "xdotool key ``%s''" % keycommand[hyp]
		command = hyp
	elif hyp in mousecommand:
		prog = "xdotool click %s" % mousecommand[hyp]
		command = hyp
	else:
		values = hyp.split(' ')
		if len(values) <= 1:
			return
		if values[0] in progswithargs:
			prog = progswithargs[values[0]] + ' ' + ' '.join(values)
			command = values[0]
		else:
			for value in values:
				self.final_result(value, 0)
	if prog:
		print "command is %s" % command
		if command in confirm:
			self.confirm(prog)
		else:
			p = Popen(prog, shell=True)
    def confirm(self, prog):
	print "Confirming %s" % prog
	self.dial = gtk.MessageDialog(message_format = "Confirm?", type=gtk.MESSAGE_QUESTION)
	self.dial.format_secondary_markup("Say <b><i>yes</i></b> or <b><i>no</i></b>")
	self.dial.prog = prog
	self.dial.show_all()
	self.dial.connect("response", self.confirmCallback)
    def confirmCallback(self, dialog, response_id):
	print "callback called back"
	if response_id == gtk.RESPONSE_YES:
		p = Popen(dialog.prog, shell=True)
    	self.dial.destroy()
	self.dial = None

versionNumber = '0.0.1'
usageInfo = '''Usage: voximp [options]

Options:
  -v, --version		show program version and exit
  -h, --help		show this help message and exit
  -c, --corpus		create a corpus.txt in current directory - used for generating language model files
'''
def usage():
	print "Voximp version %s" % versionNumber
	print usageInfo
def version():
	print "Version %s" % versionNumber
def corpus():
	words = []
	words.extend(keycommand.keys())
	words.extend(programcommand.keys())
	words.extend(mousecommand.keys())
	words.extend(progswithargs.keys())
	corpusText =  "\n".join(words)
	filename = os.path.join(os.getcwd(), 'corpus.txt')
	print "Saving to %s" % filename
	corp = open(filename, 'w')
	corp.write(corpusText)
	corp.flush()
	corp.close()
	print "Corpus saved"
	print "Now visit http://www.speech.cs.cmu.edu/tools/lmtool.html"
	print "  ==> choose the corpus file, click COMPILE KNOWLEDGE BASE"
	print "  ==> save the three files to ~/.config/voximp/"
	print "  ==> edit ~/.config/voximp/voximpconf.py and set the languagemodel string to the appropriate value \n\t- e.g. if the files are named 4766.dic, 4766.lm and 4766.sent, set languagemodel = '4766'"
if __name__ == '__main__':
	try:                                
		opts, args = getopt.getopt(sys.argv[1:], "hcv", ["help", "corpus", "version"])
	except getopt.GetoptError:
		print "error"
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()                     
			sys.exit()
		elif opt in ("-c", "--corpus"):
			corpus()
			sys.exit()
		elif opt in ("-v", "--version"):
			version()
			sys.exit()
	app = Voximp()
	gtk.main()
