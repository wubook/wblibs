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
    self.mc = memcache.Client(*self.s)

  def get(self, k):
    try:
      return self.mc.get(k)
    except:
      self.reinit()
  def set(self, k, v):
    try:
      return self.mc.set(k, v)
    except:
      self.reinit()

mc= TwichedMc()

def key_values(f, prefix, skipfirst, *a, **kw):
  if not a and not kw:
    return (prefix,)
  varnames= f.func_code.co_varnames
  if skipfirst:
    varnames= varnames[1:]
  vardefas= f.func_defaults or {}
  n= len(varnames) - len(vardefas)
  t= [prefix]
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
    if not obj:
      ret = func(*a, **kw)
      mc.set(key, ret)
      return ret, key, False
    return obj, key, True
  return _

class Twiched:
  """ Simply Sublass Providing _loadValues() """
  def __init__(self, twichedSetUp= None):
    self.keys= set()
    #if twichedSetUp:
      #key= key_values(self._loadValues, str(self.__class__), 1)
      #mc.set(str(hash(key)), twichedSetUp)
    self._loadValues= cache(self._loadValues, str(self.__class__), 1)

  def _onLoadValues(self, *a, **kw):
    pass

  def getValues(self, *a, **kw):
    res, key, cached= self._loadValues(*a, **kw)
    self._onLoadValues(res)
    self.keys.add(key)
    return res

  def refresh(self):
    mc.mc.delete_multi(self.keys)
    self.keys= set()


class Foo(Twiched):
  def _loadValues(self, *a, **kw):
    return [1,2,3]

