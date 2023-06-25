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

def runtimestats_func(p,state,min_samples=1,strict=False,silent=True):
    #if len(state["execution_times"])>1:
    #    return [statistics.mean(state["execution_times"]),statistics.median(state["execution_times"])]
    #else:
    #    return ["",""]
    if strict and state["errrec"]['dist_value']>0:
        return None
    if (len(state['execution_times'])>=min_samples) and all(type(e)==int or type(e)==float for e in state['execution_times']):
        return [statistics.mean(state['execution_times']),statistics.median(state['execution_times'])]
    else:
        return None

def gsheetstats_func(p,state,total_errors,has_fatal_error):
    part1 = [total_errors,(1 if has_fatal_error else 0)]
    part2 = runtimestats_func(p,state,min_samples=20)
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

def verify_distance_computation(t,X1,Y1,X2,Y2,DISTx8_COMPUTED):
    DISTSQ_ACTUAL = (X1-X2)**2+(Y1-Y2)**2
    DISTx8_ACTUAL = int(8*math.sqrt(DISTSQ_ACTUAL))
    #print(f"t={t}: DIST_ACTUAL(({X1},{Y1}),({X2},{Y2}))={DISTx8_ACTUAL/8}, DIST_COMPUTED={DISTx8_COMPUTED/8}")
    if DISTx8_ACTUAL==DISTx8_COMPUTED:
        return True
    else:
        print(f"Incorrect output @ t={t}: distance(({X1},{Y1}),({X2},{Y2})) should be {DISTx8_ACTUAL/8} but got {DISTx8_COMPUTED/8}")
        return False

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
            #DIST = twos(signextend(sigrec['DIST']['val'],4),4)
            DISTx8 = int(sigrec['DIST']['val'],2)
            assert verify_distance_computation(t,X1,Y1,X2,Y2,DISTx8)
            state["correct_dist"] += 1
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
    elif state["jobs_completed"]==0:
        print(f"Raw functionality score = 0 as no DIST was produced / no DONE=1 was received.")
        test["score"] = 0
        return 0
    elif state['errrec']['protocol']>0 and state['correct_dist']==0:
        print(f"Raw functionality score = 0 as there were protocol errors and no valid data output was produced.")
        test["score"] = 0
        return 0
    else:
        max_functionality_score = p['max_functionality_score']
        max_quality_score = p['max_quality_score']
        fraction_good_clocks = 1-state['errrec']['badclockticks']/state['t_max']
        has_bad_clocks = True if state['errrec']['badclockticks']>0 else False
        print(f"DUT worked incorrectly on {round(100*(1-fraction_good_clocks),2)}% of the clock edges ({state['errrec']['badclockticks']} out of {state['t_max']}).")

        fraction_jobs_done = min(1,(state['jobs_completed']+state['resets_done'])/state['jobs_arrived'])
        print(f"DUT finished {round(100*fraction_jobs_done,2)}% of the jobs that arrive.")
        fraction_good_dist = state['correct_dist']/state['total_dist'] if state['total_dist']>0 else 0
        print(f"DUT computed correctly outputs on {round(100*fraction_good_dist,2)}% of the jobs it completed.")

        has_functionality_error = has_bad_clocks or (fraction_jobs_done<1) or (fraction_good_dist<1)

        if (1-fraction_good_clocks)>p['valid_design_max_percent_failed_tests']/100.0 and test['extra_data']['# of components']<p['valid_design_min_component_count']:
            print(f"\nThis design seems to be bogus or frivolous: it has {test['extra_data']['# of components']} components and has errors on {100*(1-fraction_good_clocks)}% of the clock ticks tested.")
            print(f"Zero functionality and quality scores.")
            test["score"]=0
            return test["score"]
        if has_functionality_error:
            max_badclockticks_allowed = state['t_max']*round(float(p['percent_failed_tests_for_zero_score'])/100)
            max_badoutputs_allowed = state['total_dist']*round(float(p['percent_failed_tests_for_zero_score'])/100)
            print(f"Errors carry minimum penalty of {float(p['minimum_penalty_percent'])}% and result in zero score upon failures at {float(p['percent_failed_tests_for_zero_score'])}% of tests.")
            print(f"Maximum # of clock ticks with problems allowed = {max_badclockticks_allowed}")
            print(f"Maximum # of computation jobs with problems allowed = {max_badoutputs_allowed}")
            if state['errrec']['badclockticks']>max_badclockticks_allowed or (state['total_dist']-state['correct_dist'])>max_badoutputs_allowed:
                if state['errrec']['badclockticks']>max_badclockticks_allowed:
                    print("Too many clock ticks with problems.")
                if (state['total_dist']-state['correct_dist'])>max_badoutputs_allowed:
                    print("Too many jobs with bad output values.")
                actual_functionality_score = 0
            else:
                actual_functionality_score = max_functionality_score*(1-0.01*p['minimum_penalty_percent'])
                delta1 = actual_functionality_score/(max_badclockticks_allowed-1)
                actual_functionality_score1 = max(0,actual_functionality_score-delta1*(state['errrec']['badclockticks']-1))
                delta2 = actual_functionality_score/(max_badoutputs_allowed-1)
                actual_functionality_score2 = max(0,actual_functionality_score-delta2*((state['total_dist']-state['correct_dist'])-1))
                actual_functionality_score = min(actual_functionality_score1,actual_functionality_score2)
        else:
            actual_functionality_score = max_functionality_score
        print(f"Functionality score = {actual_functionality_score}.")
        #actual_functionality_score = max_functionality_score*min(fraction_good_clocks,(0.25*fraction_jobs_done+0.75*fraction_good_dist))
        sfa = p["tester"]["scoring_func_args"] if ("tester" in p and "scoring_func_args" in p["tester"]) else None
        prorate_quality_score = p.get("prorate_quality_score",False)
        if prorate_quality_score:
            print("Quality score is being prorated for functionality.")
        else:
            print("Quality score is not being prorated for functionality: zero score for quality in case of any functionality error.")
        if has_functionality_error:
            if prorate_quality_score:
                #quality_score_scalefactor = fraction_good_clocks
                quality_score_scalefactor = min(fraction_good_clocks,fraction_good_dist)
                print(f"Design has at least one functionality error. Base quality score will be multiplied by x{quality_score_scalefactor}.")
            else:
                quality_score_scalefactor = 0
                print(f"Design has functionality errors. Setting quality score to 0.")
        else:
            quality_score_scalefactor = 1
            print(f"Design has no functionality errors detected. Base quality scare will not be derated.")
        if not sfa or not isinstance(sfa,dict) or not set(["best_quality", "thresholds"]).issubset(sfa.keys()):
            print("Warning: did not find proper 'scoring_func_args' to grade quality-optimized task. Please report to developers. Setting score to 0.")
            test["score"]=actual_functionality_score
        elif not is_numeric(sfa["best_quality"]): 
            print(f"Warning: invalid scoring_func_args['best_quality']: {sfa}. Please report to developers. Setting quality score to 0.")
            test["score"]=actual_functionality_score
        elif not (isinstance(sfa["thresholds"],list) and all(isinstance(e,list) and (len(e)==2) and is_numeric(e[0]) and is_numeric(e[1]) for e in sfa["thresholds"])):
            print(f"Warning: invalid scoring_func_args['thresholds']: {sfa}. Please report to developers. Setting quality score to 0.")
            test["score"]=actual_functionality_score
        else:
            best_quality = sfa["best_quality"]
            delay_stats = runtimestats_func(p,state,min_samples=20)
            if delay_stats:
                median_delay = delay_stats[1]
                output_msg = f"Median delay = {median_delay}"
                print(output_msg)
                quality = test['extra_data']['component cost'] * median_delay
                quality_ratio = quality/best_quality
                output_msg = f"Raw Quality (Area x Delay) = {quality} [best = {best_quality}, ratio = {quality_ratio}]"
                print(output_msg)
                test["output"].append(output_msg)
                thresholds = sfa["thresholds"]
                thresholds.sort(key=lambda e: e[0])
                if thresholds[0][0] != 0:
                    thresholds = [[0,1]]+thresholds
                if quality_ratio>thresholds[-1][0]:
                    quality_score_factor = 0
                else:
                    i=0
                    while quality_ratio>thresholds[i+1][0]:
                        i += 1
                    x1 = thresholds[i][0]
                    x2 = thresholds[i+1][0]
                    y1 = thresholds[i][1]
                    y2 = thresholds[i+1][1]
                    quality_score_factor = y1+((y2-y1)/(x2-x1))*(quality_ratio-x1)
                print(f"Base Quality Score is {max_quality_score} x {quality_score_factor}")
                print(f"Base Quality Score is further scaled by x{quality_score_scalefactor} based on functionality.")
                quality_score = quality_score_scalefactor * quality_score_factor * max_quality_score
                print(f"Final Quality Score = {quality_score}.")
                test["score"]=actual_functionality_score+quality_score
            else:
                print(f"No credit for Quality (Area x Delay) due to insufficiently functional design with sufficient # of samples to compute meaningful delay.")
                test["score"]=actual_functionality_score
        test["score"] = min(max(0,test["score"]),test["max_score"])
        print(f"Net score before penalties is {test['score']}")
        return test["score"]
