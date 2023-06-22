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
    f4 = (state["correct_dist"]>1)
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
            state['X1'] = sigrec['X1']['val']
            state['Y1'] = sigrec['Y1']['val']
        if rising_edge('GO2',t,sigrec): 
            state["t_arrivals_2"].append(t)
            state['opcount'] += 1
            state['X2'] = sigrec['X2']['val']
            state['Y2'] = sigrec['Y2']['val']
        if state['opcount']==2 and (rising_edge('GO1',t,sigrec) or rising_edge('GO2',t,sigrec)):
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
            state['X1'] = None
            state['Y1'] = None
            state['X2'] = None
            state['Y2'] = None
            state['opcount'] = 0
    #print(f"state: {state}")
    return

def check_protocol_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "protocol"
    if rising_edge('DONE',t,sigrec) and state['opcount']!=2:
        # checking that DONE is asserted only after two operands are there
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        errrec['protocol.opcount'] = errrec.get('protocol.opcount',0)+1
        return False
    elif falling_edge('DONE',t,sigrec) and sigrec['DONE']['t@2'] and t!=sigrec['DONE']['t@2']+1:
        # checking that DONE is a high pulse of width 1
        errrec['total'] = errrec.get('total',0)+1
        errrec[errtype] = errrec.get(errtype,0)+1
        errrec['protocol.donewidth'] = errrec.get('protocol.donewidth',0)+1
        return False
    return True

def verify_distance_computation(X1,Y1,X2,Y2,DIST):
    DISTSQ_ACTUAL = (X1-X2)**2+(Y1-Y2)**2
    DISTx8_ACTUAL = int(8*math.sqrt(DISTSQ_ACTUAL))
    DISTx8_OBSERVED = DIST**2
    print(f"DISTx8_ACTUAL(({X1},{Y1}),({X2},{Y2}))={DISTx8_ACTUAL}, DISTx8_OBSERVED={DIST}^2={DISTx8_OBSERVED}")
    return DISTx8_ACTUAL==DISTx8_OBSERVED

def check_output_value_func(tester,t,sigrec,state,msgs=None,params=None,errtype=None):
    errrec = state["errrec"]
    errtype = errtype if errtype!=None else "dist_value"
    if rising_edge('DONE',t,sigrec):
        state["total_dist"] += 1
        try:
            X1 = twos(signextend(state['X1'],4),4)
            Y1 = twos(signextend(state['Y1'],4),4)
            X2 = twos(signextend(state['X2'],4),4)
            Y2 = twos(signextend(state['Y2'],4),4)
            DIST = twos(signextend(sigrec['DIST']['val'],4),4)
            assert verify_distance_computation(X1,Y1,X2,Y2,DIST)
            state["correct_dist"] += 1
        except:
            print(f"Incorrect output @ t={t} distance(({X1},{Y1}),({X2},{Y2}))={DIST/8}")
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
    elif state["jobs_completed"]==0:
        print(f"Raw functionality score = 0 as no DOUT was produced / no DONE=1 was received.")
        test["score"] = 0
        return 0
    elif state['errrec']['protocol']>0 and state['correct_dout']==0:
        print(f"Raw functionality score = 0 as there were protocol errors and no valid data output was produced.")
        test["score"] = 0
        return 0
    else:
        max_functionality_score = p['max_functionality_score']
        max_area_score = p['max_area_score']
        fraction_good_clocks = 1-state['errrec']['badclockticks']/state['t_max']
        has_bad_clocks = True if state['errrec']['badclockticks']>0 else False
        print(f"DUT worked incorrectly on {round(100*(1-fraction_good_clocks),2)}% of the clock edges ({state['errrec']['badclockticks']} out of {state['t_max']}).")

        fraction_jobs_done = min(1,(state['jobs_completed']+state['resets_done'])/state['jobs_arrived'])
        print(f"DUT finished {round(100*fraction_jobs_done,2)}% of the jobs that arrive.")
        fraction_good_dout = state['correct_dout']/state['total_dout'] if state['total_dout']>0 else 0
        print(f"DUT computed correctly outputs on {round(100*fraction_good_dout,2)}% of the jobs it completed.")

        has_functionality_error = has_bad_clocks or (fraction_jobs_done<1) or (fraction_good_dout<1)

        if (1-fraction_good_clocks)>p['valid_design_max_percent_failed_tests']/100.0 and test['extra_data']['# of components']<p['valid_design_min_component_count']:
            print(f"\nThis design seems to be bogus or frivolous: it has {test['extra_data']['# of components']} components and has errors on {100*(1-fraction_good_clocks)}% of the clock ticks tested.")
            print(f"Zero functionality and area scores.")
            test["score"]=0
            return test["score"]
        if has_functionality_error:
            max_badclockticks_allowed = state['t_max']*round(float(p['percent_failed_tests_for_zero_score'])/100)
            max_badoutputs_allowed = state['total_dout']*round(float(p['percent_failed_tests_for_zero_score'])/100)
            print(f"Errors carry minimum penalty of {float(p['minimum_penalty_percent'])}% and result in zero score upon failures at {float(p['percent_failed_tests_for_zero_score'])}% of tests.")
            print(f"Maximum # of clock ticks with problems allowed = {max_badclockticks_allowed}")
            print(f"Maximum # of computation jobs with problems allowed = {max_badoutputs_allowed}")
            if state['errrec']['badclockticks']>max_badclockticks_allowed or (state['total_dout']-state['correct_dout'])>max_badoutputs_allowed:
                if state['errrec']['badclockticks']>max_badclockticks_allowed:
                    print("Too many clock ticks with problems.")
                if (state['total_dout']-state['correct_dout'])>max_badoutputs_allowed:
                    print("Too many jobs with bad output values.")
                actual_functionality_score = 0
            else:
                actual_functionality_score = max_functionality_score*(1-0.01*p['minimum_penalty_percent'])
                delta1 = actual_functionality_score/(max_badclockticks_allowed-1)
                actual_functionality_score1 = max(0,actual_functionality_score-delta1*(state['errrec']['badclockticks']-1))
                delta2 = actual_functionality_score/(max_badoutputs_allowed-1)
                actual_functionality_score2 = max(0,actual_functionality_score-delta2*((state['total_dout']-state['correct_dout'])-1))
                actual_functionality_score = min(actual_functionality_score1,actual_functionality_score2)
        else:
            actual_functionality_score = max_functionality_score
        print(f"Functionality score = {actual_functionality_score}.")
        #actual_functionality_score = max_functionality_score*min(fraction_good_clocks,(0.25*fraction_jobs_done+0.75*fraction_good_dout))
        sfa = p["tester"]["scoring_func_args"] if ("tester" in p and "scoring_func_args" in p["tester"]) else None
        prorate_area_score = p.get("prorate_area_score",False)
        if prorate_area_score:
            print("Area score is being prorated for functionality.")
        else:
            print("Area score is not being prorated for functionality: zero score for area in case of any functionality error.")
        if has_functionality_error:
            if prorate_area_score:
                #area_score_scalefactor = fraction_good_clocks
                area_score_scalefactor = min(fraction_good_clocks,fraction_good_dout)
                print(f"Design has at least one functionality error. Base area score will be multiplied by x{area_score_scalefactor}.")
            else:
                area_score_scalefactor = 0
                print(f"Design has functionality errors. Setting area score to 0.")
        else:
            area_score_scalefactor = 1
            print(f"Design has no functionality errors detected. Base area scare will not be derated.")
        if not sfa or not isinstance(sfa,dict) or not set(["best_area", "threshold_full", "threshold_zero"]).issubset(sfa.keys()):
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
            print(f"Component cost {test['extra_data']['component cost']} is {test['extra_data']['component cost']/sfa['best_area']} x  {sfa['best_area']} (best).")
            print(f"Adjusting base area score downward: {max_area_score} --> {adjusted_area_score}.")
            print(f"Scaling area score by x{area_score_scalefactor} based on functionality.")
            print(f"Further adjusting area score downwards: {adjusted_area_score} --> {adjusted_area_score*area_score_scalefactor}")
            test["score"]=actual_functionality_score+adjusted_area_score*area_score_scalefactor
        else:
            print(f"Component cost {test['extra_data']['component cost']} is <= {sfa['threshold_full']} x {sfa['best_area']} (best). Full score of {max_area_score} given for area.")
            print(f"Base area score set to maximum: {max_area_score}.")
            print(f"Scaling base area score by x{area_score_scalefactor} based on functionality.")
            print(f"Adjusting area score downwards: {max_area_score} --> {max_area_score*area_score_scalefactor}")
            test["score"]=actual_functionality_score+max_area_score*area_score_scalefactor
        test["score"] = min(max(0,test["score"]),test["max_score"])
        print(f"Net score before penalties is {test['score']}")
        return test["score"]
