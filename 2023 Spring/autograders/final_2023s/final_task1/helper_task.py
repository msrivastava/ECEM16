from BitVector import BitVector
import statistics
import math
import sys
from digikit import *

# Task specific functions

def validate_endstate_func(p,state,msg=[]):
    return True

def validate_effort_func(p,state):
    f1 = (state['ticks']>2)
    f2 = (p["# components"]>50)
    f3 = (state['errrec']['nonbinary']<0.8*state['ticks'])
    f4 = (state["correct_dout"]>1)
    return f1 and f2 and f3 and f4

def runtimestats_func(p,state):
    if len(state["execution_times"])>1:
        return [statistics.mean(state["execution_times"]),statistics.median(state["execution_times"])]
    else:
        return ["",""]

def gsheetstats_func(p,state,total_errors,has_fatal_error):
    part1 = [total_errors,(1 if has_fatal_error else 0)]
    part2 = runtimestats_task3(p,state)
    if not part2 or has_fatal_error:
        part2 = ["",""]
    return part1+part2

def stateupdate_func(state,t,sigrec):
    state['ticks'] += 1
    if sigrec['RST']['t@1']==t and sigrec['RST']['val']=='0' and sigrec['RST']['val@2']=='1' and sigrec['RST']['val@3']=='0':
        state['resets_done'] +=1
        state['opcount'] = 0
    if sigrec['RST']['t@1']==t and sigrec['RST']['val']=='1' and sigrec['RST']['val@2']=='0' and sigrec['RST']['val@3']=='1':
        state['runs_done'] +=1
    if t>0 and sigrec['RST']['val@2']=='1':
        if rising_edge('GO1',t,sigrec): 
            state["t_arrivals_1"].append(t)
            state['opcount'] += 1
            state['DIN1'] = sigrec['DIN1']['val']
        if rising_edge('GO2',t,sigrec): 
            state["t_arrivals_2"].append(t)
            state['opcount'] += 1
            state['DIN2'] = sigrec['DIN2']['val']
        if rising_edge('GO3',t,sigrec): 
            state["t_arrivals_3"].append(t)
            state['opcount'] += 1
            state['DIN3'] = sigrec['DIN3']['val']
        if state['opcount']==3 and (rising_edge('GO1',t,sigrec) or rising_edge('GO2',t,sigrec) or rising_edge('GO3',t,sigrec)):
            state["t_arrivals"].append(t)
            state["jobs_arrived"] += 1
        if rising_edge('DONE',t,sigrec):
            state["t_completions"].append(t)
            state["jobs_completed"] += 1
            if len(state["t_arrivals"])>0:
                state["execution_times"].append(t-state["t_arrivals"][-1])
            else:
                state["execution_times"].append(None)
        if falling_edge('DONE',t,sigrec):
            state['DIN1'] = None
            state['DIN2'] = None
            state['DIN3'] = None
            state['opcount'] = 0
    #print(f"state: {state}")
    return

def check_protocol_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "protocol"
    if rising_edge('DONE',t,sigrec) and state['opcount']!=3:
        # checking that DONE is asserted only after three operands are there
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        errrec['protocol.opcount'] = errrec.get('protocol.opcount',0)+1
        return False
    elif falling_edge('DONE',t,sigrec) and sigrec['DONE']['t@2'] and t!=sigrec['DONE']['t@2']+1:
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        errrec['protocol.donewidth'] = errrec.get('protocol.donewidth',0)+1
        # checking that DONE is a high pulse of width 1
        return False
    return True

def check_output_value_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "dout_value"
    if rising_edge('DONE',t,sigrec):
        state["total_dout"] += 1
        try:
            DIN1 = twos(signextend(state['DIN1'],4),4)
            DIN2 = twos(signextend(state['DIN2'],4),4)
            DIN3 = twos(signextend(state['DIN3'],4),4)
            DOUT = twos(signextend(sigrec['DOUT']['val'],4),4)
            #print(f"median({DIN1},{DIN2},{DIN3})={DOUT}")
            assert statistics.median([DIN1,DIN2,DIN3])==DOUT
            state["correct_dout"] += 1
        except:
            errrec['total'] = errrec.get('total',0)+1
            errrec[errtype] = errrec.get(errtype,0)+1
            return False
    return True

# note: this needs to be corrected to put penalty for first bad clock
def scoring_func(p,state,test,assertion_checks,fatal_error,fatal_error_msg,silent=True):
    # helper
    def is_numeric(x):
        return type(x)==int or type(x)==float
    # main body
    if not silent:
        print("Computing Scores (in scoring_func):")
    if fatal_error:
        print(f"Raw functionality score = 0 as there is a fatal error that prevents testing.")
        test["output"].append(f"{fatal_error_msg}")
        test["score"] = 0
        return 0
    #elif 'max_score' not in p.keys():
    #    test["score"] = -1
    #    return -1
    elif state["jobs_completed"]==0:
        print(f"Raw functionality score = 0 as no DOUT was produced.")
        test["score"] = 0
        return 0
    elif state['errrec']['protocol']>0 and state['correct_dout']==0:
        print(f"Raw functionality score = 0 as both control and data flawed.")
        test["score"] = 0
        return 0
    else:
        max_area_score = p['max_area_score']
        max_functionality_score = p['max_functionality_score']
        #percent_score_for_area = min(max(0,p.get('percent_score_for_area',0)),100)
        #percent_score_for_functionality = 100 - percent_score_for_area
        #max_functionality_score = test["max_score"]*(percent_score_for_functionality/100)
        #max_area_score = test["max_score"]*(percent_score_for_area/100)
        fraction_good_clocks = 1-state['errrec']['badclockticks']/state['t_max_expected']
        print(f"Fraction of clocks with no error = {fraction_good_clocks}.")
        fraction_jobs_done = min(1,(state['jobs_completed']+state['resets_done'])/state['jobs_arrived'])
        print(f"Fraction of jobs done = {fraction_jobs_done}.")
        fraction_good_dout = state['correct_dout']/state['total_dout']
        print(f"Fraction of jobs completed that were correct = {fraction_good_dout}.")
        #if fraction_good_clocks<1:
        #    max_functionality_score = max_functionality_score*(1-0.01*p['minimum_penalty_percent'])
        actual_functionality_score = max_functionality_score*min(fraction_good_clocks,(0.25*fraction_jobs_done+0.75*fraction_good_dout))
        print(f"Functionality score = {actual_functionality_score}.")
        sfa = p["tester"]["scoring_func_args"] if ("tester" in p and "scoring_func_args" in p["tester"]) else None
        if state['errrec']['badclockticks']>0:
            print(f"No credit for area due to functionality bugs in the design.")
            test["score"]=actual_functionality_score
        elif not sfa or not isinstance(sfa,dict) or not set(["best_area", "threshold_full", "threshold_zero"]).issubset(sfa.keys()):
            print("Warning: did not find proper 'scoring_func_args' to grade area-optimized task. Please report to developers. Setting score to 0.")
            test["score"]=actual_functionality_score
        elif not all(is_numeric(sfa[k]) for k in ["best_area", "threshold_full", "threshold_zero"]) or (sfa["threshold_zero"] <= sfa["threshold_full"]):
            print(f"Warning: 'scoring_func_args' are invalid: {sfa}. Please report to developers. Setting area score to 0.")
            test["score"]=actual_functionality_score
        elif test['extra_data']['component cost']/sfa["best_area"] > sfa["threshold_zero"]:
            print(f"Component cost {test['extra_data']['component cost']} is way too high (> {sfa['threshold_zero']} x {sfa['best_area']}): Setting score to 0.")
            test["score"]=actual_functionality_score
        elif test['extra_data']['component cost']/sfa["best_area"] > sfa["threshold_full"]:
            adjusted_area_score = max_area_score*(sfa["threshold_zero"]-test['extra_data']['component cost']/sfa["best_area"])/(sfa["threshold_zero"]-sfa["threshold_full"])
            print(f"Component cost is {test['extra_data']['component cost']/sfa['best_area']} x  {sfa['best_area']}. Adjusting area score downward: {max_area_score} --> {adjusted_area_score}")
            test["score"]=adjusted_area_score+actual_functionality_score
        else:
            print(f"Component cost is <= {sfa['threshold_full']} x {sfa['best_area']}. Full score of {max_area_score} given for area.")
            test["score"]=max_area_score+actual_functionality_score
        test["score"] = min(max(0,test["score"]),test["max_score"])
        return test["score"]
