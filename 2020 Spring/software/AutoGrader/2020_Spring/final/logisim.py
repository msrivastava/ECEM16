import os
import re

def readLogisimDesign(circ_filename):
	f = open(circ_filename,'r')
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
	f.close()
	return design, logisim

def getGateStats(circ_filename,main_circuit,java_binary,logisim_jar):
	if not os.path.exists(circ_filename):
		return None
	if not os.path.exists(logisim_jar):
		return None
	new_name = os.path.splitext(circ_filename)[0]+"_"+main_circuit
	new_circfilename = new_name+".circ"
	pattern = re.compile('<main name="(.+)"/>')
	fin = open(circ_filename,'r')
	fout = open(new_circfilename,'w')
	for i, line in enumerate(fin):
		fout.write(re.sub(pattern,'<main name="{0}"/>'.format(main_circuit),line[0:-1]+'\r\n'))
	fin.close()
	fout.close()
	status = os.system('java -jar {0} {1} -tty stats > {2}.stats'.format(logisim_jar,new_circfilename,new_name))
	#os.remove(new_circfilename)
	statfile = open(new_name+".stats","r")
	stats = []
	for line in statfile.readlines():
		data = [e.strip() for e in line.split('\t')]
		if data[2][:5]=='TOTAL' or data[3]==new_name:
			continue
		stats.append(data)
	return stats
