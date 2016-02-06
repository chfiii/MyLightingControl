#!/usr/bin/env python

"""
Control when lights (X10) are turned on/off automatically via Crontab

Requires:
	CM19aDriver version  0.11 or above

"""

import sys, time, os, types
from datetime import date as dt
import pt
import CM19aDriver

REFRESH = 1.0

DAYS = ['mon', 'tues', 'wed', 'thu', 'fri', 'sat', 'sun']


# MAIN
if __name__ == '__main__' :
    if len(sys.argv) <=1 :
        # no command line arguments given
        print "Command line usage:"
        print "   Lights.py -c house&unitcode ON/OFF"
        print "   e.g. Lights.py A 1 ON     # Turns on device A1, returns 1 if OK, 0 if not"
        print "   e.g. Lights.py A 0 ALLOFF # Turns off all housecode A"
	print "             or"
	print "   Lights.py timespan lightmode starttime(hour:minute) [nonzero for localtime]"
	print "   e.g.  Lights.py 160 1 21:00 # allows 160 minute sine curve"
	print "                               # to match sun (starts at 2100 UTC)"
	print "   Lights.py -off lightmode  # valid modes are 3 and 4"
	print "   Lights.py -xmasflip lightmode  # valid modes are 2 or 6"

	sys.exit(2)

    # Make sure we are in the Lights directory
    os.chdir('/home/chf/Lights')

    # Parse the command line
    if sys.argv[1] == '-c' :
	# Command Line Processing - no wait, only 1 command allowed
        (a,b,c) = pt.parsecommandline(sys.argv[1:])
	if type(a) is int :
	    print "Error parsing house input, return value is " + str(a)
	    exit(a)
	action = [(a,b,c)]
    elif sys.argv[1] == '-xmasflip' :
        if len(sys.argv) > 2:
            lightMode = int(sys.argv[2])
	    if lightMode not in [2, 6, 7] :
	        print "Error:  Got " + str(lightMode) + ", only 2 or 6 allowed!"
		exit(21)
        else :
            lightMode = 6
        action = pt.determineActions(lightMode)
    elif sys.argv[1] == '-off' :
        lightMode = pt.getChristmas()
	action = pt.determineActions(lightMode)
    else :
	# Cron Entry Point
    	timespan = int(sys.argv[1])
        lightMode = int(sys.argv[2])
        action = pt.determineActions(lightMode)
        startTime = sys.argv[3]
        if len(sys.argv) > 4: 
	    startTZ = sys.argv[4]
	else:
	    startTZ = None
        
        pt.waitForStart(timespan, startTime, startTZ)
    
    
    print
    print "*************************"
    print time.strftime("%A %m/%d/%y %H:%M:%S")
    mypid = os.getpid()
    #LOGFILE = '/home/chf/Log/cm19aLog.' + str(mypid)
    LOGFILE = '/home/chf/Log/cm19a.log'
    log = CM19aDriver.startLogging(progname="Lights.py",logfile=LOGFILE)
    print "\nInitializing..."
    cm19a = CM19aDriver.CM19aDevice(1, log, polling = False)  #Initialize device
    if not cm19a.initialised > 0:
        print "CM19a Driver: failed to initialize - See log for errors\n"
        log.error ('CM19a Driver: failed to initialize')
        cm19a.finish()
        sys.exit(5)

    else:
        for args in action :
            (House, Unit, Action) = args
 	    if not House in [ 1, 2, 3 ] :
	        result = cm19a.send(House, Unit, Action)
		if not result:
		    print 'Command failed: %s%s %s' % (House, Unit, Action)
	    time.sleep(5)

    cm19a.finish()
    sys.exit(0)

