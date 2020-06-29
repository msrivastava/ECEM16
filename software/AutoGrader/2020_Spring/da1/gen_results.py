# EEM16

import re
import hashlib
import os.path
import os

libList = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O', 'HDL-IP', 'TCL', 'Base', 'BFH', 'CS410']

allowed_logisim = ["2.14.6", "2.14.8.2", "2.14.8.4"]

design_config_list = [
	{
		'name': ('da1_task1','DUT'),
		'logisim': '2.14.8.4',
		'maxscore': 20,
		'percent_deduction_per_error': 25,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['RAM', 'ROM'],
		'inputs': [
			{'name':'A', 'base':2, 'length':7}
		],
		'outputs': [
			{'name':'X3', 'base':2, 'length':32},
			{'name':'X2', 'base':2, 'length':32},
			{'name':'X1', 'base':2, 'length':32},
			{'name':'X0', 'base':2, 'length':32}
		]
	},
	{
		'name': ('da1_task2','DUT'),
		'logisim': '2.14.8.4',
		'maxscore': 30,
		'percent_deduction_per_error': 25,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['RAM', 'ROM'],
		'inputs': [
			{'name':'A', 'base':2, 'length':4},
			{'name':'B', 'base':2, 'length':4},
			{'name':'C', 'base':2, 'length':4}
		],
		'outputs': [
			{'name':'MEDIAN', 'base':2, 'length':4}
		]
	},
	{
		'name': ('da1_task3','DUT'),
		'logisim': '2.14.8.4',
		'maxscore': 30,
		'percent_deduction_per_error': 25,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['RAM', 'ROM'],
		'inputs': [
			{'name':'CODON', 'base':2, 'length':6}
		],
		'outputs': [
			{'name':'AA', 'base':2, 'length':5}
		]
	},
	{
		'name': ('da1_task4','DUT'),
		'logisim': '2.14.8.4',
		'maxscore': 60,
		'percent_deduction_per_error': 25,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['RAM', 'ROM', 'Multiplier', 'Divider'],
		'inputs': [
			{'name':'P', 'base':2, 'length':5},
			{'name':'K', 'base':2, 'length':5}
		],
		'outputs': [
			{'name':'C', 'base':2, 'length':5}
		]
	},
	{
		'name': ('da1_task5','DUT'),
		'logisim': '2.14.8.4',
		'maxscore': 60,
		'percent_deduction_per_error': 25,
		'allowed_libs': ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'Memory', 'I/O'],
		'disallowed_gates': ['RAM', 'ROM', 'Multiplier', 'Divider'],
		'inputs': [
			{'name':'D1', 'base':2, 'length':4},
			{'name':'D0', 'base':2, 'length':4}
		],
		'outputs': [
			{'name':'Z', 'base':2, 'length':7}
		]
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
	else:
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
		results.write('    "name": "Autgrader",')
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