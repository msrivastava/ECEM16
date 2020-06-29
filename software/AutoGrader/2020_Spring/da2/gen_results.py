# EEM16

import re
import hashlib
import os.path
import os

libList = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O', 'HDL-IP', 'TCL', 'Base', 'BFH', 'CS410']

allowed_logisim = ["2.14.8.2", "2.14.8.4", "2.14.6"]

# err, errsummary, score = design_config['graderfunc'](design_config,traces_i,traces_o)
def print_iotrace(design_config, traces_i, traces_o,header=None):
	t_max = len(traces_o[0])
	num_i = len(traces_i)
	num_o = len(traces_o)
	print("")
	print("{0}:".format(design_config['name'][0]))
	print("")
	if header:
		print(header)
	for t in range(t_max):
		for i in range(num_i):
			if i==0:
				# first field is CYCLE - print in base 10
				print(int(traces_i[i][t],base=2),end="\t")
			else:
				print(traces_i[i][t],end="\t")
		for i in range(num_o):
			print(traces_o[i][t],end="\t")
		print("")
	return

def default_sequential_grader(design_config, traces_i, traces_o):
	#print_iotrace(design_config, traces_i, traces_o)
	return [], "", design_config['maxscore']

def da2_task1_grader(design_config, traces_i, traces_o):
	print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tDIN\tDOUT")
	CYCLE = traces_i[0]
	RST = traces_i[1]
	DIN = traces_i[2]
	DOUT = traces_o[0]
	t_max = len(traces_o[0])
	state = 'before_reset'
	err = [] 
	button_presses = 0
	for t in range(1,t_max):
		# state changes
		if (state=='before_reset') and (RST[t-1]=='0' and RST[t]=='1'):
			state='being_reset'
		elif (state=='being_reset') and (RST[t-1]=='1' and RST[t]=='0'):
			state='done_reset'
		# check correctness of DOUT
		if (state=='done_reset'):
			if (DOUT[t].lower() not in {'0','1'}):
				err.append("ERROR: output DOUT is neither 0 nor 1 @ t={0}. Testing abandoned.".format(t))
				print(err[-1])
				errsummary = "Testing abandoned as circuit produced unknown output"
				score = 0
				return (err, errsummary, score)
			if (DIN[t-1]=='0' and DIN[t]=='1'):
				button_presses += 1
			if (t+1<t_max) and (DIN[t-1]=='0' and DIN[t]=='1') and (DOUT[t+1]!='1'):
				err.append("ERROR: Failed to assert DOUT=1 @ t={0}.".format(t+1))
				print(err[-1])
			if (DOUT[t]=='1') and (DOUT[t-1]=='1'):
				err.append("ERROR: DOUT=1 asserted for >1 clock edges at t={0}.".format(t))
				print(err[-1])
	errsummary = "{0} testing errors across {1} button presses".format(len(err),button_presses)
	if len(err)==0:
		score = design_config['maxscore']
	else:
		score = design_config['maxscore'] - 0.1*design_config['maxscore'] - max(len(err)-1,0)*design_config['maxscore']/max(button_presses,10)
	score = score if score>=0 else 0
	print("da2_task1: "+errsummary+".")
	return (err, errsummary, score)

def da2_task2_grader(design_config, traces_i, traces_o):
	#return default_sequential_grader(design_config, traces_i, traces_o)
	print_iotrace(design_config, traces_i, traces_o, "CYCLE\tRST\tDIN\tDOUT_S\tDOUT_L")
	CYCLE = traces_i[0]
	RST = traces_i[1]
	DIN = traces_i[2]
	DOUT_SHORT = traces_o[0]
	DOUT_LONG = traces_o[1]
	t_max = len(traces_o[0])
	state = 'before_reset'
	err = [] 
	button_presses = 0
	for t in range(1,t_max):
		# state changes
		if (state=='before_reset') and (RST[t-1]=='0' and RST[t]=='1'):
			state='being_reset'
		elif (state=='being_reset') and (RST[t-1]=='1' and RST[t]=='0'):
			state='done_reset'
		# check correctness of DOUT
		if (state=='done_reset'):
			if (DOUT_SHORT[t].lower() not in {'0','1'}):
				err.append("ERROR: output DOUT_SHORT is neither 0 nor 1 @ t={0}. Testing abandoned.".format(t))
				print(err[-1])
				errsummary = "Testing abandoned as circuit produced unknown output"
				score = 0
				return (err, errsummary, score)
			if (DOUT_LONG[t].lower() not in {'0','1'}):
				err.append("ERROR: output DOUT_LONG is neither 0 nor 1 @ t={0}.".format(t))
				print(err[-1])
				errsummary = "Testing abandoned as circuit produced unknown output"
				score = 0
				return (err, errsummary, score)
			if (DIN[t-1]=='0' and DIN[t]=='1'):
				button_presses += 1
				t_last_press = t
			if (t+1<t_max) and (button_presses>0) and (t-t_last_press<8) and (DIN[t-1]=='1' and DIN[t]=='0') and (DOUT_SHORT[t+1]!='1'):
				err.append("ERROR: Failed to assert DOUT_SHORT=1 @ t={0}.".format(t+1))
				print(err[-1])
			if (t+1<t_max) and (button_presses>0) and (t-t_last_press>=8) and (DIN[t-1]=='1' and DIN[t]=='0') and (DOUT_LONG[t+1]!='1'):
				err.append("ERROR: Failed to assert DOUT_LONG=1 @ t={0}.".format(t+1))
				print(err[-1])
			if (DOUT_SHORT[t]=='1') and (DOUT_SHORT[t-1]=='1'):
				err.append("ERROR: DOUT_SHORT=1 asserted for >1 clock edges at t={0}.".format(t))
				print(err[-1])
			if (DOUT_LONG[t]=='1') and (DOUT_LONG[t-1]=='1'):
				err.append("ERROR: DOUT_LONG=1 asserted for >1 clock edges at t={0}.".format(t))
				print(err[-1])
	errsummary = "{0} testing errors across {1} button presses".format(len(err),button_presses)
	if len(err)==0:
		score = design_config['maxscore']
	else:
		score = design_config['maxscore'] - 0.1*design_config['maxscore'] - max(len(err)-1,0)*design_config['maxscore']/max(button_presses,10)
	score = score if score>=0 else 0
	print("da2_task2: "+errsummary+".")
	return (err, errsummary, score)

def da2_task3_grader(design_config, traces_i, traces_o):
	print_iotrace(design_config, traces_i, traces_o,"CYCLE\tRST\tDIN\tDOUT")
	CYCLE = traces_i[0]
	RST = traces_i[1]
	DIN = traces_i[2]
	DOUT = traces_o[0]
	t_max = len(traces_o[0])
	state = 'before_reset'
	err = [] 
	remainder = 3
	num_bits = 0
	for t in range(1,t_max):
		# state changes
		if (state=='before_reset') and (RST[t-1]=='0' and RST[t]=='1'):
			state='being_reset'
			prevstate = 'before_reset'
		elif (state=='being_reset') and (RST[t-1]=='1' and RST[t]=='0'):
			state='done_reset'
			prevstate = 'being_reset'
		# check correctness of DOUT
		if (state=='done_reset'):
			if (DOUT[t].lower() not in {'0','1'}):
				err.append("ERROR: output DOUT is neither 0 nor 1 @ t={0}. Testing abandoned.".format(t))
				print(err[-1])
				errsummary = "Testing abandoned as circuit produced unknown output"
				score = 0
				return (err, errsummary, score)
			num_bits = num_bits+1
			if (remainder!=0 and DOUT[t]=='1'):
				err.append("ERROR: DOUT must be 0 @ t={0}.".format(t))
				print(err[-1])
			if (remainder==0 and DOUT[t]!='1'):
				err.append("ERROR: DOUT must be 1 @ t={0}.".format(t))
				print(err[-1])
			if DIN[t]=='0':
				remainder = [0, 2, 4, 0, 2, 4][remainder]
			else:
				remainder = [1, 3, 5, 1, 3, 5][remainder]
	errsummary = "{0} testing errors across {1} bits".format(len(err),num_bits)
	if len(err)==0:
		score = design_config['maxscore']
	else:
		score = design_config['maxscore'] - 0.1*design_config['maxscore'] - design_config['maxscore']*(len(err)-1)/(num_bits-1)
	score = score if score>=0 else 0
	print("da2_task3: "+errsummary+".")
	return (err, errsummary, score)

def da2_task4_grader(design_config, traces_i, traces_o):
	CYCLE = traces_i[0]
	RST = traces_i[1]
	RDY = traces_i[2]
	DIN = traces_i[3]
	DIN_printable = [None]*len(DIN)
	for i in range(len(DIN)):
		asciicode = int(DIN[i],base=2)
		c = chr(asciicode)
		DIN[i]=c
		if c==" ":
			DIN_printable[i]="SP"
		elif c=="\n":
			DIN_printable[i]="\\n"
		elif c=="\t":
			DIN_printable[i]="\\t"
		elif c.isprintable():
			DIN_printable[i]=c
		else:
			DIN_printable[i]="{0}".format(hex(asciicode))
	F = traces_o[0]
	traces_i[3] = DIN_printable
	print_iotrace(design_config, traces_i, traces_o,"CYCLE\tRST\tRDY\tDIN\tF")
	traces_i[3] = DIN
	t_max = len(traces_o[0])
	CORONA = "CORONA"
	COVID = "COVID"
	VIRUS = "VIRUS"
	max_buffer_len = max(len(CORONA),len(COVID),len(VIRUS))
	buffer = ""
	num_chars = 0
	state='before_reset'
	err = []
	for t in range(1,t_max):
		# state changes
		if (state=='before_reset') and (RST[t-1]=='0' and RST[t]=='1'):
			state='being_reset'
		elif (state=='being_reset') and (RST[t-1]=='1' and RST[t]=='0'):
			state='done_reset'
		# check correctness of F
		if (state=='done_reset') and (F[t].lower() not in {'0','1'}):
				err.append("ERROR: output F is neither 0 nor 1 @ t={0}. Testing abandoned.".format(t))
				print(err[-1])
				errsummary = "Testing abandoned as circuit produced unknown output"
				score = 0
				return (err, errsummary, score)
		#print("buffer @ {0} = {1}".format(t,buffer))
		if (state=='done_reset') and (RDY[t-1]=='1') and (buffer.endswith(CORONA) or buffer.endswith(COVID) or buffer.endswith(VIRUS)):
			if (F[t]!='1'):
				err.append("ERROR: F must be 1 @ t={0}.".format(t))
				print(err[-1])
				#print("buffer @ {0} = {1}".format(t,buffer))
				#print("DIN[t] @ {0} = {1}".format(t,hex(ord(DIN[t]))))
		elif (state=='done_reset') and (F[t]=='1'):
			err.append("ERROR: F must be 0 @ t={0}.".format(t))
			print(err[-1])
		# read character and put in buffer
		if (state=='done_reset') and (RDY[t]=='1'):
			num_chars = num_chars+1
			buffer = buffer + DIN[t].upper()
			if len(buffer)>max_buffer_len:
				buffer = buffer[1:]
			#print("buffer @ {0} = {1}".format(t,buffer))
	errsummary = "{0} testing errors across {1} input characters over {2} cycles".format(len(err),num_chars,t_max)
	if len(err)==0:
		score = design_config['maxscore']
	else:
		score = design_config['maxscore'] - 0.1*design_config['maxscore'] - design_config['maxscore']*(len(err)-1)/(num_chars-1)
	score = score if score>=0 else 0
	print("da2_task3: "+errsummary+".")
	return (err, errsummary, score)


design_config_list = [
	{
		'name': ('da2_task1','DUT'),
		'sequential': True,
		'maxscore': 15,
		'percent_deduction_per_error': "Equal",
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': [],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':8},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'DIN', 'base':2, 'length':1}
		],
		'outputs': [
			{'name':'DOUT', 'base':2, 'length':1}
		],
		'graderfunc': da2_task1_grader
	},
	{
		'name': ('da2_task2','DUT'),
		'sequential': True,
		'maxscore': 20,
		'percent_deduction_per_error': "Equal",
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': [],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':8},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'DIN', 'base':2, 'length':1}		
		],
		'outputs': [
			{'name':'DOUT_SHORT', 'base':2, 'length':1},
			{'name':'DOUT_LONG', 'base':2, 'length':1}
		],
		'graderfunc': da2_task2_grader
	},
	{
		'name': ('da2_task3','DUT'),
		'sequential': True,
		'maxscore': 25,
		'percent_deduction_per_error': "Equal",
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': [],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':8},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'DIN', 'base':2, 'length':1}		
		],
		'outputs': [
			{'name':'DOUT', 'base':2, 'length':1}
		],
		'graderfunc': da2_task3_grader
	},
	{
		'name': ('da2_task4','DUT'),
		'sequential': True,
		'maxscore': 40,
		'percent_deduction_per_error': "Equal",
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': [],
		'inputs': [
			{'name':'CYCLE', 'base':2, 'length':12},
			{'name':'RST', 'base':2, 'length':1},
			{'name':'RDY', 'base':2, 'length':1},
			{'name':'DIN', 'base':2, 'length':7}		
		],
		'outputs': [
			{'name':'F', 'base':2, 'length':1}
		],
		'graderfunc': da2_task4_grader
	},
	
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
			err, errsummary, score = design_config['graderfunc'](design_config,traces_i,traces_o)
		scores.append(score)
		if len(err)!=0:
			output_tasklevel.append("".join(err[0:4]))
			output_toplevel.append("Task {0} failed with {1}.".format(design_config['name'][0],errsummary))
		else:
			output_tasklevel.append("Task {0} passes all tests.".format(design_config['name'][0]))
			output_toplevel.append("Task {0} passes all tests.".format(design_config['name'][0]))

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
		results.write('    "max_score": "{0}",'.format(design_config['maxscore']))
		results.write('    "name": "Autograder",')
		results.write('    "output": "{0}",'.format(output_tasklevel_list[i]))
		circ_filename = design_config['name'][0]+'.circ'
		if os.path.exists(circ_filename):
			results.write('    "extra_data": {{"md5":"{0}"}}'.format(hashlib.md5(open(circ_filename,'rb').read()).hexdigest()))
		else:
			results.write('    "extra_data": {"md5":"none"}')
		if i<len(design_config_list)-1:
			results.write('   },')
		else:
			results.write('   }')

	results.write('  ]')
	results.write('}')
	results.close()

main()