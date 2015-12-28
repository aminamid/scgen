#!/bin/env python

import itertools
import time
import sched
import random
import yaml

import pprint

def _blackbox(spec):
    _index=[]
    _ll=[]
    _hash=[]
    for (k,v) in  spec.items():
       id=len(_index)
       _index.append(k)
       _ll.append([id for x in range(v["weight"])])
    _hash=list(itertools.chain(*_ll))
    while True:
        yield _index[random.choice(_hash)]

def _timer(sec_interval,sec_duration=0):
    s={
      "count": 0,
      "intrvl": sec_interval,
      "start_time": time.time(),
      "sched": sched.scheduler(time.time, time.sleep),
      "duration": sec_duration,
    }
    s["now"]=s["start_time"]
    while s["duration"] >= (s["now"] - s["start_time"]):
        s["sched"].enter(s["start_time"]+(s["intrvl"]*s["count"]) - time.time(), 1, lambda x=None: x, ())
        s["sched"].run()
        s["count"]+=1
        s["now"]=time.time()
        yield s["count"], s["now"]

def _timer_scenario(times,sequence):
    for x in range(times):
        for s in sequence:
            timer=_timer(1.0/s[1],s[2])
            for t in timer:
                yield s[0],t

def expand_tmpl(tmpl,params):
    if isinstance(tmpl, str):
        return [tmpl.format(x) for x in range(*params)]
    elif isinstance(tmpl, list):
        return [[y.format(x) for y in tmpl ] for x in range(*params)]

def _draw_serial(l):
    for x in itertools.cycle(l):
        yield x

def _draw_permutation(l):
    _l=l
    random.shuffle(_l)
    for x in itertools.cycle(_l):
        print x
        yield x

def _draw_random(l):
    while True:
        yield random.choice(l)

def _param_generator(how, tmpl,argspec,lot_type="random"):
    _lot_drawer={
      "tmpl":{
        "random": _draw_random,
        "serial": _draw_serial,
        "permutation": _draw_permutation,
      }
    }
    return _lot_drawer[how][lot_type](expand_tmpl(tmpl,argspec))

def _zipgen(tupls):
    while True:
        yield [(k,v.next()) for k,v in tupls]

def scenario(cfg):
    #pp=pprint.PrettyPrinter()
    #pp.pprint(cfg)

    profs={}
    lots={}
    for (k,v) in cfg["profiles"].items():
        lots[k]=_blackbox(v)
        profs[k]={}
        for (k2,v2) in v.items():
            profs[k][k2]=_zipgen([(k3, _param_generator(*cfg["params"][v3])) for k3,v3 in v2.items() if k3!="weight"])
    
    for t in _timer_scenario(cfg["scenario"]["times"],cfg["scenario"]["sequence"]):
        paramid=lots[t[0]].next()
        # yield time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime(t[1][1])),t[0],paramid,profs[t[0]][paramid].next()
        yield paramid,profs[t[0]][paramid].next()

# time ./prot.py | awk '{n+=1} $1!=now && now!=0 {print now,n ; n=0; now=$1} now==0{now=$1}'

if __name__ == '__main__':

    sc=scenario(yaml.load(open("cfg.yml").read()))
    for t in sc:
        print dict(t)

