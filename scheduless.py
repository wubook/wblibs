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
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THISimport stackless
#
# This File is Part of WuBook Labs Researches:
#   http://wubook.net/
#   http://en.wubook.net/


import logging
from twiless import deferToStackless
from Queue import Queue
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

class IWuScheduler(Queue):
  """ Attrs:
    * freq ~> launch each N seconds
    * scop ~> scheduled operation, it takes no args
    wait ~> begin after N seconds
    lrun ~> make another tour before to shutdown if lrun
    wque ~> with queue. If True, implements Queue() (add_queue, get_queue)
    each ~> launc maop each N seconds (False otherwise) 
    errb ~> function called if scop() fails
  """

  def __init__(self):
    if getattr(self, 'wque', None):
      Queue.__init__(self)
    wait= getattr(self, 'wait', 0)
    self.dbg('Setting Up Scheduler with Delay = %d' % wait)
    reactor.callLater(wait, self._setuploop)

    each= getattr(self, 'each', 0)
    self.each= each 
    errb= getattr(self, 'errb', self._errb)
    self.errb= errb 

    self.launched= 0
    self.blocked= False

  def dbg(self, s):
    logging.debug('%s: %s' % (self.__class__, s))

  def _errb(self, *a, **kw):
    print a
    print kw

  def _setuploop(self):
    self.dbg('Setting Up Scheduler')
    self.lc= t= LoopingCall(self.launch_scop)
    t.start(self.freq, 0)

  def add_queue(self, obj):
    self.put(obj)

  def get_queue(self):
    _g= self.get
    res= []
    while 1:
      try: res.append(_g(False))
      except: break
    return res

  def end_scop(self, *a, **kw):
    self.launched+= 1
    self.dbg('Stackless (%d) Operation End' % self.launched)
    if self.each and not self.launched % self.each:
      self.dbg('Launching Maintanance Operation')
      deferToStackless(self.maop)

  def launch_scop(self):
    self.dbg('Launching Stackless Operation')
    if self.blocked: return
    d= deferToStackless(self.scop)
    d.addCallback(self.end_scop)
    d.addErrback(self.errb)

  def block(self):
    self.dbg('Blocking Scheduler')
    self.blocked= 1
