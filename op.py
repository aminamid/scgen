#!/bin/env python
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)

import sys
import time
import multiprocessing
import functools
import itertools
from logging import getLogger, StreamHandler, Formatter

import ldap
import yaml

import scgen


def concat( ll ):
    return list(itertools.chain(*ll))

def nowstr(fmt="%Y-%m-%dT%H:%M:%S"):
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

##  logging
def change_state(obj, method_arglist_tpls):
    for m_as in method_arglist_tpls:
        getattr(obj, m_as[0])(*m_as[1])
    return obj

def loginit(logname, format="%(message)s", stream=sys.stderr, level=15, datefmt="%Y/%m/%dT%H:%M:%S" ):
    return change_state(getLogger(logname), [
        ("setLevel", [level]),
        ("addHandler", [change_state(
            StreamHandler(stream),[("setFormatter", [Formatter(fmt=format,datefmt=datefmt)])]
        )])
      ])

def traclog( f ):
    @functools.wraps(f)
    def _f(*args, **kwargs):
        logger.debug("ENTER:{0} {1}".format( f.__name__, kwargs if kwargs else args))
        result = f(*args, **kwargs)
        logger.debug("RETRN:{0} {1}".format( f.__name__, result))
        return result
    return _f

loggercfg = {
  #"format": "%(asctime)s.%(msecs).03d %(process)d %(thread)x %(levelname).4s;%(module)s(%(lineno)d/%(funcName)s) %(message)s",
  "format": "%(asctime)s.%(msecs).03d %(process)d %(module)s(%(lineno)d/%(funcName)s) %(message)s",
  #"format": "%(message)s",
  "datefmt": "%Y-%m-%dT%H:%M:%S",
  "level": 15,
  "stream": sys.stderr,

}
logstdcfg = {
  "stream": sys.stdout,
  "level": 15,
}


logger = loginit(__name__,**loggercfg)
logstd = loginit("std",**logstdcfg)

def dictfilter(d,filter=[]):
    return dict([(k,v) for (k,v) in d.items() if k in filter ])

def ldapstat(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        start_time=time.time()
        try:
            rtn=func(*args, **kwargs)
        except ldap.LDAPError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type=func.__name__, name="None", response_time=total_time, exception=e)
            raise e
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type=func.__name__, name="None", response_time=total_time, response_length=0)
        return rtn
    return func_wrapper

def _ldapconnection(params={"ldaphost":None,"ldapport":None,"ldapuser":None,"ldappass":None}):
    _l=ldap.initialize("ldap://{0}:{1}".format(**params))
    while True:
        _ldapbind(_l,params)
        time.sleep(1)
        if _l:
            yield _l

def _ldapbind(l,params={"ldapuser":None,"ldappass":None}):
    return l.bind_s(who=ldapuser,cred=ldappass,method=ldap.AUTH_SIMPLE)

def _ldapmod_replace(l,params={"dn":None,"attr":None,"val":None}):
    return l.modify_s(params["dn"],[(ldap.MOD_REPLACE,params["attr"],params["val"],)])

def _ldapmod_add(l,params={"dn":None,"attr":None,"val":None}):
    return l.modify_s(params["dn"],[(ldap.MOD_ADD,params["attr"],params["val"],)])

def _ldapmod_delete(l,params={"dn":None,"attr":None}):
    return l.modify_s(params["dn"],[(ldap.MOD_DELETE,params["attr"])])

def _ldapsearch(l,params={"filterstr":None,"attrlist":None}):
    return self.l.search_s(base=params["baseDN"], scope=ldap.SCOPE_SUBTREE,filterstr=params["filterstr"],attrlist=params["attrlist"])

def workerloop(in_que,out_que,done,cfg):
    _lgen=_ldapconnection(cfg)
    l=_lgen.next()
    while True:
        (profname,prof)=in_que.get()
        in_que.task_done() 

        if paramid.startswith("add") or paramid.startswith("del"):
            prefix=[v for (k,v) in prof if k=="dn"][0][0]
            if not prefix in ldiftmpl:
                ldiftmpl[prefix]=open("base.{0}".format(prefix)).read()
 
         

def main(opts):
    prof=yaml.load(open(opts["profile"]).read())

    p_que,in_que=scgen.scque(prof)
    cfg=prof["config"]   
    
 
    done = multiprocessing.Value('b', False)
    procs=[]
    for i in range(opts["numproc"]):
        out_que = multiprocessing.JoinableQueue()
        procs.append((multiprocessing.Process(target=workerloop, args=(in_que,out_que,done,cfg)), out_que))
        procs[-1][0].daemon=True

    for p in procs: p[0].start()
    while True:
        deadps = [i for (i,p) in enumerate(procs) if not p[0].is_alive()]
        for i in deadps:
            procs[i][0].join()
        procs=[p for (i,p) in enumerate(procs) if not i in deadps]
        if not procs: break
        time.sleep(1) 
    logger.info("done")

    

def parsed_opts():
    import optparse
    import os

    opt = optparse.OptionParser()
    opt.add_option("-P", "--prof", default=False, action="store_true", help="get profile [default: %default]" )
    opt.add_option("-L", "--loglevel", default=15, type="int", help="15:info, 10:debug, 5:trace [default: %default]" )
    opt.add_option("-n", "--numproc",  default=1, type="int", help="[default: %default]" )
    opt.add_option("-f", "--profile",  default="cfg.yml", help="[default: %default]" )
    (opts, args)= opt.parse_args()
    return dict(vars(opts).items() + [("args", args)])

if __name__ == '__main__':
    opts = parsed_opts()
    logger.setLevel(opts['loglevel'])
    if opts['prof']:
      import cProfile
      cProfile.run('main(opts)')
      sys.exit(0)
    main(opts)

