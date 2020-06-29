# EEM16

import re
import hashlib
import os.path
import os

libList = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O', 'HDL-IP', 'TCL', 'Base', 'BFH', 'CS410']

allowed_logisim = ["2.14.8.2", "2.14.8.4", "2.14.6"]

# err, errsummary, score = design_config['graderfunc'](design_config,traces_i,traces_o)
def print_iotrace(design_config, traces_i, traces_o,header=None,t_range=None,suffix=None):
	t_max = len(traces_o[0])
	num_i = len(traces_i)
	num_o = len(traces_o)

	if header:
		print("")
		print("{0}:".format(design_config['name'][0]))
		print("")
		print(header)
	if not t_range:
		t_range = range(t_max)
	for t in t_range:
		for i in range(num_i):
			if i==0:
				# first field is CYCLE - print in base 10
				print(int(traces_i[i][t],base=2),end="\t")
			else:
				print(traces_i[i][t],end="\t")
		for i in range(num_o):
			print(traces_o[i][t],end="\t")
		if suffix:
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

def da3_grader(design_config, traces_i, traces_o):
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
	LDCTR = traces_o[5]
	CTRVALIN = traces_o[6]
	CTRDONE = traces_o[7]
	CTRVALOUT = traces_o[8]

	err = []
	t_max = len(traces_o[0])

	if t_max==1:
		err.append("ERROR: circuit fails to simulate due to apparent oscillation. Testing abandoned.")
		print(err[-1])
		errsummary = "Testing abandoned as Logisim failed to simulate the circuit"
		score = 0
		return (err, errsummary, score)

	# validate that circuit output is all binary
	if not all([isBinaryTrace(e) for e in [Q, R, FDBZ, ACK]]):
		err.append("ERROR: some outputs are non binary, i.e. neither 0 nor 1. Testing abandoned.")
		print(err[-1])
		errsummary = "Testing abandoned as circuit produced non binary output"
		score = 0
		return (err, errsummary, score)

	for i in range(len(A)):
		A[i] = twos(A[i],2)
		D[i] = twos(D[i],2)
		Q[i] = twos(Q[i],2)
		R[i] = twos(R[i],2)
		REQNUM[i] = int(REQNUM[i],base=2)
		CTRVALIN[i] = int(CTRVALIN[i],base=2)
		CTRVALOUT[i] = int(CTRVALOUT[i],base=2)
	#print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tREQ\tA\tD\tQ\tR\tFDBZ\tACK")

	

	
	score = 0
	score_function = design_config['maxscore']*2/3
	score_speed = design_config['maxscore']*1/3
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

	print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tREQ\tA\tD\tQ\tR\tFDBZ\tACK\tREQNUM\tLDCTR\tCTRVALI\tCTRDONE\tCTRVALO",range(1),"init")
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
					print("Job #{0} Arrived: A={1}, D={2}, Q={3}, R={4}, FDBZ={5} @ t={6}".format(num_jobs,curA,curD,expectedQ,expectedR,expectedFDBZ,t))
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
							err.append("ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t]))
							print(err[-1])
						if treq>0 and Q[t]==expectedQ and R[t]==expectedR and FDBZ[t]==expectedFDBZ:
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
						err.append("ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t]))
						print(err[-1])
					if treq>0 and Q[t]==expectedQ and R[t]==expectedR and FDBZ[t]==expectedFDBZ:
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
							err.append("ERROR: FDBZ must be {0} @ t={1} but is {2}.".format(expectedFDBZ,t,FDBZ[t]))
							print(err[-1])
				if (REQ[t-1]=='1') and (REQ[t]=='0'):
					if ACK[t]=='1':
						substate='req0ack1'
					else:
						# ACK became 0 immediately
						substate='req0ack0'
			elif substate=='req0ack1':
				if (ACK[t-1]=='1') and (ACK[t]=='0'):
					substate='req0ack0'
		#currvals = (RST[t],REQ[t],A[t],D[t],Q[t],R[t],FDBZ[t],ACK[t],REQNUM[t],LDCTR[t],CTRVALIN[t],CTRDONE[t],CTRVALOUT[t])
		#priorvals = (RST[t-1],REQ[t-1],A[t-1],D[t-1],Q[t-1],R[t-1],FDBZ[t-1],ACK[t-1],REQNUM[t-1],LDCTR[t-1],CTRVALIN[t-1],CTRDONE[t-1],CTRVALOUT[t])
		#currvals = (RST[t],REQ[t],A[t],D[t],Q[t],R[t],FDBZ[t],ACK[t],REQNUM[t],LDCTR[t],CTRDONE[t])
		#priorvals = (RST[t-1],REQ[t-1],A[t-1],D[t-1],Q[t-1],R[t-1],FDBZ[t-1],ACK[t-1],REQNUM[t-1],LDCTR[t-1],CTRDONE[t-1])
		currvals = (RST[t],REQ[t],A[t],D[t],Q[t],R[t],FDBZ[t],ACK[t],REQNUM[t])
		priorvals = (RST[t-1],REQ[t-1],A[t-1],D[t-1],Q[t-1],R[t-1],FDBZ[t-1],ACK[t-1],REQNUM[t-1])
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
	score = score if score<=design_config['maxscore'] else design_config['maxscore']
	errsummary = "{0} testing errors across {1} total jobs and {2} passed jobs over {3} cycles with functionality score = {4} and speed score = {5}".format(
		len(err),num_jobs,passed_jobs,t_max,fs,ss)
	print("da3: "+errsummary+".")
	return (err, errsummary, score, num_jobs, passed_jobs)


design_config_list = [
	{
		'name': ('da3','DUT'),
		'sequential': True,
		'maxscore': 75,
		'percent_deduction_per_error': "Equal",
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
			{'name':'LDCTR', 'base':2, 'length':1},
			{'name':'CTRVALIN', 'base':2, 'length':4},
			{'name':'CTRDONE', 'base':2, 'length':1},
			{'name':'CTRVALOUT', 'base':2, 'length':4}
		],
		'graderfunc': da3_grader
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
	design, logisim = read_design(design_config['name'][0])
	err_hasValidGates = []
	if not logisim in allowed_logisim:
		scores.append(0)
		output_tasklevel.append("Task {0} uses Logisim version {1} which is not allowed.".format(design_config['name'][0], logisim))
		output_toplevel.append("Invalid Logisim used in Task {0}.".format(design_config['name'][0]))
		return
	elif not design_config['name'][1] in design.keys():
		scores.append(0)
		output_tasklevel.append("Didn't find design {0} in Task {1}.".format(design_config['name'][1],design_config['name'][0]))
		output_toplevel.append("Design not found for Task {0}.".format(design_config['name']))
		return
	elif not hasValidGates(design, design_config['name'][1], design_config['allowed_libs'], design_config['disallowed_gates'], err_hasValidGates, libList):
		scores.append(0)
		output_tasklevel.append(" ".join(err_hasValidGates))
		output_toplevel.append("Task {0} using disallowed gate.".format(design_config['name'][1]))
		return
	elif not design_config.get('sequential',False):
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
		f = open(design_config['name'][0]+".out")
		num_i = len(design_config['inputs'])
		num_o = len(design_config['outputs'])
		traces_i = [[] for _ in range(num_i)]
		traces_o = [[] for _ in range(num_o)]
		err = []
		errsummary = ""
		score = design_config['maxscore']
		for l in f:
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
			output_toplevel.append("Task {0} failed {1} out of {2} tests with {3}.".format(
				design_config['name'][0],num_jobs-passed_jobs,num_jobs,errsummary))
		else:
			output_tasklevel.append("Task {0} passes all {1} tests.".format(design_config['name'][0],num_jobs))
			output_toplevel.append("Task {0} passes all {1} tests.".format(design_config['name'][0],num_jobs))

def main():
	output_toplevel = []
	output_tasklevel_list = []
	scores = []
	for design_config in design_config_list:
		output_tasklevel = []
		circ_filename = design_config['name'][0]+'.circ'
		if os.path.exists(circ_filename):
			test_design(design_config,output_toplevel,output_tasklevel,scores,libList)
			output_tasklevel_list.append(" ".join(output_tasklevel))
		else:
			output_tasklevel_list.append("File {0} not found.".format(circ_filename))
			scores.append(0)

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
		results.write('    "name": "Autograder",')
		results.write('    "output": "{0}",'.format(output_tasklevel_list[i]))
		circ_filename = design_config['name'][0]+'.circ'
		if os.path.exists(circ_filename):
			results.write('    "extra_data": {{"md5":"{0}"}}'.format(hashlib.md5(open(circ_filename,'rb').read()).hexdigest()))
		if i<len(design_config_list)-1:
			results.write('   },')
		else:
			results.write('   }')

	results.write('  ]')
	results.write('}')
	results.close()

main()