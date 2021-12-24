#!/usr/bin/env python3

'''
                    ___           ___           ___ 
        ___        /\__\         /\  \         /\  \
       /\  \      /::|  |       /::\  \       /::\  \
       \:\  \    /:|:|  |      /:/\:\  \     /:/\ \  \
       /::\__\  /:/|:|  |__   /::\~\:\  \   _\:\~\ \  \
    __/:/\/__/ /:/ |:| /\__\ /:/\:\ \:\__\ /\ \:\ \ \__\
   /\/:/  /    \/__|:|/:/  / \:\~\:\ \/__/ \:\ \:\ \/__/
   \::/__/         |:/:/  /   \:\ \:\__\    \:\ \:\__\
    \:\__\         |::/  /     \:\ \/__/     \:\/:/  /
     \/__/         /:/  /       \:\__\        \::/  /
                   \/__/         \/__/         \/__/


    File:          grove_pi_interface.py


    Purpose:       Due to problems with interacting
                   grovePi board from different processes, 
                   we use this interface class for all
                   the traffic between the python
                   interpreter and the driver which
                   interacts with the GrovePi board.
                   The GrovePi interactor classs/thread
                   must be used as singleton only.

                   Interactor class is based on
                   the thread class of the python 
                   threading module.


    Remarks:       -


    Author:        P. Leibundgut <leiu@zhaw.ch>


    Date:          10/2018

'''

import sys
import threading
import grovepi

from queue import Queue


DIGITAL_READ  = grovepi.digitalRead
ANALOG_READ   = grovepi.analogRead

DIGITAL_WRITE = grovepi.digitalWrite
ANALOG_WRITE  = grovepi.analogWrite


# Has to be protected with a mutex.
# It is used from the main application
# (signal handler) terminate the
# member queue processing.
running = True


# TX queue towards the grovepi board
# all traffic goes through this queue
grovepi_tx_queue = Queue()


def flush_queue( q ):
    while not q.empty():
        q.get()
        q.task_done()


class GrovePiInteractor( threading.Thread ):

    def __init__( self ):
        # must be called ...
        threading.Thread.__init__( self )
        self.lock = threading.Lock()


    def run( self ):
        self.process_tx_queue()


    def process_tx_queue( self ):
        self.lock.acquire()
        running_local = running
        self.lock.release()

        while running_local:
            # value must be a tuple of 1 or 2:
            # value[ 0 ] is a InteractorMember
            # value[ 1 ] is the value to send
            #            towards the grovepi board
            #            if the member is an output
            value = grovepi_tx_queue.get()
            if value is None:
                break

            self.work_queue_entry( value )
            grovepi_tx_queue.task_done()

            self.lock.acquire()
            running_local = running
            self.lock.release()


    @staticmethod
    def work_queue_entry( value ):
        member = value[ 0 ]
        input_val = int( 0 )

        if not member.pin_mode_set:
            grovepi.pinMode( member.connector, member.direction )
            member.pin_mode_set = True

        if member.direction == 'OUTPUT':
            output_val = value[ 1 ]
            try:
                member.grovepi_func( member.connector, int( output_val ) )
            except IOError:
                print( "Error in writing to sensor at pin " + str( member.connector ) )

        elif member.direction == 'INPUT':
            try:
                input_val = member.grovepi_func( member.connector )
            except IOError:
                print( "Error in reading sensor at pin " + str( member.connector ) )

            # Always put an item to the rx queue of the calling
            # thread, even if the grovepi board reports an error
            # Othewise the consumer thread will not receive
            # an answer on his rx_queue.get() call and will block
            # forever. (We set no timeout in the get() call)
            member.rx_queue.put( input_val )


    def stop_interactor( self ):
        global running
        print( "Stopping the GrovePi Interactor." )
        self.lock.acquire()
        running = False
        self.lock.release()
        grovepi_tx_queue.put( None )



class InteractorMember( object ):

    def __init__( self, connector, direction, grovepi_func ):

        self.sanity_check_connector( connector )
        self.sanity_check_direction( direction )

        self.connector = connector
        self.direction = direction

        if self.direction == 'INPUT':
            self.rx_queue = Queue()
        else:
            self.rx_queue = None

        self.tx_queue = grovepi_tx_queue
        self.grovepi_func = grovepi_func
        self.pin_mode_set = False


    @staticmethod
    def sanity_check_connector( connector ):
        err = False

        if not isinstance( connector, int ):
            err = True
            print( "Connector has the wrong type ..." )
        else:
            if not ( connector >= int( 0 ) and connector <= int( 8 ) ):
                err = True
                print( "Connector is in the wrong range." )

        if err is True:
            sys.exit( 1 )


    @staticmethod
    def sanity_check_direction( direction ):
        err = False

        if not isinstance( direction, str ):
            err = True
            print( "Direction has the wrong description string." )
        else:
            if not ( direction == 'INPUT' or direction == 'OUTPUT' ):
                err = True
                print( "Direction is a wrong description string." )

        if err is True:
            sys.exit( 1 )

