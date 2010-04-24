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
def _mc():
  mc = memcache.Client(['127.0.0.1:11211'], debug=0)
  return mc

mc= _mc()

class TwichedMc:

  def __init__(self, h= '127.0.0.1', p= 11211, d= 0):
    self.s= ['%s:%d' % (h,p)], d
    self.mc = memcache.Client(*self.s)

  def reinit(self):
    logging.debug('Reinitializing Memcache Client...')
    self.mc = memcache.Client(*self.s)

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

mc= TwichedMc()

def key_values(f, prefix, skipfirst, *a, **kw):
  fname= f.__name__
  if not a and not kw:
    return (fname, prefix,)
  varnames= f.func_code.co_varnames[:f.func_code.co_argcount]
  if skipfirst:
    varnames= varnames[1:]
  vardefas= f.func_defaults or {}
  n= len(varnames) - len(vardefas)
  t= [fname, prefix]
  i= -1
  for i, ar in enumerate(a):
    t.append(ar)
  if skipfirst:
    j= i+ 1
  else: j= i
  for ar in varnames[i+1:]:
    v= ar in kw and kw[ar] or vardefas[j-n]
    t.append(v)
  return tuple(t)

def cache(func, prefix= '', skipfirst= 0):
  def _(*a, **kw):
    t= key_values(func, prefix, skipfirst, *a, **kw)
    key= str(hash(t))
    obj = mc.get(key)
    if obj is not None:
      return obj, key, True
    ret = func(*a, **kw)
    mc.set(key, ret)
    return ret, key, False
  return _

def uncache(func, *a, **kw):
  t= key_values(func, '', 0, *a, **kw)
  key= str(hash(t))
  mc.mc.delete(key)

class Twiched:
  """ Simply Sublass Providing _loadValues() """
  def __init__(self, twichedSetUp= None, useInstanceId= 1, initValue= None):
    self.keys= set()
    self.useInstanceId= useInstanceId
    if twichedSetUp:
      key= key_values(self._loadValues, self._getTwichedPrefix(), 1)
      mc.set(str(hash(key)), twichedSetUp)
    self._loadValues= cache(self._loadValues, self._getTwichedPrefix(), 1)
    if initValue:
      self._initValue= initValue

  def _onLoadValues(self, *a, **kw):
    pass

  def _getTwichedPrefix(self):
    if self.useInstanceId:
      if hasattr(self, '_twicedPrefix'):
        return self._twicedPrefix
      ri= randint(1, 10000)
      res= str(id(self)) + str(self.__class__) + str(ri)
      self._twicedPrefix= res
      return res
    else:
      return str(self.__class__)

  def getValues(self, *a, **kw):
    if hasattr(self, '_initValue') and self._initValue is not None:
      return self._initValue
    res, key, cached= self._loadValues(*a, **kw)
    if not cached:# or not getattr(self, '_twichedInitialized', False):
      self._onLoadValues(res)
    #self._twichedInitialized= 1
    self.keys.add(key)
    return res

  def refresh(self):
    if hasattr(self, '_initValue'):
      self._initValue= None
    mc.mc.delete_multi(self.keys)
    self.keys= set()


class Foo(Twiched):
  def _loadValues(self, *a, **kw):
    return [1,2,3]

