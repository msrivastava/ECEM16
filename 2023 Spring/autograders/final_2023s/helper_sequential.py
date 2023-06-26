from BitVector import BitVector
import statistics
import math
import sys
from digikit import *
import helper_task

# These are task specific and so must be defined in task-specific helper file
def validate_endstate_func(p,state,msg=[]):
    return helper_task.validate_endstate_func(p,state,msg)

def validate_effort_func(p,state,has_fatal_error):
    return helper_task.validate_effort_func(p,state,has_fatal_error)

def runtimestats_func(p,state):
    return helper_task.runtimestats_func(p,state)

def gsheetstats_func(p,state,total_errors,has_fatal_error):
    return helper_task.gsheetstats_func(p,state,total_errors,has_fatal_error)

def stateupdate_func(state,t,sigrec):
    return helper_task.stateupdate_func(state,t,sigrec)

def check_output_value_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    return helper_task.check_output_value_func(tester,t,sigrec,state,msgs,params,errtype)

def check_protocol_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    return helper_task.check_protocol_func(tester,t,sigrec,state,msgs,params,errtype)

def scoring_func(p,state,test,assertion_checks,fatal_error,fatal_error_msg,silent=False):
    return helper_task.scoring_func(p,state,test,assertion_checks,fatal_error,fatal_error_msg,silent)

# Generic functions

def check_signals_at_reset(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    errrec = state["errrec"]
    resetsig = None
    sigstocheck = []
    edge_func = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = int(e.get('reset_level',1))
            edge_func = falling_edge if reset_level==1 else rising_edge
        if 'reset_check_value' in e:
            sigvalue_at_reset = e['reset_check_value']
            if isinstance(sigvalue_at_reset,int):
                bv = BitVector(intVal = 2**e['length']+sigvalue_at_reset)
                sigvalue_at_reset = str(bv[-e['length']:])
            sigvalue_at_reset = sigvalue_at_reset[0]*(e['length']-len(sigvalue_at_reset))+sigvalue_at_reset
            sigstocheck.append((e['name'],sigvalue_at_reset))
    if resetsig==None or t==0 or sigrec[resetsig]['t@1']==None:
        return True
    answer = True
    if edge_func(resetsig,t,sigrec):
        for e in sigstocheck:
            if sigrec[e[0]]['val']!=e[1]:
                if errtype:
                    errrec[errtype] = errrec.get(errtype,0)+1
                answer = False
                errrec['total'] = errrec.get('total',0)+1
    return answer

def check_no_nonbinary(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    if resetsig!=None and sigrec[resetsig]['val@2']!=reset_level:
        return True 
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "nonbinary"
    pins_to_check_names = [e['name'] for e in tester['pins'] if e.get('binary_check',0)==1]
    if all([isBinaryValue(sigrec[k]['val']) for k in pins_to_check_names]):
        return True
    else:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        return False

def check_consecutive_events_separated_by_event(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    # ignore event that take place due to reset
    # either we are in reset at present or just came out of reset
    if resetsig!=None and (sigrec[resetsig]['val@2']!=reset_level or t==sigrec[resetsig]['t@2']+1):
        return True 
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "protocol"
    speedrec = state["speedrec"]
    if not params or not "event" in params.keys() or not "separator" in params.keys():
        return True
    
    eventsig = params["event"]
    event_type = params.get("event_type","any")
    event_edge_func = rising_edge if event_type=="rising" else (falling_edge if event_type=="falling" else edge)

    separatorsig = params["separator"]
    separator_type = params.get("separator_type","any")
    separator_may_change = True if params.get("separator_may_change",0)==1 else False
    separator_values = ['1'] if separator_type=="rising" else (['0'] if separator_type=="falling" else ['0','1'])

    if t==0 or sigrec[eventsig]['t@1']==None or sigrec[eventsig]['t@2']==None or sigrec[separatorsig]['t@1']==None:
        return True
    if not event_edge_func(eventsig,t,sigrec):
        return True
    
    if sigrec[separatorsig]['t@1']<=sigrec[eventsig]['t@2']:
        # Case: S@1 < E@2 < E@1 FAIL
        assertion = False
    elif sigrec[separatorsig]['val@1'] in separator_values:
        # Case: E@2 < S@1 < E@1 and S@1 correct type PASS
        t1 = sigrec[eventsig]['t@2']
        t2 = sigrec[separatorsig]['t@1']
        t3 = sigrec[eventsig]['t@1']
        assertion = True
    elif separator_may_change and sigrec[separatorsig]['t@2'] and (sigrec[eventsig]['t@2']<=sigrec[separatorsig]['t@2']):
        # Case: separator allowed to change and E@2 < S@2 < S@1 < E@1 and S@1 not correct type
        t1 = sigrec[eventsig]['t@2']
        t2 = sigrec[separatorsig]['t@2']
        t3 = sigrec[eventsig]['t@1']
        assertion = True
    else:
        assertion = False

    if not assertion:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        #print(sigrec)
        return False
    else:
        measurement_name = f"{separatorsig}2{eventsig}"
        if not measurement_name in speedrec:
            speedrec[measurement_name] = []
        speedrec[measurement_name].append(t3-t2)

        measurement_name = f"{eventsig}2{separatorsig}"
        if not measurement_name in speedrec:
            speedrec[measurement_name] = []
        speedrec[measurement_name].append(t2-t1)

        return True

def check_event_is_after_event1event2(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    if resetsig!=None and sigrec[resetsig]['val@2']!=reset_level:
        return True 
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "protocol"
    speedrec = state["speedrec"]
    if not params or not "rising" in params.keys() or not "event1" in params.keys() or not "event2" in params.keys():
        return True
    eventsig = params["event"]
    event1sig = params["event1"]
    event2sig = params["event2"]
   
    event_type = params.get("event_type","any")
    event_edge_func = rising_edge if event_type=="rising" else (falling_edge if event_type=="falling" else edge)
    
    event1_type = params.get("event1_type","any")
    event1sig_values = ['1'] if event1_type=="rising" else (['0'] if event1_type=="falling" else ['0','1'])
   
    event2_type = params.get("event2_type","any")
    event2sig_values = ['1'] if event2_type=="rising" else (['0'] if event2_type=="falling" else ['0','1'])

    # check that rising event on risingsig is caused by an event on precursorsig 
    if t==0 or sigrec[eventsig]['t@1']==None or sigrec[event1sig]['t@1']==None or sigrec[event2sig]['t@1']==None:
        return True
    if not event_edge_func(eventsig,t,sigrec):
        return True
    elif (sigrec[event1sig]['t@1']<=sigrec[event2sig]['t@1'] and sigrec[event1sig]['t@1'] in event1sig_values and sigrec[event2sig]['t@1'] in event2sig_values):
        return True
    else:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        return False

def check_event_is_when_signal_at_value(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    if resetsig!=None and sigrec[resetsig]['val@2']!=reset_level:
        return True 
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "protocol"
    speedrec = state["speedrec"]
    if not params or not "event" in params.keys() or not "signal" in params.keys() or not "signal_value" in params.keys():
        return True
    eventsig = params["event"]
    event_type = params.get("event_type","any")
    event_edge_func = rising_edge if event_type=="rising" else (falling_edge if event_type=="falling" else edge)
    condsig = params["signal"]
    condsig_value= str(params["signal_value"])
    if t==0 or sigrec[eventsig]['t@1']==None or sigrec[condsig]['t@1']==None:
        return True
    if not event_edge_func(eventsig,t,sigrec):
        return True
    ignore_when_reset = True if params.get("ignore_when_reset",0)==1 else False
    if sigrec[condsig]['val']==condsig_value:
        return True
    elif ignore_when_reset and sigrec[condsig]['t@1']<sigrec[resetsig]['t@1']:
        return True
    else:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        return False

def check_signal_value_at_event(tester,t,sigrec,state,msgs=None,params=None,errtype="dist_value"):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    if resetsig!=None and sigrec[resetsig]['val@2']!=reset_level:
        return True 
    errrec = state["errrec"]
    speedrec = state["speedrec"]
    if not params or not "event" in params.keys() or not "signal" in params.keys() or not "signal_func" in params.keys():
        return True
    eventsig = params["event"]
    event_type = params.get("event_type","any")
    event_edge_func = rising_edge if event_type=="rising" else (falling_edge if event_type=="falling" else edge)
    signame = params["signal"]
    sigfunc = params["signal_func"]
    sigfuncargs = params.get("signal_func_args",[])
    if "measurement" in params.keys() and "event" in params["measurement"].keys():
        starteventsig = params["measurement"]["event"]
        startevent_type = params["measurement"].get("event_type","any")
        startevent_edge_func = rising_edge if startevent_type=="rising" else (falling_edge if startevent_type=="falling" else edge)
    if t==0 or sigrec[eventsig]['t@1']==None or sigrec[signame]['t@1']==None or sigrec[starteventsig]['t@1']==None or sigrec[starteventsig]['t@2']==None or sigrec[starteventsig]['t@3']==None:
        return True
    if not event_edge_func(eventsig,t,sigrec):
        return True
    args = []
    for s in sigfuncargs:
        args.append(sigrec[s]['val@1'])
    args.append(sigrec[signame]['val@1'])
    if eval(f"{sigfunc}(state,args,msgs)"):
        t_finish = sigrec[eventsig]['t@1']
        if startevent_type=="rising":
            if sigrec[starteventsig]['t@1']<sigrec[eventsig]['t@1']:
                if sigrec[starteventsig]['val@1']=='1':
                    t_start = sigrec[starteventsig]['t@1']
                else:
                    t_start = sigrec[starteventsig]['t@2']
            else:
                if sigrec[starteventsig]['val@2']=='1':
                    t_start = sigrec[starstarteventsigtsig]['t@2']
                else:
                    t_start = sigrec[starteventsig]['t@3']
        elif startevent_type=="falling":
            if sigrec[starteventsig]['t@1']<sigrec[eventsig]['t@1']:
                if sigrec[starteventsig]['val@1']=='0':
                    t_start = sigrec[starteventsig]['t@1']
                else:
                    t_start = sigrec[starteventsig]['t@2']
            else:
                if sigrec[starteventsig]['val@2']=='0':
                    t_start = sigrec[starteventsig]['t@2']
                else:
                    t_start = sigrec[starteventsig]['t@3']
        else:
            if sigrec[starteventsig]['t@1']<sigrec[eventsig]['t@1']:
                t_start = sigrec[starteventsig]['t@1']
            else:
                t_start = sigrec[starteventsig]['t@2']
        measurement_name = f"{starteventsig}2{eventsig}+Correct{signame}"
        if not measurement_name in speedrec:
            speedrec[measurement_name] = []
        speedrec[measurement_name].append(t_finish-t_start)
        return True
    else:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        return False

def check_signal_stable_after_event1_until_event2(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    resetsig = None
    for e in tester['pins']:
        if resetsig==None and e.get('reset_sig',0)==1:
            resetsig = e['name']
            reset_level = str(e.get('reset_level',1))
            break
    if resetsig!=None and sigrec[resetsig]['val@2']!=reset_level:
        return True 
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "f_stability"
    speedrec = state["speedrec"]
    if not params or not "signal" in params.keys() or not "event1" in params.keys() or not "event2" in params.keys():
        return True
    signame = params["signal"]
    event1sig = params["event1"]
    event2sig = params["event2"]
    event1_type = params.get("event1_type","any")
    event1_value = ['1'] if event1_type=="rising" else (['0'] if event1_type=="falling" else ['0','1'])
    event2_type = params.get("event2_type","any")
    event2_value = ['0'] if event2_type=="rising" else (['1'] if event2_type=="falling" else ['0','1'])
    if t==0 or sigrec[signame]['t@1']==None or sigrec[event1sig]['t@1']==None or sigrec[event2sig]['t@1']==None:
        return True
    if not event(signame,t,sigrec):
        return True
    else:
        # event on signame
        if event(event1sig,t,sigrec) and (sigrec[event1sig]['val@1'] in event1_value):
            # concurrent event of the right type just happened on event1sig, which is acceptable
            return True
        if (sigrec[event1sig]['t@1']>sigrec[event2sig]['t@1']):
            # most recent edge is on event1sig
            if (sigrec[event1sig]['val@1'] in event1_value) and (sigrec[event2sig]['val@1'] in event2_value):
                errrec['total'] = errrec.get('total',0)+1
                errrec[errtype] = errrec.get(errtype,0)+1
                return False
    return True