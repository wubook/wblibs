import logging
import stackless
from twisted.internet import defer, reactor

""" This module allows to run normal code suites as deferred objects,
    without creating expensive threads, but using stackless.

    There is a limit: deferred suites are FIFO'ed and not concurrent
"""

class Twiless:

  _stc= stackless.channel()
  _initalized= 0

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
  def stackless_thread():
    """ Runs the Stackless thread. A Channel is created, which
        wait for activities. Once had it, it launch a function
        on background.

        You must run a stackless_thread doing something like:

          reactor.callInThread(stackless_thread)

        After that, to defer a function f, simply do:
          
          df= send_stackless_activity(f, *a, **kw)

        df is a deferred."""
    while 1:
      try:
        d, f, a, kw= Twiless._stc.receive()
        t= stackless.tasklet(Twiless._underground)
        t(d, f, a, kw)
        stackless.schedule()
      except Exception, ss:
        logging.error(str(ss))

  @staticmethod
  def asyncIt(f, *a, **kw):
    if not Twiless._initalized:
      reactor.callInThread(Twiless.stackless_thread)
    d= defer.Deferred()
    t= stackless.tasklet(Twiless._stc.send)
    t((d, f, a, kw))
    stackless.schedule()
    return d

def send_stackless_activity(f, *a, **kw):
  """ This allows to launch a function in an async way. A Deferred is returned """
  return Twiless.asyncIt(f, *a, **kw)
