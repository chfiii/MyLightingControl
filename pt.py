#!/usr/bin/env python

import sys, time, os, types, getpass, math as m, calendar as cal
import CM19aDriver
from datetime import date as dt

DEBUG=None

def getChristmas() :
    today = dt.today()
    if today.month in [1,12] :
        return 4
    else:
        return 3


def parsecommandline(argv) :
    Command = None
    
    HList = "ABCDEFGHIJKLMNOP"
    
    Action = ['ON', 'OFF', 'BRIGHT', 'DIM']
    
    if not argv[1].upper() in HList:
       print "Invalid House Code: " + argv[1].upper()
       return (1,0,0)
    else:
       if DEBUG : print "There!"
    
    if argv[2] == '0':
        if not argv[3].upper() in ['ALLON', 'ALLOFF'] :
            print 'Invalid command for Unit code %d: %s' % (int(argv[2]), argv[3].upper())
            return (2,0,0)
        else:
    	    Command = 'Issuing Command: %s %d %s' % (argv[1].upper(), int(argv[2]), argv[3].upper())
    	    if DEBUG : print Command
    elif int(argv[2]) > 16 :
        print 'Range error for Unit code %d: ' % (int(argv[2]))
        return (2,0,0)
	
    elif not argv[3].upper() in Action :
        print 'Invalid command for Unit code %d: %s' % (int(argv[2]), argv[3].upper())
        return (3,0,0)
    else:
        Command = 'Issuing Command: %s %d %s' % (argv[1].upper(), int(argv[2]), argv[3].upper())
        if DEBUG : print Command
    
    return (argv[1].upper(), argv[2], argv[3].upper())

def sunOffset(span, jdate):
    juliandate = jdate + 10
    if juliandate > 365: juliandate -= 365
    arg = 2.*m.pi*juliandate/365
    span *= 60			# convert minutes to seconds
    factor = int(.5*span*(1.-m.cos(arg)))
    return factor

def secsToHourMinSecond(s):
    # Assumes timespan < 1 day
    s0 = s
    m = s//60
    h = m//60
    m -= 60*h
    s -= 60*(60*h+m)
    return (s0,h,m,s)


def waitForStart(span, starttime, starttz):
    
    # Figure out basic timezone stuff
    cursecs = time.time()
    locTime = time.localtime(cursecs)
    utcTime = time.gmtime(cursecs)
    tzDiff = utcTime.tm_hour - locTime.tm_hour

    # Decide how long we need to wait based on the required time/timezone
    (h,m) = starttime.split(':')
    startHour = int(h)
    startMin  = int(m)
    if starttz == None:
        waitMin = 60*(startHour-utcTime.tm_hour) + (startMin - utcTime.tm_min)
    else:
        waitMin = 60*(startHour-locTime.tm_hour) + (startMin - locTime.tm_min)

    waitSecs = 60.0*waitMin
    newTime = time.localtime(cursecs + waitSecs)
    julianDate = newTime.tm_yday

    secs = sunOffset(span, julianDate)	# get the sun cycle offset

    sleeptime = secs + waitSecs
    lt = time.localtime(cursecs+sleeptime)	# now add it to the requred start time

    if lt[3] > 12:
        h = str(lt[3] - 12)
	ampm = 'PM'
    else:
        h = str(lt[3])
	ampm = 'AM'

    m = lt[4]

    waitTime = '(%d seconds [or %d Hours,%.2d Minutes,%d Seconds])' % secsToHourMinSecond(sleeptime)

    print
    print "**************"
    print time.strftime("%A %m/%d/%y %H:%M:%S")
    print
    msg = 'Lights coming on at %s:%.2d%s %s' % (h,m,ampm,waitTime)
    print msg
#
# PUT YOUR CELL TEXING ADDRESS IN 1-LINE LOCAL FILE: "mycellnumber"
#     - Example: 2125551212@vtext.com\n
#
    with open("./mycellnumber", "r") as f:
        cellPhone = f.read().replace('\n','')

    username = getpass.getuser()
    msg1 = "/root/bin/mymail.pl %s %s@chf3.org '%s'" % (cellPhone, username, msg)

    os.system(msg1)
    time.sleep(sleeptime)


def determineActions(mode) :
    List = [ 
            [('a', '8', 'on')], 
	    [('a', '8', 'on'), ('a', '3', 'on')], 
	    [('a', '1', 'on'), ('a', '2', 'on'), ('a', '3', 'on'), ('a', '8', 'off')], 
	    [('a', '8', 'off')],
	    [('a', '0', 'alloff')],
	    [('a', '0', 'alloff'), ('a', '3', 'on')],
	    [('a', '8', 'on'), ('a', '1', 'off'), ('a', '2', 'off')], 
	    [('a', '3', 'on')]
	   ]
    return List[mode]


if __name__ == '__main__' :
    if len(sys.argv) <=1 :
        # no command line arguments given
        print "Command line usage:"
        print "   Lights.py -c house&unitcode ON/OFF"
        print "   e.g. Lights.py A 1 ON     # Turns on device A1, returns 1 if OK, 0 if not"
        print "   e.g. Lights.py A 1 ALLOFF # Turns off all housecode A"
	print "             or"
	print "   Lights.py timespan lightmode starttime(hour:minute) [nonzero for localtime]"
	print "   e.g.  Lights.py 160 1 21:00 # allows 160 minute sine curve"
	print "                               # to match sun (starts at 2100 UTC)"

	sys.exit(2)

    # Parse the command line
    if sys.argv[1] == '-c' :
	# Command Line Processing - no wait, only 1 command allowed
        (a,b,c) = parsecommandline(sys.argv[1:])
	if type(a) is int :
	    print "Error parsing house input, return value is " + str(a)
	    exit(a)
	action = [(a,b,c)]
    else :
	# Cron Entry Point
    	timespan = int(sys.argv[1])
        lightMode = int(sys.argv[2])
        action = determineActions(lightMode)
        startTime = sys.argv[3]
        if len(sys.argv) > 4: 
	    startTZ = sys.argv[4]
	else:
	    startTZ = None
        waitForStart(timespan, startTime, startTZ)
    
    LOGFILE = 'cm19.log.' + str(os.getpid())
    log = CM19aDriver.startLogging(logfile=LOGFILE)
    print "\nInitializing..."
    cm19a = CM19aDriver.CM19aDevice(1, log, polling = False)  #Initialize device
    if not cm19a.initialised > 0:
        print "CM19a Driver: failed to initialize - See log for errors\n"
    else:
        for args in action :
            (House, Unit, Action) = args
	    cm19a.send(House, Unit, Action)
            print "Return: %s %d %s" % (House, Unit, Action) 

    cm19a.finish()

