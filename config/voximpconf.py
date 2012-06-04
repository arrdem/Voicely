#################################
#  Voximp 0.0.1  Sample Config  #
#################################
# When you change this file you #
# must regenerate the language  #
# model files. Firstly call     #
# voximp -c and follow the      #
# instructions. Set	        #
# languagemodel below to approp #
# value                         #
#################################


languagemodel = '9882' #set this to something sensible

keycommand = {
	'RIGHT': "super+Right", #move one tag to the right
	'LEFT': "super+Left", #move one tag to the left
	'TERMINAL': "ctrl+grave", #spawn the terminal
	'CLOSE': "alt+F4", #close window
	'ENTER': "Return",
	'SAVE': "ctrl+s",
	'NEW': "ctrl+n",
	'TAB': "ctrl+Tab", #for seeing next firefox tab
	'BACKSPACE': "BackSpace",
	'CUT': "ctrl+x",
	'COPY': "ctrl+c",
	'PASTE': "ctrl+v"
}
for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
	keycommand[letter] = letter.lower() #add all the letters - yes this is a true python file, you can do w/e you want in here
programcommand = {
	'FIREFOX': "firefox",
	'NOTEPAD': "medit",
	'GOOGLE': "firefox www.google.com", #open google in a new tab in firefox
	'HIBERNATE': "sudo hibernate",
	'PLAY': "xmms2 play",
	'STOP': "xmms2 stop"
}

mousecommand = {
	'CLICK': '1', #leftclick
	'RIGHTCLICK': '3' #rightclick
}

progswithargs = {
	'ALERT': "notify-send" #just to demonstrate with arguments 
}

confirm = [ #anything listed here produces a confirm dialog before being executed
	'HIBERNATE' 
]
