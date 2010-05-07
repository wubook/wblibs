# Copyright (c) 2009, Federico Tomassini AKA efphe (effetom AT gmail DOT com)
# Copyright (c) 2009, Marco Giusti AKA nohero (marco.giusti AT gmail DOT com)
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
# This File is Part of WuBook Labs Researches (Tourism Technologies as
# booking online engine and channel management):
#
#   http://wubook.net/
#   http://en.wubook.net/
#

from random import randint
import logging
import memcache
_mserver= (['127.0.0.1:11211'], 0)

class TwichedMc:

  def __init__(self):
    #self.s= ['%s:%d' % (h,p)], d
    #self.s= ['%s:%d' % (h,p)], d
    self.mc = memcache.Client(*_mserver)

  def reinit(self):
    logging.debug('Reinitializing Memcache Client...')
    self.mc = memcache.Client(*_mserver)

  def connected(self):
    return self.mc.servers[0].socket

  def get(self, k):
    if not self.connected():
      self.reinit()
    try:
      return self.mc.get(k)
    except:
      self.reinit()
  def set(self, k, v):
    if not self.connected():
      self.reinit()
    try:
      return self.mc.set(k, v)
    except:
      self.reinit()

#mc= TwichedMc()
mc= None
def initTwiched(mserver= None, mfile= None, dontkill= False):
  if mserver:
    global _mserver
    _mserver= mserver
  global mc
  mc= TwichedMc()
  if mfile:
    import os
    bfile= os.path.abspath(mfile)
    ufile= bfile + '.unix'
    pfile= bfile + '.pid'
    if not dontkill and os.path.isfile(pfile):
      os.system('kill `cat %s`' % pfile)
    os.system('memcached -s %s -d -P %s' % (ufile, pfile))

def initUnixTwiched(tfile):
  initTwiched((['unix:%s.unix' % tfile],0), tfile)

def key_values(f, prefix, skipkeys, *a, **kw):
  def _s(t):
    print (f.__name__, prefix) + t
    res= hash((f.__name__, prefix) + t )
    return str(res)

  fname= f.__name__
  covars= f.func_code.co_varnames[:f.func_code.co_argcount]
  if not covars or (not a and not kw):
    return _s(tuple())

  tmp= []
  la= len(a)
  fdefs= f.func_defaults or []
  offs= len(covars) - len(fdefs)
  for n,k in enumerate(covars):
    if la > n:
      tmp.append(a[n])
    else:
      if k in kw: tmp.append(kw[k])
      else: tmp.append( fdefs[n-offs] )
  return _s(tuple(tmp))

def cache(func, prefix= '', normalreturn= 0, skipkeys= []):
  def _(*a, **kw):
    key= key_values(func, prefix, skipkeys, *a, **kw)
    obj = mc.get(key)
    if obj is not None:
      if not normalreturn:
        return obj, key, True
      return obj
    ret = func(*a, **kw)
    mc.set(key, ret)
    if not normalreturn:
      return ret, key, False
    else: return ret
  return _

def ncache(func, prefix= '', skipkeys= [], normalreturn= 1):
  return cache(func, prefix, normalreturn, skipkeys)

def uncache(func, *a, **kw):
  key= key_values(func, '', [], *a, **kw)
  mc.mc.delete(key)
