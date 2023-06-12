# EEM16

import re
import hashlib
import os.path
import os
import math
from  statistics import mean, median
from logisim import readLogisimDesign, getGateStats

libList = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O', 'HDL-IP', 'TCL', 'Base', 'BFH', 'CS3410']

allowed_logisim = ["2.14.8.2", "2.14.8.4", "2.14.6"]

def signextend(val_str,numbytes=None):
	if numbytes==None:
		numbytes = math.ceil(len(val_str)/8)
	if numbytes*8 <= len(val_str):
		return val_str
	sign = val_str[0]
	return sign*(8*numbytes-len(val_str))+val_str

def twos(val_str, bytes):
	import sys
	val = int(val_str, 2)
	b = val.to_bytes(bytes, byteorder=sys.byteorder, signed=False)                                                          
	return int.from_bytes(b, byteorder=sys.byteorder, signed=True)

# err, errsummary, score = design_config['graderfunc'](design_config,traces_i,traces_o)
def print_iotrace(design_config,traces,header=None,t_range=None,suffix=None):
	t_max = len(traces[0])
	num_sigs = len(traces)

	if header:
		print("")
		print("{0}:".format(design_config['name'][0]))
		print("")
		print(header)
	if not t_range:
		t_range = range(t_max)
	for t in t_range:
		for i in range(num_sigs):
			if i<num_sigs-1:
				endchar = "\t"
			else:
				endchar = ""
			display_format = design_config['pins'][i].get('display','raw')
			num_bits = design_config['pins'][i]['length']
			if 'x' in traces[i][t]:
				if not ('0' in traces[i][t] or '1' in traces[i][t]) or len(traces[i][t])<5:
					print("x*{0}".format(len(traces[i][t])),end=endchar)
				else:
					print(traces[i][t],end=endchar)
			elif display_format == 'udec':
				print(int(traces[i][t],base=2),end=endchar)
			elif display_format == 'sdec':
				print(twos(signextend(traces[i][t],4)),end=endchar)
			elif display_format == 'uhex':
				print( "{0:#0{1}x}".format(int(traces[i][t],base=2),2+math.ceil(num_bits/4)))
			else:
				print(traces[i][t],end="\t")		
		if suffix!=None:
			print("\t"+suffix)
		else:
			print("")
	return

def print_sigrec(sigrec):
	print("")
	for k in sigrec:
		print("Signal: {0} = {1} @ {2}\t{3} @ {4}\t{5} @ {6}".format(
				k, sigrec[k]['val'], sigrec[k]['t'], 
				sigrec[k]['val@1'], sigrec[k]['t@1'],
				sigrec[k]['val@2'], sigrec[k]['t@2']
			))
def isBinaryValue(string):
	if not isinstance(string, str):
		return False
	for character in string:
		if character != '0' and character != '1':
			return False
	return True

def isBinaryTrace(trace):
	for value in trace:
		if not isBinaryValue(value):
			return False
	return True

def default_sequential_grader(design_config, traces):
	header = ""
	for i,e in enumerate(design_config['pins']):
		header = header+("\t" if i>0 else "") + e['name']

	#print_iotrace(design_config,traces,header)

	err = []
	errsummary = ""
	t_max = len(traces[0])

	if t_max==1:
		err.append("ERROR: circuit fails to simulate due to apparent oscillation. Testing abandoned.")
		print(err[-1])
		errsummary = "Testing of {0}.{1} abandoned as Logisim failed to simulate the circuit".format(
			design_config['dut'][0],design_config['dut'][1])
		score = 0
		extra_credit = None
		return (err, errsummary, score, extra_credit)

	# validate that circuit output is all binary
	pins_to_check_indices = [i for i,e in enumerate(design_config['pins']) if e.get('binary_check',False)]
	#if not all([isBinaryTrace(traces[i]) for i in pins_to_check_indices]):
	#	err.append("ERROR: some outputs are non binary, i.e. neither 0 nor 1. Testing abandoned.")
	#	print(err[-1])
	#	errsummary = "Testing of {0}.{1} abandoned as circuit produced non binary output".format(design_config['dut'][0],design_config['dut'][1])
	#	score = 0
	#	extra_credit = None
	#	return (err, errsummary, score extra_credit)

	sigrec = {}
	jobs_arrived = 0
	t_arrivals = []
	jobs_completed = 0
	t_completions = []
	errrec = {'reset':0, 'protocol':0, 'dout_value':0, 'dout_stability':0, 'nonbinary':0, 'fatal':0}
	speedrec = dict()

	for p in design_config['pins']:
		sigrec[p['name']] = {'val':None, 'val@1':None, 'val@2':None, 't@1':None, 't@2':None}

	for t in range(t_max):
		if t==0:
			print_iotrace(design_config,traces,header,range(0,1))
			t_last_print = 0
		elif any([e[t]!=e[t-1] for e in traces[1:]]):
			if t<t_max-1 and all([e[t]==e[t+1] for e in traces[1:]]):
				print_iotrace(design_config,traces,t_range=range(t,t+1),suffix="+")
			else:
				print_iotrace(design_config,traces,t_range=range(t,t+1))
			t_last_print = t
		for i,e in enumerate(design_config['pins']):
			p = e['name']
			sigrec[p]['val'] = traces[i][t]
			sigrec[p]['t'] = t
			if sigrec[p]['val']!=sigrec[p]['val@1']:
				# we have an event
				sigrec[p]['val@2'] = sigrec[p]['val@1']
				sigrec[p]['t@2'] = sigrec[p]['t@1']
				sigrec[p]['val@1'] = sigrec[p]['val']
				sigrec[p]['t@1'] = t
		if t>0 and edge('REQ',t,sigrec) and sigrec['RST']['val@2']=='1':
			t_arrivals.append(t)
			jobs_arrived = jobs_arrived+1
		if t>0 and edge('ACK',t,sigrec) and sigrec['RST']['val@2']=='1':
			t_completions.append(t)
			jobs_completed = jobs_completed+1

		for e in design_config['assertions']:
			msgs = []
			if e['func'](design_config,t,sigrec,errrec,speedrec,msgs):
				continue
			else:
				err.append("Assertion violation @ t = {0}: {1}. {2}".format(t,e['description']," ".join(msgs)))
				#print("\n")
				print(err[-1])
				#print_sigrec(sigrec)
				if errrec['fatal']==1:
					print("Unable to continue: Abandoning further testing.")
					errrecord = "{{reset={0}, protocol={1}, dout_value={2}, dout_stability={3}, nonbinary={4}, fatal={5}}}".format(
						errrec['reset'], errrec['protocol'], errrec['dout_value'], errrec['dout_stability'],errrec['nonbinary'], errrec['fatal'])
					errsummary = "Testing of {0}.{1} abandoned @ {2} due to error: {3}".format(
						design_config['dut'][0],design_config['dut'][1],t,err[-1])
					print("Error Record:\n\t{0}".format(errrecord))
					score = 0
					extra_credit = None
					return (err, errsummary, score, extra_credit)
	print("")
	print("Testing of {0}.{1} completed with {2} jobs arrived and {3} jobs finished (including incorrect ones).".format(
		design_config['dut'][0], design_config['dut'][1], jobs_arrived, jobs_completed))
	errrecord = "{{reset={0}, protocol={1}, dout_value={2}, dout_stability={3}, nonbinary={4}, fatal={5}}}".format(
		errrec['reset'], errrec['protocol'], errrec['dout_value'], errrec['dout_stability'],errrec['nonbinary'], errrec['fatal'])
	errsummary = "Errors = {0}".format(errrecord)
	print("Error Record:\n\t{0}".format(errrecord))
	print("Speed Record: ")
	for k in speedrec:
		print("\t{0}: {{count={1}, min={2}, max={3}, mean={4}, median={5}}}".format(
			k, len(speedrec[k]), min(speedrec[k]), max(speedrec[k]), mean(speedrec[k]), median(speedrec[k])))
	if jobs_completed<design_config['minjobs']:
		err.append("Design {0}.{1} completed only {2} jobs which is too few to give a score.".format(
			design_config['dut'][0], design_config['dut'][1],jobs_completed))
		print(err[-1])
		errummary = err[-1]
		score = 0
		extra_credit = None

		print("Score = {0}/{1}".format(score,design_config['maxscore']))
		return err,errsummary,score,extra_credit

	score, msg = default_scorer(jobs_arrived, jobs_completed, errrec, speedrec, design_config['maxscore'])
	msg = "Score = {0}/{1} [{2}]".format(score,design_config['maxscore'],msg)
	print(msg)
	errsummary = errsummary + " " + msg
	if 'extracreditfunc' in design_config and 'maxextracredit' in design_config and int(design_config['maxextracredit'])>0:
		if (jobs_completed-errrec['dout_value']) < design_config.get('minecjobs',jobs_completed*0.8):
			extra_credit = 0
			ecmsg = "Too few jobs done correctly - no extra credit for {0}.{1}.".format(design_config['dut'][0],design_config['dut'][1])
		else:
			extra_credit_multiplier = score/design_config['maxscore']
			extra_credit, ecmsg= design_config['extracreditfunc'](jobs_arrived, jobs_completed, errrec, speedrec, 
				design_config['maxextracredit'],extra_credit_multiplier)
			ecmsg = "Extra Credit = {0} / {1} [{2}]".format(extra_credit,int(design_config['maxextracredit']),ecmsg)
	else:
		extra_credit = None
		ecmsg = "No Extra Credit Available."
	print(ecmsg)
	errsummary = errsummary + " " + ecmsg
	#print("t_arrivals = {0} [{1}]".format(t_arrivals, len(t_arrivals)))
	#print("t_completions = {0} [{1}]".format(t_completions, len(t_completions)))
	return err,errsummary,score,extra_credit

def rising_edge(signame,t,sigrec):
	return sigrec[signame]['t@1']==t and sigrec[signame]['val']=='1' and isBinaryValue(sigrec[signame]['val@2'])

def falling_edge(signame,t,sigrec):
	return sigrec[signame]['t@1']==t and sigrec[signame]['val']=='0' and isBinaryValue(sigrec[signame]['val@2'])

def event(signame,t,sigrec):
	return sigrec[signame]['t@1']==t and isBinaryValue(sigrec[signame]['val@2'])

def edge(signame,t,sigrec):
	return event(signame,t,sigrec)


def check_no_nonbinary(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	pins_to_check_names = [e['name'] for e in design_config['pins'] if e.get('binary_check',False)]
	if all([isBinaryValue(sigrec[k]['val']) for k in pins_to_check_names]):
		return True
	else:
		if t>0 and sigrec['RST']['val@2']=='1':
			errrec['fatal'] = errrec['fatal']+1
		errrec['nonbinary'] = errrec['nonbinary']+1
		return False

def check_reset_ok_ack(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['RST']['t@1']==None:
		return True
	if not(falling_edge('RST',t,sigrec) and sigrec['ACK']['val']!='0'):
		return True
	else:
		errrec['reset'] = errrec['reset']+1
		return False

def check_reset_ok_dout(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['RST']['t@1']==None:
		return True
	if not(falling_edge('RST',t,sigrec) and sigrec['DOUT']['val']!='0'*8):
		return True
	else:
		errrec['reset'] = errrec['reset']+1
		return False

def check_no_successive_ack_events(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['ACK']['t@1']==None or sigrec['ACK']['t@2']==None or sigrec['REQ']['t@1']==None:
		return True
	if sigrec['RST']['val@2']!='1':
		return True 
	if not edge('ACK',t,sigrec):
		return True
	if sigrec['ACK']['t@2']>sigrec['REQ']['t@1']:
		errrec['fatal'] = errrec['fatal']+1
		errrec['protocol'] = errrec['protocol']+1
		return False
	else:
		t_finish = sigrec['ACK']['t@1']
		t_start = sigrec['REQ']['t@1'] if sigrec['REQ']['t@1']<sigrec['ACK']['t@1'] else sigrec['REQ']['t@2']
		if not "REQ2ACK" in speedrec:
			speedrec["REQ2ACK"] = []
		speedrec["REQ2ACK"].append(t_finish-t_start)
		return True		

def check_rising_go_is_after_req(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	# check that go rises as a result of REQ evemt
	if t==0 or sigrec['ACK']['t@1']==None or sigrec['GO']['t@1']==None or sigrec['REQ']['t@1']==None:
		return True
	if not(rising_edge('GO',t,sigrec) and sigrec['REQ']['t@1']<sigrec['ACK']['t@1']):
		return True
	else:
		errrec['protocol'] = errrec['protocol']+1
		return False

def check_ack_event_is_after_done(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['ACK']['t@1']==None or sigrec['DONE']['t@1']==None or sigrec['REQ']['t@1']==None:
		return True
	if not(edge('ACK',t,sigrec) and sigrec['DONE']['val']=='0' and sigrec['DONE']['t@1']<sigrec['REQ']['t@1']):
		return True
	else:
		errrec['protocol'] = errrec['protocol']+1
		return False

def check_dout_correct_at_ack(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['ACK']['t@1']==None or sigrec['DOUT']['t@1']==None or sigrec['REQ']['t@1']==None or sigrec['REQ']['t@2']==None:
		return True
	if sigrec['RST']['val@2']!='1':
		return True 
	if not edge('ACK',t,sigrec):
		return True
	DIN = int(sigrec['DIN']['val@1'],base=2)
	DOUT = int(sigrec['DOUT']['val@1'],base=2)
	if DOUT==min(255,round(math.sqrt(DIN))):
		t_finish = sigrec['ACK']['t@1']
		t_start = sigrec['REQ']['t@1'] if sigrec['REQ']['t@1']<sigrec['ACK']['t@1'] else sigrec['REQ']['t@2']
		if not "REQ2ACK+CorrectDOUT" in speedrec:
			speedrec["REQ2ACK+CorrectDOUT"] = []
		speedrec["REQ2ACK+CorrectDOUT"].append(t_finish-t_start)
		return True
	else:
		if msgs==[]:
			msgs.append("DIN={0} DOUT={1} Expected DOUT={2}".format(DIN,DOUT,min(255,round(math.sqrt(DIN)))))
		errrec['dout_value'] = errrec['dout_value']+1
		return False

def check_dout_stable_after_ack_until_req(design_config,t,sigrec,errrec,speedrec=None,msgs=None):
	if t==0 or sigrec['DOUT']['t@1']==None or sigrec['REQ']['t@1']==None or sigrec['ACK']['t@1']==None:
		return True
	if event('DOUT',t,sigrec) and (not event('ACK',t,sigrec)) and (sigrec['ACK']['t@1']>sigrec['REQ']['t@1']):
		errrec['dout_stability'] = errrec['dout_stability']+1
		return False
	else:
		return True
		

def default_scorer(jobs_arrived, jobs_completed, errrec, speedrec, max_score, nonbinary_penalty=0.25, score_frac_reset=0.1, score_frac_protocol=0.2):
	score = 0
	score_reset = 0
	score_protocol = 0
	score_computation = 0
	penalty_nonbinary = 0
	score_frac_data = (1-score_frac_reset-score_frac_protocol)
	if errrec['reset']==0:
		score_reset = score_frac_reset*max_score
		score = score + score_reset
	if errrec['protocol']==0 and errrec['dout_stability']==0:
		score_protocol = score_frac_protocol*max_score
	elif errrec['protocol']==0:
		score_protocol = min(score_frac_protocol*max_score/2,max(0,score_frac_protocol*max_score*(1-errrec['dout_stability']/jobs_completed)))
	score = score + score_protocol
	score_computation = score_frac_data*max_score*(jobs_completed-errrec['dout_value'])/jobs_arrived
	score = score + score_computation
	if errrec['nonbinary']>0:
		penalty_nonbinary = nonbinary_penalty*max_score
		score = score - nonbinary_penalty*max_score
	score = min(max_score,score)
	score = max(0,score)
	msg = "Credits: reset={0} protocol+dout_stability={1} doutvalue={2}; Penalties: nonbinary={3}".format(
		score_reset, score_protocol, score_computation, penalty_nonbinary)
	return score, msg

def final_part2_ec(jobs_arrived, jobs_completed, errrec, speedrec, max_score_ec, ec_multiplier,penalty_unstable_dout_min=0.1, penalty_unstable_dout_max=0.35):
	if any([errrec[k]!=0 for k in errrec if k not in ['dout_value', 'dout_stability', 'nonbinary', 'reset']]):
		msg = "No extra credit due to error record: {0}".format(errrec)
		return 0, msg
	mean_latency = mean(speedrec['REQ2ACK+CorrectDOUT'])
	if mean_latency>=50:
		msg = "Design too slow (mean latency = {0}) for extra credit.".format(mean_latency)
		extra_credit = 0
	else:
		fraction_correct_jobs = len(speedrec['REQ2ACK+CorrectDOUT'])/len(speedrec['REQ2ACK'])
		msg = []
		ec_penalty_factor = ec_multiplier
		if (fraction_correct_jobs<1):
			ec_penalty_factor = ec_penalty_factor*fraction_correct_jobs
		if errrec['dout_stability']>0:
			penalty_unstable_dout = max(penalty_unstable_dout_min,min(penalty_unstable_dout_max,errrec['dout_stability']/jobs_completed))
			ec_penalty_factor = ec_penalty_factor*(1-penalty_unstable_dout)
		msg.append("Extra credit error penalty = x{0}.".format(ec_penalty_factor))
		if mean_latency<14:
			ec_speed_factor = 1
		elif mean_latency<20:
			ec_speed_factor = 0.8
		elif mean_latency<30:
			ec_speed_factor = 0.6
		elif mean_latency<40:
			ec_speed_factor = 0.4
		else:
			ec_speed_factor = 0.2
		if ec_speed_factor==1:
			msg.append("Extra credit speed penalty = None")
		else:
			msg.append("Extra credit speed penalty = {0}.".format(ec_speed_factor))
		msg.append("Mean Latency = {0}".format(mean_latency))
		extra_credit = max_score_ec*ec_speed_factor*ec_penalty_factor
	return extra_credit, " ".join(msg)

design_config_list = [
	{
		'enabled': True,
		'name': ('final_part1_tb','TB'),
		'dut': ('final','FSM_2PHS'),
		'sequential': True,
		'maxscore': 18,
		'maxextracredit': 0,
		'minjobs': 30,
		'allowed_libs':  [],
		'disallowed_libs':  [],
		'allowed_gates': [],
		'disallowed_gates': [],
		'limited_gates': [],
		'pins': [
			{'name':'CYCLE', 'length':16, 'display':'udec'},
			{'name':'RST', 'length':1},
			{'name':'REQ', 'length':1},
			{'name':'ACK', 'length':1, 'binary_check':True},
			{'name':'GO', 'length':1, 'binary_check':True},
			{'name':'DONE', 'length':1},
			{'name':'CNTREQ', 'length':5, 'display':'udec'},
			{'name':'CNTACK', 'length':5, 'display':'udec'},
			{'name':'ASSERTIONS', 'length':1}
		],
		'assertions': [
			{'func':check_no_nonbinary, 'description':'Non binary signal'},
			{'func':check_reset_ok_ack, 'description':'Improper reset of ACK'},
			{'func':check_no_successive_ack_events, 'description':'Successive ACK events without intervening REQ event'},
			{'func':check_rising_go_is_after_req, 'description':'Incorrect rising edge on GO'},
			{'func':check_ack_event_is_after_done, 'description':'Event on ACK before DONE==1'},
		],
		'scorerfunc': default_scorer,
		'graderfunc': default_sequential_grader,
		'altscore': ('final','MAIN')
	},
	{
		'enabled': True,
		'name': ('final_part2_tb','TB'),
		'dut': ('final','MAIN'),
		'sequential': True,
		'maxscore': 42,
		'maxextracredit': 15,
		'minjobs': 100,
		'minecjobs':80,
		'allowed_libs':  [],
		'disallowed_libs':  [],
		'allowed_gates': [],
		'disallowed_gates': [],
		'limited_gates': [],
		'pins': [
			{'name':'CYCLE', 'length':16, 'display':'udec'},
			{'name':'RST', 'length':1},
			{'name':'REQ', 'length':1},
			{'name':'DIN', 'length':16, 'display':'udec'},
			{'name':'ACK', 'length':1, 'binary_check':True},
			{'name':'DOUT', 'length':8, 'display':'udec', 'binary_check':True},
			{'name':'CNTREQ', 'length':7, 'display':'udec'},
			{'name':'CNTACK', 'length':7, 'display':'udec'},
			{'name':'ASSERTIONS', 'length':1}
		],
		'assertions': [
			{'func':check_no_nonbinary, 'description':'Non binary signal'},
			{'func':check_reset_ok_ack, 'description':'Improper reset of ACK'},
			{'func':check_reset_ok_dout, 'description':'Improper reset of DOUT'},
			{'func':check_no_successive_ack_events, 'description':'Successive ACK events must not occur with an intervening REQ event'},
			{'func':check_dout_correct_at_ack, 'description':'DOUT value is incorrect at ACK event'},
			{'func':check_dout_stable_after_ack_until_req, 'description':'DOUT must remain stable from ACK event until next REQ event'}
		],
		'scorerfunc': default_scorer,
		'graderfunc': default_sequential_grader,
		'extracreditfunc': final_part2_ec
	}
]
		

def hasValidGates(design_config,err_hasValidGates,libList=libList):
	circ_filename = design_config['dut'][0]+'.circ'
	main_circuit = design_config['dut'][1]
	disallowed_libs = design_config.get('disallowed_libs',[])
	allowed_libs = design_config.get('allowed_libs',[])
	allowed_gates = design_config.get('allowed_gates',[])
	disallowed_gates = design_config.get('disallowed_gates',[])
	limited_gates = design_config.get('limited_gates',dict())
	gate_stats = getGateStats(circ_filename,main_circuit,"java","logisim-evolution-2.14.8.4-cornell.jar")
	for e in gate_stats:
		c = gate_stats[1]
		g = gate_stats[2]
		l = gate_stats[3]
		if len(allowed_libs)>0 and (l not in allowed_libs):
			err_hasValidGates.append("Circuit {0} in {1} uses library {3} not on allowed list".format(
				main_circuit, circ_filename,l))
			return False
		if len(disallowed_libs)>0 and (l in disallowed_libs):
			err_hasValidGates.append("Circuit {0} in {1} uses library {3} on disallowed list".format(
				main_circuit, circ_filename,l))
			return False
		if len(allowed_gates)>0 and (g not in allowed_gates):
			err_hasValidGates.append("Circuit {0} in {1} uses gate {3} not on allowed list".format(
				main_circuit, circ_filename,g))
			return False
		if len(disallowed_gates)>0 and (g in disallowed_gates):
			err_hasValidGates.append("Circuit {0} in {1} uses gate {3} on disallowed list".format(
				main_circuit, circ_filename,g))
			return False
		if g in limited_gates and c > limited_gates[g]:
			err_hasValidGates.append("Circuit {0} in {1} uses count {3} of gate {4} which exceeds allowed {5}".format(
				main_circuit, circ_filename,c,g,limited_gates[g]))
			return False
		return True


def testDesign(design_config,output_toplevel,output_tasklevel,scores,extra_credits,libList=libList):
	circ_filename = design_config['name'][0]+'.circ'
	dut_circ_filename = design_config['dut'][0]+'.circ'
	design, logisim = readLogisimDesign(circ_filename)
	design_dut, logisim_dut = readLogisimDesign(dut_circ_filename)
	err_hasValidGates = []
	# check that version of Logisim is correct
	if not logisim_dut in allowed_logisim:
		scores.append(0)
		output_tasklevel.append("{0} uses Logisim version {1} which is not allowed.".format(design_config['dut'][0], logisim_dut))
		output_toplevel.append("Invalid Logisim used in {0}.".format(design_config['dut'][0]))
		return
	# check that subcircuits exist
	elif not design_config['name'][1] in design.keys():
		scores.append(0)
		output_tasklevel.append("Didn't find design {0} in {1}.circ.".format(design_config['name'][1],design_config['name'][0]))
		output_toplevel.append("Design {0} not found in {1}.circ.".format(design_config['name'][1],design_config['name'][0]))
		return
	elif not design_config['dut'][1] in design_dut.keys():
		scores.append(0)
		output_tasklevel.append("Didn't find design {0} in {1}.circ.".format(design_config['dut'][1],design_config['dut'][0]))
		output_toplevel.append("Design {0} not found in {1}.circ.".format(design_config['dut'][1],design_config['dut'][0]))
		return
	# nor check DUT to make sure it is not using disallowed gates
	elif not hasValidGates(design_config,err_hasValidGates,libList=libList):
		scores.append(0)
		output_tasklevel.append(" ".join(err_hasValidGates))
		output_toplevel.append("Design {0} using disallowed gate or library.".format(design_config['dut'][1]))
		return
	elif not design_config.get('sequential',False):
		# combinational
		f = open(design_config['name'][0]+".out")
		err = []
		for l in f:
			if l[-2]=='1':
				continue
			parsed_line = ["".join(e.split()) for e in l[:-1].split('\t')]
			num_i = len(design_config['inputs'])
			num_o = len(design_config['outputs'])
			inputs = parsed_line[0:num_i]
			output_ref = parsed_line[num_i:num_i+num_o]
			output_dut = parsed_line[num_i+num_o:num_i+2*num_o]
			err.append("input: {0}, reference: {1}, dut: {2}; ".format(
					["{0}:{1}".format(design_config['inputs'][i]['name'],inputs[i]) for i in range(len(inputs))],
					["{0}:{1}".format(design_config['outputs'][i]['name'],output_ref[i]) for i in range(len(output_ref))],
					["{0}:{1}".format(design_config['outputs'][i]['name'],output_dut[i]) for i in range(len(output_dut))]
				))
		f.close()
		scores.append(1.0*max(0,design_config['maxscore']*(1.0-(design_config['percent_deduction_per_error']/100.0)*len(err))))
		if len(err)!=0:
			output_tasklevel.append("".join(err[0:4]))
			if len(err)>4:
				output_tasklevel.append("and, {0} more failures.".format(len(err)-4))
			output_toplevel.append("Task {0} failed {1} tests.".format(design_config['name'][0],len(err)))
		else:
			output_tasklevel.append("Task {0} passes all tests.".format(design_config['name'][0]))
			output_toplevel.append("Task {0} passes all tests.".format(design_config['name'][0]))
	else:
		# sequential
		task_name = design_config['dut'][0]+"."+design_config['dut'][1] if design_config['dut'][1]!=None else design_config['dut'][0]
		f = open(design_config['name'][0]+".out")
		num_sigs = len(design_config['pins'])
		traces = [[] for _ in range(num_sigs)]
		err = []
		errsummary = ""
		score = 0
		for l in f:
			parsed_line = ["".join(e.split()) for e in l[:-1].split('\t')]
			for i in range(num_sigs):
				traces[i].append(parsed_line[i])
		f.close()
		if 'graderfunc' in design_config:
			err, errsummary, score, extra_credit = design_config['graderfunc'](design_config,traces)
		scores.append(score)
		extra_credits.append(extra_credit)
		if len(err)!=0:
			output_tasklevel.append("".join(err[0:4]))
			output_toplevel.append("Task {0} failed. [{1}].".format(task_name,errsummary))
		else:
			output_tasklevel.append("Task passes all tests.".format(task_name))
			output_toplevel.append("Task {0} passes all tests. [{1}].".format(task_name,errsummary))

def writeResults(design_config_list,output_toplevel,output_tasklevel_list,scores,extra_credits=None):
	extra_credit_available = extra_credits!=None and any([('maxextracredit' in e) and (int(e['maxextracredit'])>0) and ('extracreditfunc' in e) for e in design_config_list])
	results = open(os.environ.get('AGHOME')+'/results/results.json', 'w') 
	results.write('{')
	results.write(' "output": "{0}",'.format(" ".join(output_toplevel)))
	results.write(' "tests":')
	results.write('  [')

	for i,design_config in enumerate(design_config_list):
		results.write('   {')
		results.write('    "score": "{0}",'.format(scores[i]))
		#results.write('    "score": "0",'.format(scores[i]))
		results.write('    "max_score": "{0}",'.format(design_config['maxscore']))
		results.write('    "name": "[Autograder] {0}.{1}",'.format(design_config['dut'][0],design_config['dut'][1]))
		results.write('    "output": "{0}",'.format(output_tasklevel_list[i]))
		circ_filename = design_config['name'][0]+'.circ'
		if os.path.exists(circ_filename):
			results.write('    "extra_data": {{"md5":"{0}"}}'.format(hashlib.md5(open(circ_filename,'rb').read()).hexdigest()))
		if i<len(design_config_list)-1 or extra_credit_available:
			results.write('   },')
		else:
			results.write('   }')
	if extra_credit_available:
		results.write('   {')
		results.write('    "score": "{0}",'.format(sum([e for e in extra_credits if e!=None and e>0])))
		#results.write('    "score": "0",'.format(scores[i]))
		results.write('    "max_score": "{0}",'.format(sum([int(e['maxextracredit']) for e in design_config_list if (
			('maxextracredit' in e) and (int(e['maxextracredit'])>0) and ('extracreditfunc' in e))])))
		results.write('    "name": "[Autograder] Extra Credits",')
		results.write('    "output": "Extra Credits = {0}"'.format(extra_credits))
		results.write('   }')
	results.write('  ]')
	results.write('}')
	results.close()

def scoreAdjuster(design_config_list,scores,output_toplevel,output_tasklevel_list):
	print("\nAdjusting scores...")
	scores_adjusted = []
	for i,dc1 in enumerate(design_config_list):
		if 'altscore' in dc1:
			dc2 = None
			j = None
			for k,e in enumerate(design_config_list):
				if e['dut'] == dc1['altscore']:
					dc2 = e
					j = k
			if j in scores_adjusted:
				print("Skipping adjustment of the score of {0}.{1} with prorated score of {2}.{3} as latter has already been adjusted".format(
					dc1['dut'][0],dc1['dut'][1],dc2['dut'][0],dc2['dut'][1]))
			elif dc2!=None and scores[i]/dc1['maxscore'] < scores[j]/dc2['maxscore']:
				new_score = dc1['maxscore'] * scores[j]/dc2['maxscore']
				msg = "Score {0} for {1}.{2} replaced with new score {3} using prorated score of {4}.{5}".format(
					scores[i],dc1['dut'][0],dc1['dut'][1],new_score,dc2['dut'][0],dc2['dut'][1]
					)
				scores[i] = new_score
				print("Score Adjustment: "+msg)
				output_toplevel.append(msg)
				output_tasklevel_list[i] = output_tasklevel_list[i] + " " + msg
				scores_adjusted.append(i)


def main():
	output_toplevel = []
	output_tasklevel_list = []
	scores = []
	extra_credits = []
	for design_config in design_config_list:
		if not design_config['enabled']:
			print("\nSkipping {0}".format(design_config['name'][0]))
			output_tasklevel_list.append("Design {0} skipped.".format(design_config['name'][0]))
			scores.append(0)
			extra_credits.append(None)
			continue
		print("\nProcessing {0}".format(design_config['name'][0]))
		circ_filename = design_config['name'][0]+'.circ'
		if not 'dut' in design_config:
			design_config['dut'] == design_config['name']
		if not os.path.exists(circ_filename):
			output_tasklevel_list.append("File {0} not found.".format(circ_filename))
			scores.append(0)
			extra_credits.append(None)
			continue
		if design_config['dut']!=design_config['name']:
			dut_circ_filename = design_config['dut'][0]+'.circ'
			if not os.path.exists(dut_circ_filename):
				output_tasklevel_list.append("File {0} not found.".format(dut_circ_filename))
				extra_credits.append(None)
				scores.append(0)
				continue
		output_tasklevel = []
		testDesign(design_config,output_toplevel,output_tasklevel,scores,extra_credits,libList=libList)
		output_tasklevel_list.append(" ".join(output_tasklevel))
	scoreAdjuster(design_config_list,scores,output_toplevel,output_tasklevel_list)
	writeResults(design_config_list,output_toplevel,output_tasklevel_list,scores,extra_credits)
		

main()