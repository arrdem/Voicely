#!/usr/bin/env python2
#
# Copyright 2008 Ben Duffield as Voximp,
#           2012 Reid McKenzie as Voicely
#
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
#

#  StdLib imports...
from ConfigParser import ConfigParser
from subprocess import Popen
import getopt
import sys
import md5
import os


__version__ = '0.1.0'

__v_usage__ = """
Usage: Voicely.py [options]
Options:
    -v, --version     show program version and exit
    -h, --help        show this help message and exit
    -c, --config dir  use a nonstandard config file location
    -dbg              enable some debugging printing

About:
    Voicely version {0}, a highly configurable voice command interface for
    Linux. Copyright 2008 Ben Duffield (bavardage@archlinux.us) as Voximp,
    updated and maintained by Reid McKenzie (rmckenzie92@gmail.com)
""".format(__version__)

__no_conf_file_err__ = """
[FATAL] No configuration file found.
....    Check that {0}Voicely.conf exists and contains command
....    specifications as documented in the README.
[EXITING]
"""

__no_conf_dir_err__ = """
[FATAL] No configuration dir found.
....    Check that ~/.config/Voicely/Voicely.conf exists and contains command
....    specifications as documented in the README.
[EXITING]
"""

__hash_not_found__ = """
[FATAL] No checksum file (or a non-matching checksum file) was found for your
        configuration file. As a result you need to follow the instructions
        below and generate new Sphinx corpus files before Voicely will support
        your new instructions.
"""


class Voicely(object):
    dial = None

    def __init__(self, config, dbg=False):
        self.config = config
        self.dbg = dbg

        self.init_gst()
        self.pipeline.set_state(gst.STATE_PLAYING)

    def init_gst(self):
        self.pipeline = gst.parse_launch(
            'alsasrc ! audioconvert ! audioresample ! ' +
            ' vader name=vad auto-threshold=true ' +
            '! pocketsphinx name=asr ! fakesink')

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
        if(self.dbg):
            print ("partial: %s" % hyp)

    def final_result(self, hyp, uttid):
        if(self.dbg):
            print ("final: %s" % hyp)

        val = None
        if self.dial is not None:
            if hyp == 'YES':
                self.dial.response(gtk.RESPONSE_YES)
            else:
                self.dial.response(gtk.RESPONSE_NO)
        elif hyp in self.config:
            val = self.config[hyp]
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
        if val:
            if(self.dbg):
                print "command is %s" % val['cmd']

            if 'msg' in val:
                print "[COMMAND DEBUG]", val['msg']

            Popen(val['cmd'], shell=True)

    def confirm(self, prog):
        if(self.dbg):
            print "Confirming %s" % prog

        self.dial = gtk.MessageDialog(message_format="Confirm?",
                                      type=gtk.MESSAGE_QUESTION)
        self.dial.format_secondary_markup(
                                    "Say <b><i>yes</i></b> or <b><i>no</i></b>")
        self.dial.prog = prog
        self.dial.show_all()
        self.dial.connect("response", self.confirmCallback)

    def confirmCallback(self, dialog, response_id):
        if(self.dbg):
            print "callback called back"

        if response_id == gtk.RESPONSE_YES:
            p = Popen(dialog.prog, shell=True)
            self.dial.destroy()
        self.dial = None


def corpus(config):
    words = set(config.keys())
    if '__settings__' in words:
        words.remove('__settings__')
        if 'keyphrase' in config['__settings__']:
            words.add(config['__settings__']['keyphrase'])

    corpusText = "\n".join(words)
    filename = os.path.join(os.getcwd(), 'corpus.txt')
    corp = open(filename, 'w')
    corp.write(corpusText + '\n')
    corp.flush()
    corp.close()

    print ("Corpus saved to %s" % filename)
    print """Now visit http://www.speech.cs.cmu.edu/tools/lmtool.html
  ==> choose the corpus file, click COMPILE KNOWLEDGE BASE"
  ==> save the three files to ~/.config/Voicely/"
  ==> edit ~/.config/voicely/voicely.conf and set the lang field of the
      __settings__ section to the appropriate value - e.g. if the files are
      named 4766.dic, 4766.lm and 4766.sent, set lang = 4766"""


if __name__ == '__main__':
    config_dir = os.path.expanduser("~/") + '.config/voicely/'
    config_file = 'voicely.conf'
    config_data = None

    c_flag = False
    c_dbg_flag = False
    for opt in sys.argv[1:]:
        if c_flag:
            c_flag = False

            if(os.path.exists(opt) and os.path.isdir(opt)):
                config_dir = opt

                if opt[-1] != os.sep:
                    config_dir += os.sep
                continue

            else:
                print ("[FATAL] Specified config dir does not exist")
                exit(2)

        if opt in ("-h", "--help"):
            print __v_usage__
            sys.exit()

        elif opt in ("-v", "--version"):
            print __version__
            sys.exit()

        elif opt in ('-c', '--config'):
            c_flag = True

        elif opt in ('-dbg'):
            c_dbg_flag = True

        else:
            print ("[WARNING] Unknown option %s" % opt)

    # Depend. imports...
    import gobject
    import pygtk
    import pygst
    import gtk
    pygtk.require('2.0')
    pygst.require('0.10')
    gobject.threads_init()
    import gst

    if not (os.path.isdir(config_dir)):
        # the configurations are non-existant as far as this code can tell
        os.makedirs(config_dir)
        open(config_dir + config_file, 'w').write('\n')
        print __no_conf_dir_err__
        exit(1)

    elif not os.path.exists(config_dir + config_file):
        open(config_dir + config_file, 'w').write('\n')
        print __no_conf_file_err__.format(config_dir)
        exit(1)

    else:
        # the configs are assumed to be present, check hash of config file to
        # see if the language files need to be recalculated.
        #
        # the hash file is '~/.config/Voicely/hash'
        # the config file is '~/.config/Voicely/Voicely.conf'

        hf = config_dir + 'hash'
        cf = config_dir + config_file

        hash = md5.new()
        hf_data = open(hf).read() if os.path.exists(hf) else ""
        hash.update(open(cf).read())

        a = ConfigParser()
        a.read(cf)

        config_data = None

        if a.getboolean('__settings__', 'use_keyphrase'):
            ph = a.get('__settings__', 'keyphrase').upper()
            config_data = {(ph + " " + b.upper() if b != '__settings__' else b): dict(a.items(b)) for b in a.sections()}

            if c_dbg_flag:
                for k in config_data:
                    print k, config_data[k]

        else:
            config_data = {b.upper(): dict(a.items(b)) for b in a.sections()}

        if(hash.hexdigest() != hf_data):
            print __hash_not_found__
            # this is the recalculate language file case
            corpus(config_data)

            # and update the hash...
            hf = open(hf, 'w')
            hf.write(hash.hexdigest())
            hf.close()
            exit(1)

        language_file = os.path.join(config_dir,
                                     config_data['__settings__']['lang'])

        config_data['hmm'] = '/usr/share/pocketsphinx/model/hmm/wsj1'
        config_data['lm'] = '{0}.lm'.format(language_file)
        config_data['dict'] = '{0}.dic'.format(language_file)

    app = Voicely(config_data, dbg=c_dbg_flag)
    gtk.main()
