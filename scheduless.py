import stackless
import logging
from twiless import send_stackless_activity
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
    self.dbg('Stackless Operation End')
    self.launched+= 1
    if self.each and not self.launched % self.each:
      send_stackless_activity(self.maop)

  def launch_scop(self):
    self.dbg('Launching Stackless Operation')
    if self.blocked: return
    d= send_stackless_activity(self.scop)
    d.addCallback(self.end_scop)
    d.addErrback(self.errb)

  def block(self):
    self.dbg('Blocking Scheduler')
    self.blocked= 1

class FooScheduless(IWuScheduler):
  freq= 3
  def scop(self, *a, **kw):
    print 'scop'
  def errb(self, *a, **kw):
    print 'an error occurred!!!'
