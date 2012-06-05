#!/usr/bin/env python2
# Copyright 2008 Ben Duffield, 2012 Reid McKenzie
# --MIT License-----------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#  StdLib imports...
from ConfigParser import ConfigParser
from subprocess import Popen
import getopt
import sys
import md5
import os

# Depend. imports...
import gobject
import pygtk
import pygst
import gtk
pygtk.require('2.0')
pygst.require('0.10')
gobject.threads_init()
import gst

class Voximp(object):
    dial = None

    def __init__(self, config, dbg=False):
        self.config = config
        self.dbg = dbg

        self.init_gst()
        self.pipeline.set_state(gst.STATE_PLAYING)

    def init_gst(self):
        self.pipeline = gst.parse_launch('alsasrc ! audioconvert ! audioresample '
                                         + '! vader name=vad auto-threshold=true '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)
        asr.set_property('lm', self.config['lm'])
        asr.set_property('dict', self.config['dict'])
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

    def partial_result(self, hyp, uttid):
        if(self.dbg): print "partial: %s" % hyp

    def final_result(self, hyp, uttid):
        if(self.dbg): print "final: %s" % hyp
        prog = ''
        command = None
        if self.dial is not None:
            if hyp == 'YES':
                self.dial.response(gtk.RESPONSE_YES)
            else:
                self.dial.response(gtk.RESPONSE_NO)
        elif hyp in self.config:
            prog = self.config[hyp]['cmd']
            command = hyp
        #else:
            #values = hyp.split(' ')
            #if len(values) <= 1:
                #return
            #if values[0] in progswithargs:
                #prog = progswithargs[values[0]] + ' ' + ' '.join(values)
                #command = values[0]
            #else:
                #for value in values:
                    #self.final_result(value, 0)
        if prog:
            if(self.dbg):
                print "command is %s" % command

            Popen(prog, shell=True)

    def confirm(self, prog):
        if(self.dbg): print "Confirming %s" % prog
        self.dial = gtk.MessageDialog(message_format = "Confirm?", type=gtk.MESSAGE_QUESTION)
        self.dial.format_secondary_markup("Say <b><i>yes</i></b> or <b><i>no</i></b>")
        self.dial.prog = prog
        self.dial.show_all()
        self.dial.connect("response", self.confirmCallback)

    def confirmCallback(self, dialog, response_id):
        if(self.dbg): print "callback called back"
        if response_id == gtk.RESPONSE_YES:
            p = Popen(dialog.prog, shell=True)
            self.dial.destroy()
        self.dial = None

__version__ = '0.1.0'

__usage__ = """
Usage: voximp.py [options]
Options:
    -v, --version     show program version and exit
    -h, --help        show this help message and exit
About:
    Voximp version {0}, a highly configurable voice command interface for
    Linux. Copyright 2008 Ben Duffield (bavardage@archlinux.us), updated and
    maintained by Reid McKenzie (rmckenzie92@gmail.com)
""".format(__version__)

def corpus(config):
    words = config.keys()
    corpusText =  "\n".join(words)
    filename = os.path.join(os.getcwd(), 'corpus.txt')
    corp = open(filename, 'w')
    corp.write(corpusText)
    corp.flush()
    corp.close()

    print "Corpus saved to %s" % filename
    print "Now visit http://www.speech.cs.cmu.edu/tools/lmtool.html"
    print "  ==> choose the corpus file, click COMPILE KNOWLEDGE BASE"
    print "  ==> save the three files to ~/.config/voximp/"
    print "  ==> edit ~/.config/voximp/voximpconf.py and set the languagemodel string to the appropriate value \n\t- e.g. if the files are named 4766.dic, 4766.lm and 4766.sent, set languagemodel = '4766'"


if __name__ == '__main__':
    config_dir  = os.path.expanduser("~/") + '.config/voximp/'
    config_file = 'voximp.conf'
    config = None

    if not os.path.isdir(config_dir):
        # the configurations are non-existant as far as this code can tell
        os.makedirs(config_dir)
        open(config_dir + os.sep + config_file, 'w').write('\n') # touch conf file
        print "[FATAL] No configuration file found.\n" +\
              ".......     Check that ~/.config/voximp/voximp.conf exists and contains command\n" +\
              ".......     specifications as documented.\n" +\
              "[EXITING]"
        exit(1)

    else:
        # the configs are assumed to be present, check hash of config file to
        # see if the language files need to be recalculated.
        #
        # the hash file is '~/.config/voximp/hash'
        # the config file is '~/.config/voximp/voximp.conf'

        hf = open(config_dir + 'hash', 'r+')
        cf = config_dir + 'voximp.conf'

        hash = md5.new()
        hash.update(open(cf).read())

        a = ConfigParser()
        a.read(cf)

        config = {b: dict(a.items(b)) for b in a.sections()}

        if(hash.hexdigest() != hf.read()):
            # this is the recalculate language file case
            corpus(config)

            # and update the hash...
            hf.seek(0, 0)
            hf.write(hash.hexdigest())
            hf.close()

        language_file = os.path.join(config_dir, config['__settings__']['lang'])

        config['hmm'] = '/usr/share/pocketsphinx/model/hmm/wsj1'
        config['lm'] = '{0}.lm'.format(language_file)
        config['dict'] = '{0}.dic'.format(language_file)

    opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "version"])

    for opt, _ in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()

        elif opt in ("-v", "--version"):
            version()
            sys.exit()

    app = Voximp(config)
    gtk.main()

