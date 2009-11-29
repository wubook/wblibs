# Copyright (c) 2009, Federico Tomassini AKA efphe (effetom AT gmail DOT com)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the University of California, Berkeley nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#
# This File is Part of WuBook Labs Researches:
#   http://wubook.net/
#   http://en.wubook.net/
#
# This file is inspired by:
#
#  http://www.tempestnetworks.com/11/multi-threaded-twisted-stackless-integration/
#

import stackless
import logging
from twisted.internet import defer, reactor

""" 
  This module allows to run normal code suites as deferred objects,
  without creating expensive threads, but using stackless.

  In fact, twiless borns to substitute deferToThread() with a less
  expensive deferToStackless

  There is a limit: deferred suites are FIFO'ed and not concurrent.

  Design: your application has two main loops: Twisted Loop and 
  Stackless Loop. Both loops are neverending and we need to stop
  them to stop app. 

  The usage of deferToStackless() installs a SystemEventTrigger
  so that when reactor.stop() is called, Stackless scheduler
  will stop too.

  This is completely automatic. So, don't worry: just use
  deferToStackless() async'ing your f()
"""

TWILES_EXIT_KEY= 'exit'

def _aerror(*a, **kw):
  logging.error('AsyncIt Error: %s' % str(a[0]))

class Twiless:

  from threading import Lock
  _stc= stackless.channel()
  _initalized= 0
  _running= 1
  _initlock= Lock()
  del Lock

  @staticmethod
  def sendExit():
    Twiless._stc.send((TWILES_EXIT_KEY,1,1,1))
  @staticmethod
  def stopStacklessThread():
    Twiless.sendExit()

  @staticmethod
  def _underground(d, f, *a, **kw):
    """ This function runs f() on stackless, making sure that,
        when done, the deferred d will call back."""
    md= defer.maybeDeferred(f, *a, **kw)
    def _cb(x):
      reactor.callFromThread(d.callback, x)
    def _eb(x):
      reactor.callFromThread(d.errback, x)
    md.addCallback(_cb)
    md.addErrback(_eb)

  @staticmethod
  def launchStacklessThread():
    if Twiless._initalized: 
      return
    Twiless._initlock.acquire()
    if not Twiless._initalized:
      Twiless._initalized= 1
      d= reactor.callInThread(Twiless.stackless_thread)
      st= reactor.addSystemEventTrigger
      stopf= Twiless.stopStacklessThread
      st('before', 'shutdown', stopf)
    Twiless._initlock.release()

  @staticmethod
  def stackless_thread():
    """ 
      Runs the Stackless thread. A Channel is created, which
      wait for activities. Once had it, it launch a function
      on background.

      You must run a stackless_thread doing something like:

        reactor.callInThread(stackless_thread)

      After that, to defer a function f, simply do:
        
        df= send_stackless_activity(f, *a, **kw)

      df is a deferred."""
    while Twiless._running:
      try:
        d, f, a, kw= Twiless._stc.receive()
        if d == TWILES_EXIT_KEY: 
          Twiless._running= 0
          break
        t= stackless.tasklet(Twiless._underground)
        t(d, f, a, kw)
        stackless.schedule()
      except Exception, ss:
        pass

  @staticmethod
  def asyncIt(f, *a, **kw):
    if not Twiless._initalized:
      Twiless.launchStacklessThread()
    d= defer.Deferred()
    t= stackless.tasklet(Twiless._stc.send)
    t((d, f, a, kw))
    stackless.schedule()
    d.addErrback(_aerror)
    return d

deferToStackless= Twiless.asyncIt
