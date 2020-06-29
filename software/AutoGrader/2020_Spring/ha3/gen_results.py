# EEM16

import re
import hashlib
import os.path
import os

libList = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O', 'HDL-IP', 'TCL', 'Base', 'BFH', 'CS410']

allowed_logisim = ["2.14.8.2", "2.14.8.4", "2.14.6"]

# err, errsummary, score = design_config['graderfunc'](design_config,traces_i,traces_o)
def print_iotrace(design_config,traces_i,traces_o,header=None,t_range=None,suffix=None):
	return
	t_max = len(traces_o[0])
	num_i = len(traces_i)
	num_o = len(traces_o)
	if header!=None:
		print("")
		#print("{0}:".format(design_config['name'][0]))
		#print("")
		print(header)
	if t_range==None:
		t_range = range(t_max)
	for t in t_range:
		for i in range(num_i):
			if num_o==0 and i==num_i-1:
				endchar = ""
			else:
				endchar = "\t"
			if i==0:
				# first field is CYCLE - print in base 10
				print(int(traces_i[i][t],base=2),end=endchar)
			else:
				print(traces_i[i][t],end=endchar)
		for i in range(num_o):
			if i==num_o-1:
				endchar = ""
			else:
				endchar = "\t"
			print(traces_o[i][t],end=endchar)
		if suffix!=None:
			print("\t"+suffix)
		else:
			print("")
	return

def default_sequential_grader(design_config, traces_i, traces_o):
	#print_iotrace(design_config, traces_i, traces_o)
	return [], "", design_config['maxscore']

def twos(val_str, bytes):
    import sys
    val = int(val_str, 2)
    b = val.to_bytes(bytes, byteorder=sys.byteorder, signed=False)                                                          
    return int.from_bytes(b, byteorder=sys.byteorder, signed=True)

def isBinaryValue(string):
    for character in string:
        if character != '0' and character != '1':
            return False
    return True

def isBinaryTrace(trace):
	for value in trace:
		if not isBinaryValue(value):
			return False
	return True

def ha3_grader(design_config, traces_i, traces_o):
	CYCLE = traces_i[0]
	RST = traces_i[1]
	REQ = traces_i[2]
	A = traces_i[3]
	D = traces_i[4]
	Q = traces_o[0]
	R = traces_o[1]
	FDBZ = traces_o[2]
	ACK = traces_o[3]
	REQNUM = traces_o[4]
	ACKNUM = traces_o[5]

	err = []
	t_max = len(traces_o[0])
	t_last_nonbinary = -1
	t_reset = [t for t in range(t_max) if t>0 and RST[t-1]=='1' and RST[t]=='0'][0]

	if t_max==1:
		err.append("ERROR: circuit fails to simulate due to apparent oscillation. Testing abandoned.")
		print(err[-1])
		errsummary = "Testing abandoned as Logisim failed to simulate the circuit"
		score = 0
		return (err, errsummary, score)

	header1 = "CYCLE\tRST\tREQ\tA\t\t\tD\t\t\tQ\t\t\tR\t\t\tFDBZ\tACK\tREQNUM\tACKNUM"
	header = "CYCLE\tRST\tREQ\tA\tD\tQ\tR\tFDBZ\tACK\tREQNUM\tACKNUM"

	# validate that circuit output is all binary
	if not all([isBinaryTrace(e) for e in [Q, R, FDBZ, ACK]]):
		err.append("ERROR: some outputs are non binary.")
		print(err[-1])
		for t in range(t_max):
			if any([not isBinaryValue(e[t]) for e in [Q, R, FDBZ, ACK]]):
				print_iotrace(design_config,traces_i,traces_o,
					header=header1 if t==0 else None,t_range=range(t,t+1))
				t_last_nonbinary = t
		if t_last_nonbinary>t_reset:
			msg = "Testing abandoned as circuit produced non binary output post-reset"
			err.append(msg)
			print(err[-1])
			errsummary = msg
			score = 0
			return (err, errsummary, score)
		else:
			msg = "All non-binary outputs are pre-reset - so continuing to grade with penalty."
			err.append(msg)
			print(msg)
	
	#print_iotrace(design_config,traces_i,traces_o,header=header,t_range=range(1),suffix="init")

	for i in range(len(A)):
		A[i] = twos(A[i],2) if isBinaryValue(A[i]) else A[i]
		D[i] = twos(D[i],2) if isBinaryValue(D[i]) else D[i]
		Q[i] = twos(Q[i],2) if isBinaryValue(Q[i]) else Q[i]
		R[i] = twos(R[i],2) if isBinaryValue(R[i]) else R[i]
		REQNUM[i] = int(REQNUM[i],base=2) if isBinaryValue(REQNUM[i]) else REQNUM[i]
		ACKNUM[i] = int(ACKNUM[i],base=2) if isBinaryValue(ACKNUM[i]) else ACKNUM[i]
	#print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tREQ\tA\tD\tQ\tR\tFDBZ\tACK")

	score = 0
	score_function = design_config['maxscore']*(1-design_config['speedscorefrac'])
	score_speed = design_config['maxscore']*design_config['speedscorefrac']
	score_reset = score_function*0.1
	bad_ack_received = False
	score_protocol = score_function*0.2
	score_jobs = score_function - score_protocol - score_reset
	total_jobs = 255
	num_jobs = 0
	passed_jobs = 0
	job_times = []
	job_times_normal = []
	state='before_reset'
	substate="none"
	ignore_FDBZ = ('FDBZ' in design_config.get('err_ignore',[]))

	print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tREQ\tA\tD\tQ\tR\tFDBZ\tACK\tREQNUM\tACKNUM",
		range(1),"init")
	for t in range(1,t_max):
		# state changes
		if (state=='before_reset') and (RST[t-1]=='0' and RST[t]=='1'):
			state='being_reset'
		elif (state=='being_reset') and (RST[t-1]=='1' and RST[t]=='0'):
			state='done_reset'
			if ACK[t]!='0':
				print_iotrace(design_config, traces_i, traces_o, None, range(t,t+1),state+":"+substate)
				bad_ack_received = True
				err.append("Testing abandoned due to protocol violation as ACK!=0 after reset @ t={0}.".format(t))
				print(err[-1])
				break
			if Q[t]!=0 or R[t]!=0 or FDBZ[t]!='0':
				err.append("ERROR: all outputs must be 0 after reset @ t={0}.".format(t))
				print(err[-1])
			else:
				print("Reset done ok @ t={0}.".format(t))
				score = score + score_reset
			substate='req0ack0'
		if (state=='done_reset'):
			if substate=='req0ack0':
				if REQ[t]=='0' and ACK[t]=='1':
					print_iotrace(design_config, traces_i, traces_o, None, range(t,t+1),state+":"+substate)
					bad_ack_received = True
					err.append("Testing abandoned due to protocol violation as ACK!=0 @ t={0}.".format(t))
					print(err[-1])
					break
				if (REQ[t]=='1') and (REQ[t-1]=='0'):
					curA = A[t]
					curD = D[t]
					if curD==0:
						expectedFDBZ = '1'
						expectedR = 0
						if curA==0:
							expectedQ = 0
						elif curA>0:
							expectedQ = 32767
						else:
							expectedQ = -32768
					elif curD==-1 and curA==-32768:
						expectedR = 0
						expectedQ = -32768
						expectedFDBZ = '0'
					else:
						expectedFDBZ = '0'
						expectedQ = curA//curD
						expectedR = curA%curD
						if expectedR<0:
							if curD<0:
								expectedR = expectedR-curD
								expectedQ = expectedQ+1
							else:
								expectedR = expectedR+curD
								expectedQ = expectedQ-1
					num_jobs = num_jobs + 1
					print("Job #{0} Arrived: A={1}, D={2}, Q={3}, R={4}, FDBZ={5} @ t={6}".format(
						num_jobs,curA,curD,expectedQ,expectedR,expectedFDBZ,t))
					treq = t
					if ACK[t]=='0':
						substate='req1ack0'
					else:
						substate='req1ack1'
						print("Job Done: A={0}, D={1}, Q={2}, R={3}, FDBZ={4} @ t={5}".format(curA,curD,Q[t],R[t],FDBZ[t],t))
						if Q[t]!=expectedQ:
							err.append("ERROR: Q must be {0} @ t={1} but is {2}.".format(expectedQ,t,Q[t]))
							print(err[-1])
						if R[t]!=expectedR:
							err.append("ERROR: R must be {0} @ t={1} but is {2}.".format(expectedR,t,R[t]))
							print(err[-1])
						if FDBZ[t]!=expectedFDBZ:
							msg = "ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t])
							print(msg)
							if not ignore_FDBZ:
								err.append(msg)
						if treq>0 and Q[t]==expectedQ and R[t]==expectedR and (ignore_FDBZ or FDBZ[t]==expectedFDBZ):
							passed_jobs = passed_jobs + 1
							job_times.append(min(1,t-treq))
							if curA!=0 and curD!=0 and curD!=1 and curD!=-1:
								job_times_normal.append(t-treq)
							treq = 0
			elif substate=='req1ack0':
				if (ACK[t-1]=='0') and (ACK[t]=='1'):
					substate='req1ack1'
					print("Job Done: A={0}, D={1}, Q={2}, R={3}, FDBZ={4} @ t={5}".format(curA,curD,Q[t],R[t],FDBZ[t],t))
					if Q[t]!=expectedQ:
						err.append("ERROR: Q must be {0} @ t={1} but is {2}.".format(expectedQ,t,Q[t]))
						print(err[-1])
					if R[t]!=expectedR:
						err.append("ERROR: R must be {0} @ t={1} but is {2}.".format(expectedR,t,R[t]))
						print(err[-1])
					if FDBZ[t]!=expectedFDBZ:
						msg = "ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t])
						print(msg)
						if not ignore_FDBZ:
							err.append(msg)
					if treq>0 and Q[t]==expectedQ and R[t]==expectedR and (ignore_FDBZ or FDBZ[t]==expectedFDBZ):
						passed_jobs = passed_jobs + 1
						job_times.append(t-treq)
						if curA!=0 and curD!=0 and curD!=1 and curD!=-1:
							job_times_normal.append(min(1,t-treq))
						treq = 0
			elif substate=='req1ack1':
				if REQ[t]=='1':
					if ACK[t]=='0':
						print_iotrace(design_config, traces_i, traces_o, None, range(t,t+1),state+":"+substate)
						bad_ack_received = True
						err.append("Testing abandoned due to protocol violation as ACK!=1 @ t={0}.".format(t))
						print(err[-1])
						break
					if False:
						if Q[t]!=expectedQ:
							err.append("ERROR: Q must be {0} @ t={1} but is {2}.".format(expectedQ,t,Q[t]))
							print(err[-1])
						if R[t]!=expectedR:
							err.append("ERROR: R must be {0} @ t={1} but is {2}.".format(expectedR,t,R[t]))
							print(err[-1])
						if FDBZ[t]!=expectedFDBZ:
							msg = "ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t])
							print(msg)
							if not ignore_FDBZ:
								err.append(msg)
				if (REQ[t-1]=='1') and (REQ[t]=='0'):
					if ACK[t]=='1':
						substate='req0ack1'
					else:
						# ACK became 0 immediately
						substate='req0ack0'
			elif substate=='req0ack1':
				if (ACK[t-1]=='1') and (ACK[t]=='0'):
					substate='req0ack0'
		currvals = (RST[t],REQ[t],A[t],D[t],Q[t],R[t],FDBZ[t],ACK[t],REQNUM[t],ACKNUM[t])
		priorvals = (RST[t-1],REQ[t-1],A[t-1],D[t-1],Q[t-1],R[t-1],FDBZ[t-1],ACK[t-1],REQNUM[t-1],ACKNUM[t-1])
		if t>1 and currvals!=priorvals:
			print_iotrace(design_config, traces_i, traces_o, None, range(t,t+1),state+":"+substate)
	
	if (not bad_ack_received) and (num_jobs>30):
		score = score + score_protocol
	if (num_jobs>0):
		score  = score + (passed_jobs/num_jobs)*score_jobs
	score = score if score>=0 else 0
	fs = score
	print("Functionality Score = {0} out of {1}".format(score,score_function))
	if len(job_times_normal)>30:
		#print(job_times_normal)
		mean_latency = sum(job_times_normal)/len(job_times_normal)
		print("Mean Latency = ",mean_latency)
		if (mean_latency<=18):
			ss = score_speed
		else:
			ss = + max(0,score_speed * (1-0.1*(mean_latency-18)))
		score = score + ss
		print("Speed Score = {0} out of {1}".format(ss,score_speed))
	else:
		print("Insufficient # of successful jobs to estimate latency.")
		ss = 0
		print("Speed Score = 0 out of {0}".format(score_speed))
	errsummary = "{0} testing errors across {1} total jobs and {2} passed jobs over {3} cycles with functionality score = {4} and speed score = {5}".format(
		len(err),num_jobs,passed_jobs,t_max,fs,ss)
	if t_last_nonbinary>-1:
		msg = "Deducting {0} for pre-reset non-binary output".format(0.05*design_config['maxscore'])
		errsummary = errsummary + "; " + msg
		score = score - 0.05*design_config['maxscore']
	score = score if score<=design_config['maxscore'] else design_config['maxscore']
	print("ha3: "+errsummary+".")
	return (err, errsummary, score, num_jobs, passed_jobs)


design_config_list = [
	{
		'enabled': True,
		'name': ('design',None),
		'logisim': None,
		'sequential': True,
		'maxscore': 45,
		'speedscorefrac': 1/3,
		'percent_deduction_per_error': None,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['Divider'],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':16},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'REQ', 'base':2, 'length':1},
			{'name':'A', 'base':2, 'length':16},
			{'name':'D', 'base':2, 'length':16},
		],
		'outputs': [
			{'name':'Q', 'base':2, 'length':16},
			{'name':'R', 'base':2, 'length':16},
			{'name':'FDBZ', 'base':2, 'length':1},
			{'name':'ACK', 'base':2, 'length':1},
			{'name':'REQNUM', 'base':2, 'length':8},
			{'name':'ACKNUM', 'base':2, 'length':8}
		],
		#'err_ignore': ['FDBZ'],
		'graderfunc': ha3_grader
	},
	{
		'enabled': True,
		'name': ('synth',None),
		'logisim': None,
		'sequential': True,
		'maxscore': 30,
		'speedscorefrac': 0,
		'percent_deduction_per_error': None,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['Divider'],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':16},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'REQ', 'base':2, 'length':1},
			{'name':'A', 'base':2, 'length':16},
			{'name':'D', 'base':2, 'length':16},
		],
		'outputs': [
			{'name':'Q', 'base':2, 'length':16},
			{'name':'R', 'base':2, 'length':16},
			{'name':'FDBZ', 'base':2, 'length':1},
			{'name':'ACK', 'base':2, 'length':1},
			{'name':'REQNUM', 'base':2, 'length':16},
			{'name':'ACKNUM', 'base':2, 'length':16}
		],
		'graderfunc': ha3_grader
	}
]

def read_design(name):
	f = open(name+'.circ','r')
	logisim = None
	design = {'default':[]}
	circuit = 'default'
	for l in f:
		m = re.match('^\s*<project source=\"(?P<logisim>.+)\"\s+version.*>',l)
		if m:
			logisim = m.group('logisim')
			continue
		m = re.match('^\s*<circuit\s+name=\"(?P<circuit>.+)\"',l)
		if m:
			circuit = m.group('circuit')
			design[circuit] = []
			continue
		m = re.match('^\s*<comp\s+loc=.*?name=\"(?P<subcircuit>.+)\"',l)
		if m:
			design[circuit].append({'type':'subcircuit', 'name':m.group('subcircuit')})
			continue
		m = re.match('^\s*<comp\s+lib=\"(?P<lib>\d+)\".*?name=\"(?P<gate>.+)\"',l)
		if m:
			design[circuit].append({'type':'gate', 'lib':m.group('lib'), 'name':m.group('gate')})
			continue
	return design, logisim

def hasValidGates(design, circuit, allowed_libs, disallowed_gates, err_hasValidGates, libList=libList):
	for c in design[circuit]:
		if c['type']=='gate' and ((libList[int(c['lib'])] not in allowed_libs+['Base']) or (c['name'] in disallowed_gates)):
			err_hasValidGates.append("Circuit " + circuit + " uses invalid gate " + c['name'])
			return False
		if c['type']=='subcircuit' and not hasValidGates(design, c['name'], 
			allowed_libs, disallowed_gates, err_hasValidGates, libList):
			return False
	return True

def test_design(design_config,output_toplevel,output_tasklevel,scores,libList=libList):
	is_logisim_design = True if design_config.get('logisim',None)!=None else False
	if is_logisim_design:
		design_name = design_config['name'][0]+"."+design_config['name'][1]
	else:
		design_name = design_config['name'][0]
	if is_logisim_design:
		design, logisim = read_design(design_config['name'][0])
		err_hasValidGates = []
	if is_logisim_design and not logisim in allowed_logisim:
		scores.append(0)
		output_tasklevel.append("Task {0} uses Logisim version {1} which is not allowed.".format(design_config['name'][0], logisim))
		output_toplevel.append("Invalid Logisim used in Task {0}.".format(design_config['name'][0]))
		return
	elif is_logisim_design and not design_config['name'][1] in design.keys():
		scores.append(0)
		output_tasklevel.append("Didn't find design {0} in Task {1}.".format(design_config['name'][1],design_config['name'][0]))
		output_toplevel.append("Design not found for Task {0}.".format(design_config['name']))
		return
	elif is_logisim_design and not hasValidGates(design, design_config['name'][1], design_config['allowed_libs'], design_config['disallowed_gates'], err_hasValidGates, libList):
		scores.append(0)
		output_tasklevel.append(" ".join(err_hasValidGates))
		output_toplevel.append("Task {0} using disallowed gate.".format(design_config['name'][1]))
		return
	elif not design_config.get('sequential',False):
		# combinational
		filename = design_config['name'][0]+".out"
		if not os.path.exists(filename):
			errmsg = "Design {0} file {1} not found.".format(design_name,filename)
			output_tasklevel.append(errmsg)
			output_toplevel.append(errmsg)
			scores.append(0)
			return 
		f = open(filename)
		err = []
		num_tests = 0
		for l in f:
			num_tests = num_tests+1
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
		if 'error_weight' in design_config and isinstance(design_config['error_weight'],int) and design_config['error_weight']>0:
			percent_deduction_per_error_1 = 100*design_config['error_weight']/num_tests
		if 'percent_deduction_per_error' not in design_config or not isinstance(design_config['percent_deduction_per_error'],int) or design_config['percent_deduction_per_error']<0:
			design_config['percent_deduction_per_error'] = 100/num_tests
		percent_deduction_per_error_2 = design_config['percent_deduction_per_error']
		percent_deduction_per_error = max(percent_deduction_per_error_1,percent_deduction_per_error_2)
		print("{0} [#tests={1}]: Each incorrect test costs {2}%".format(design_name,num_tests,percent_deduction_per_error))
		scores.append(1.0*max(0,design_config['maxscore']*(1.0-(percent_deduction_per_error/100.0)*len(err))))
		if len(err)!=0:
			output_tasklevel.append("".join(err[0:4]))
			if len(err)>4:
				output_tasklevel.append("and, {0} more failures.".format(len(err)-4))
			output_toplevel.append("Design {0} failed {1} out of {2} tests.".format(design_name,len(err),num_tests))
		else:
			output_tasklevel.append("Design {0} passes all tests.".format(design_name))
			output_toplevel.append("Design {0} passes all tests.".format(design_name))
	else:
		# sequential
		filename = design_config['name'][0]+".out"
		if not os.path.exists(filename):
			errmsg = "ERROR: Design {0} output file {1} not found [Indicates possibly incorrect design file]".format(design_name,filename)
			print(errmsg)
			output_tasklevel.append(errmsg)
			output_toplevel.append(errmsg)
			scores.append(0)
			return 
		f = open(filename)
		num_i = len(design_config['inputs'])
		num_o = len(design_config['outputs'])
		traces_i = [[] for _ in range(num_i)]
		traces_o = [[] for _ in range(num_o)]
		err = []
		errsummary = ""
		score = design_config['maxscore']
		for l in f:
			if "VCD info:" in l:
				continue
			parsed_line = ["".join(e.split()) for e in l[:-1].split('\t')]
			inputs = parsed_line[0:num_i]
			for i in range(len(inputs)):
				traces_i[i].append(inputs[i])
			outputs = parsed_line[num_i:num_i+num_o]
			for i in range(len(outputs)):
				traces_o[i].append(outputs[i])
		f.close()
		if 'graderfunc' in design_config:
			err, errsummary, score, num_jobs, passed_jobs = design_config['graderfunc'](design_config,traces_i,traces_o)
		scores.append(score)
		if len(err)!=0:
			output_tasklevel.append("".join(err[0:4]))
			output_toplevel.append("Design {0} failed {1} out of {2} tests with {3}.".format(
				design_name,num_jobs-passed_jobs,num_jobs,errsummary))
		else:
			output_tasklevel.append("Design {0} passes all {1} tests.".format(design_name,num_jobs))
			output_toplevel.append("Design {0} passes all {1} tests.".format(design_name,num_jobs))

def writeResults(design_config_list,output_toplevel,output_tasklevel_list,scores,extra_credits=None):
	extra_credit_available = extra_credits!=None and any([('maxextracredit' in e) and (int(e['maxextracredit'])>0) and ('extracreditfunc' in e) for e in design_config_list])
	results = open(os.environ.get('AGHOME')+'/results/results.json', 'w') 
	results.write('{')
	results.write(' "output": "{0}",'.format(" ".join(output_toplevel)))
	results.write(' "tests":')
	results.write('  [')

	for i,design_config in enumerate(design_config_list):
		is_logisim_design = True if design_config.get('logisim',None)!=None else False
		if design_config['name'][1]:
			design_name = design_config['name'][0]+"."+design_config['name'][1]
		else:
			design_name = design_config['name'][0]
		results.write('   {')
		results.write('    "score": "{0}",'.format(scores[i]))
		#results.write('    "score": "0",'.format(scores[i]))
		results.write('    "max_score": "{0}",'.format(design_config['maxscore']))
		results.write('    "name": "[Autograder] {0}",'.format(design_name))
		results.write('    "output": "{0}",'.format(output_tasklevel_list[i]))
		design_filename = design_config['name'][0]+('.circ' if is_logisim_design else '.v')
		if os.path.exists(design_filename):
			results.write('    "extra_data": {{"md5":"{0}"}}'.format(hashlib.md5(open(design_filename,'rb').read()).hexdigest()))
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

def main():
	output_toplevel = []
	output_tasklevel_list = []
	scores = []
	for design_config in design_config_list:
		if not design_config['enabled']:
			print("\nSkipping {0}".format(design_config['name'][0]))
			output_tasklevel_list.append("Design {0} skipped.".format(design_config['name'][0]))
			scores.append(0)
			continue
		if design_config['name'][1]:
			design_name = design_config['name'][0]+"."+design_config['name'][1]
		else:
			design_name = design_config['name'][0]
		print("\nProcessing {0}".format(design_name))
		is_logisim_design = True if design_config.get('logisim',None)!=None else False
		output_tasklevel = []
		design_filename = design_config['name'][0]+('.circ' if is_logisim_design else '.v')
		if os.path.exists(design_filename):
			test_design(design_config,output_toplevel,output_tasklevel,scores,libList)
			output_tasklevel_list.append(" ".join(output_tasklevel))
		else:
			msg = "File {0} not found.".format(design_filename)
			print(msg)
			output_tasklevel_list.append(msg)
			scores.append(0)

	writeResults(design_config_list,output_toplevel,output_tasklevel_list,scores,None)

main()