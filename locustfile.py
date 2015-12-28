import time
import random
import itertools
import functools
import ldap
import ldap.modlist
from gevent.coros import BoundedSemaphore
from locust import HttpLocust, TaskSet, task, events, Locust
from locust.exception import StopLocust

import yaml
import scgen

sc=scgen.scenario(yaml.load(open("cfg.yml").read()))
sc_sem = BoundedSemaphore(1)

baseDN="dc=com"

MBOX_STATS="ASLDP"

root_member=[["cn=root", "secret"]]

def str_range(num,numbase=0,tmpl="{0}"):
    return [tmpl.format(x) for x in range(numbase, numbase+num)]

def stat(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        start_time=time.time()
        try:
            func(*args, **kwargs)
        except ldap.LDAPError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type=func.__name__, name="None", response_time=total_time, exception=e)
            #print "### ldap.LDAPError",func.__name__,e
            return False
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type=func.__name__, name="None", response_time=total_time, response_length=0)
            #print "### SUCCESS",func.__name__
        return True
    return func_wrapper

ldiftmpl={}
class ApiUser(Locust):
    
    min_wait = 0
    max_wait = 0

    class task_set(TaskSet):

        def on_start(self):
            self.connect()

      
        def connect(self):
            #self.auth=random.choice(members)
            self.auth=random.choice(root_member)
            #print self.auth,self.locust.host
            self.l=ldap.initialize("ldap://{0}:{1}".format(self.locust.host,25005))
            self.l.bind_s(who=self.auth[0],cred=self.auth[1],method=ldap.AUTH_SIMPLE)

        @stat
        def mod_em_prov(self,prof): 
            self.l.modify_s(prof["dn"][0],[(ldap.MOD_REPLACE,"mailboxstatus",random.choice(MBOX_STATS),)])

        @stat
        def mod_ss_(self,prof): 
            self.l.modify_s(prof["dn"][0],[(ldap.MOD_REPLACE,"mailboxstatus",random.choice(MBOX_STATS),)])

        @stat
        def mod_sy_(self,prof): 
            self.l.modify_s(prof["dn"][0],[(ldap.MOD_REPLACE,"mailboxstatus",random.choice(MBOX_STATS),)])

        @stat
        def mod_em_pusha(self,prof): 
            self.l.modify_s(prof["dn"][0],[(ldap.MOD_ADD,"pushnotifyinfo",'{id:0>32X}{id:0>32X} 6801805E-89A8-431E-836E-{id:0>12X} com.apple.mobilemail "INBOX" {time}'.format(id=int(prof["dn"][1]),time=int(time.time())))])

        @stat
        def mod_em_pushd(self,prof): 
            rslt=self.l.search_s(base=baseDN, scope=ldap.SCOPE_SUBTREE,filterstr='pushnotifyinfo={id:0>32X}{id:0>32X}*'.format(id=int(prof["dn"][1])),attrlist=["dn"])
            if rslt: self.l.modify_s(prof["dn"][0],[(ldap.MOD_DELETE,"pushnotifyinfo","")])

        @stat
        def add_em_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
            self.l.add_s(_d["dn"][0],ldap.modlist.addModlist(dict([(k,v[0] if len(v) <= 1 else v ) for (k,v) in _d.items() if k !="dn"])))

        @stat
        def del_em_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
                if "dn" in _d: break
            if self.l.search_s(base=baseDN, scope=ldap.SCOPE_SUBTREE,filterstr=_d["dn"][0],attrlist=["dn"]):
                self.l.delete_s(_d["dn"][0])

        @stat
        def add_ss_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
            self.l.add_s(_d["dn"][0],ldap.modlist.addModlist(dict([(k,v[0] if len(v) <= 1 else v ) for (k,v) in _d.items() if k !="dn"])))

        @stat
        def del_ss_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
                if "dn" in _d: break
            if self.l.search_s(base=baseDN, scope=ldap.SCOPE_SUBTREE,filterstr=_d["dn"][0],attrlist=["dn"]):
                self.l.delete_s(_d["dn"][0])

        @stat
        def add_sy_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
            self.l.add_s(_d["dn"][0],ldap.modlist.addModlist(dict([(k,v[0] if len(v) <= 1 else v ) for (k,v) in _d.items() if k !="dn"])))

        @stat
        def del_sy_(self,prof):
            _d={}
            for l in ldiftmpl[prof["dn"][0]].format(id=int(prof["dn"][1]),prefix=prof["dn"][0]).split("\n"):
                if not ":" in l: continue
                k,v=l.split(":",1)
                if not k.strip() in _d: _d[k.strip()]=[]
                _d[k.strip()].append(v.strip())
                if "dn" in _d: break
            if self.l.search_s(base=baseDN, scope=ldap.SCOPE_SUBTREE,filterstr=_d["dn"][0],attrlist=["dn"]):
                self.l.delete_s(_d["dn"][0])

        @task(1)
        def ldaptask(self):
            try:
                sc_sem.acquire()
                paramid,prof=sc.next()
                sc_sem.release()
            except StopIteration as e:
                raise StopLocust()
            if paramid.startswith("add") or paramid.startswith("del"):
                prefix=[v for (k,v) in prof if k=="dn"][0][0] 
                if not prefix in ldiftmpl:
                    ldiftmpl[prefix]=open("base.{0}".format(prefix)).read()
            #print "## before:self.l",self.l
            try:
                noerr=getattr(self, paramid)(dict(prof))
            except ldap.LDAPError as e:
                print e
                #print "### reconnecting"
                self.l.unbind_s()
                self.l=self.connect()
            #print "## after:self.l",self.l
