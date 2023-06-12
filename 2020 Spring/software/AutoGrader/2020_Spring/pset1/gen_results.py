# EEM16

import re
import hashlib
import os.path
import os
from pyeda.inter import *
import yaml
import re
import pickle
from collections import Counter

DEFAULT_GRADINGINFO_FILE = 'grading_info.pkl'
DEFAULT_ANSWER_FILE = 'answers.txt'

class AutoGraderHelpers:
    # some helpers
    @staticmethod
    def checkAllStr(l):
        assert type(l) is list
        return all(type(e) is str for e in l)
    
    @staticmethod
    def checkAllList(l):
        assert type(l) is list
        return all(type(e) is list for e in l)
    
    # testin and answer are strings or list of stirngs, and are matched element by element
    @classmethod
    def matchElementInList(cls,answer,testin,cond=None,matchtype='exact'):
        assert matchtype in ['int','float','exact','nocase']
        assert cond in [None,'all','any']
        testin = [e.split() for e in testin.strip().split('\n')]
        assert type(answer) is str or cls.checkAllStr(answer)
        if type(answer) is str:
            answer = [answer]
        if matchtype=='int':
            flags = [int(e1)==int(e2) for e1,e2 in zip(answer,testin)]
        elif matchtype=='float':
            flags = [float(e1)==float(e2) for e1,e2 in zip(answer,testin)]
        elif matchtype=='nocase':
            flags = [e1.lower()==e2.lower() for e1,e2 in zip(answer,testin)]
        else:
            flags = [e1==e2 for e1,e2 in zip(answer,testin)]
        if cond=='all':
            return all(flags)
        elif cond=='any':
            return any(flags)
        else:
            return flags
        
    # each line of answer is expected to be a singleton or a list, and 
    # supposed to match to a corresponding singleton or a list of the same length
    @classmethod
    def matchList(cls,answer,testin,cond=None,ordered=False):
        assert cond in [None,'all','any']
        testin = [e.split() for e in testin.strip().split('\n')]
        assert cls.checkAllStr(answer) or (cls.checkAllList(answer) and all(cls.checkAllStr(e) for e in answer))
        if cls.checkAllStr(answer):
            answer = [answer]
        if len(answer)!=len(testin):
            return False
        if ordered:
            flags = [e1==e2 for e1,e2 in zip(answer,testin)]
        else:
            flags = [sorted(e1)==sorted(e2)for e1,e2 in zip(answer,testin)]
        if cond=='all':
            return all(flags)
        elif cond=='any':
            return any(flags)
        else:
            return flags
    
    #
    # answer: "D101010110101DDD"
    @staticmethod
    def boolEquivalentTruthTable(answer,testin):
        testin = testin.strip().split('\n')
        return False
    
    #
    # answer: [D110, 0110, 1DDD, 1001]
    @staticmethod
    def boolEquivalentKMap(answer,testin):
        testin = testin.strip().split('\n')
        return False
    
        
    # boolean expression string or a list of boolean expression strings
    @staticmethod
    def boolEquivalentExpression(vars,answer,testin,form=None,ops=None):
        testin = testin.strip().split('\n')
        assert type(answer) is str or type(answer) is list
        if type(answer) is str:
            answer = [answer]
        assert len(testin)==len(answer)
        assert form in [None, 'pos', 'sop', 'DNF', 'CNF']
        for _vn in vars:
            exec("{0}=exprvar('{0}')".format(_vn))
        _results=[]
        for _e1,_e2 in zip(answer,testin):
            _results.append(expr(_e1).equivalent(_e2))
        return _results
    
    @staticmethod
    def logisimCombinationalTester(answer,testin,config,logisim=None):
        pass

class YAMLHelpers:
    @staticmethod
    def extractHeader(allcontent):
        all_content = allcontent.strip().rstrip()
        yaml_header = {}
        if all_content[:3]=="---":
            i = all_content[4:].find("\n---")
            if i!=-1:
                try:
                    #import pdb; pdb.set_trace()
                    yaml_header = yaml.full_load(all_content[0:i+5])
                    all_content = all_content[i+9:].strip()
                except yaml.scanner.ScannerError as e:
                    raise SystemExit("Error: YAML Header has error: {0}".format(e))
                except:
                    raise SystemExit("Error: YAML Header has error")
        return (yaml_header,all_content)

class AutoGrader():
    def __init__(self, gradingfilename=DEFAULT_GRADINGINFO_FILE, answerfilename=DEFAULT_ANSWER_FILE):
        self.grading_info = {(e['probnum'],e.get('subprobnum',None),e.get('version',None)): {
            'answer_key':e.get('answer_key',None), 
            'probpoints':e.get('probpoints',None)} for e in list(pickle.load(open(gradingfilename,'rb')).values())[0]}
        self.answers = {(e['probnum'],e.get('subprobnum',None),e.get('version',None)): e.get('text',None)
                        for e in self.readAnswerFile(answerfilename)}

    @staticmethod
    def readAnswerFile(answerfilename):
        with open(answerfilename,'r') as f:
            content = f.read()
        header,body = YAMLHelpers.extractHeader(content)
        body = body.split('---\n')
        matcher = re.compile(r'(#(.*?)\n)+')
        answers = []
        for answer_text in body:
            if answer_text[0:8]!="# Answer":
                continue
            answer = {}
            m = re.search(r'# Answer\s+(\d+)(.(\d+))?(\s+\[ver(\d+)\])?\s*\n',answer_text)
            answer['probnum'] = m[1]
            if m[3]: answer['subprobnum'] = m[3]
            if m[5]: answer['version'] = m[5]
            answer['text'] = []
            answer_text_parts = matcher.sub('#\n',answer_text).split('#\n')
            for answer_text_part in answer_text_parts:
                if answer_text_part=="":
                    continue
                answer['text'].append(list(filter(lambda x: x!='',answer_text_part.split('\n'))))
            answers.append(answer)
        return answers
    
    @staticmethod
    def makePrettyProblemNumber(p):
        r = "Problem {0}".format(p[0])
        if len(p)>1 and p[1]:
            r += ", Subproblem {0}".format(p[1])
        if len(p)>2 and p[2]:
            r += ", Version {0}".format(p[2])
        return r
        
    def doGrading(self,sanityCheckOnly=True):
        # check that answer sheet only has questions that exist in the assignment
        if not set(self.answers.keys()).issubset(set(self.grading_info.keys())):
            m = "Submission has questions not in the assignment: {0}".format(
                set(self.answers.keys())-set(self.grading_info.keys()))
            
        # check that questions are answered only once
        C = Counter([(e[0],e[1]) for e in self.answers.keys()])
        results = {e:[] for e in self.grading_info.keys()}
        errmsg = ""
        for problem in C:
            if C[problem]>1:
                m = "Multiple answers for {0}".format(self.makePrettyProblemNumber(problem))
                print(m)
                results[problem] = {'error':[m]}
            else:
                results[problem] = {'error':[]}
        print(C)
        # now check format of anwers for every question
        for problem,answers in self.answers.items():
            if results[problem]!=[]:
                print("\nSkipping {0} due to prior error '{1}''".format(self.makePrettyProblemNumber(problem)),results[problem])
                continue
            else:
                print("\nAnalyzing {0}".format(self.makePrettyProblemNumber(problem)))
            #
            keys = self.grading_info.get(problem,{}).get('answer_key',[])
            if (len(answers)!=len(keys)):
                m = "Incorrect # of parts in answer for {0}: expected {1} parts, got {2} parts.".format(
                    self.makePrettyProblemNumber(problem),len(keys),len(answers))
                results[problem].append(m)
                print("\nSkipping {0} due to error '{1}''".format(self.makePrettyProblemNumber(problem)),m)
                print(m+"\n"+self.makePrettyProblemNumber(problem)+"\n"+str(answers)+"\n"+str(keys))
                continue
            #
            for partnum, (apart, kpart) in enumerate(zip(answers,keys)):
                print("\nTesting part {0} of {1}".format(partnum,self.makePrettyProblemNumber(problem)))
                if (kpart['type']=='int'):
                    a = [e.replace(',',' ').split() for e in apart]
                    if type(kpart['answer'])==list:
                        k = [e.split() if type(e)==str else e for e in eval(kpart['answer'])]
                    elif type(kpart['answer'])==str:
                        k = eval(kpart['answer'])
                    else:
                        m = "Configuration Error: answer in {0} should be string or list".format(kpart)
                        results[problem].append(m)
                        print("\nSkipping part {0} of {1} due to error '{2}''".format(partnum,self.makePrettyProblemNumber(problem)),m)
                        print(m+"\n"+self.makePrettyProblemNumber(problem)+"\n"+str(answers)+"\n"+str(keys))
                        continue
                    # check that number of lines in answer is the same as in key
                    if len(a)!=len(k):
                        m = "Incorrect # of lines in answer for part # {0} of {1}: expected {2} lines, got {3} lines.".format(
                            partnum,self.makePrettyProblemNumber(problem),len(k),len(a))
                        results[problem].append(m)
                        print("\nSkipping part {0} of {1} due to error '{2}''".format(partnum,self.makePrettyProblemNumber(problem)),m)
                        print(m+"\n"+self.makePrettyProblemNumber(problem)+"\n"+str(answers)+"\n"+str(keys))
                        continue
                    for i,e in enumerate(k):
                        print("Line #",i+1,": testing",e,"against",a[i])
    
                    continue
                elif (kpart['type']=='str'):
                    pass
                elif (kpart['type']=='float'):
                    pass
                elif (kpart['type']=='kmap'):
                    pass
                elif (kpart['type']=='truthtable'):
                    pass
                elif (kpart['type']=='file'):
                    pass
                elif (kpart['type']=='other'):
                    pass
            return results
        return results

def writeResults(msg_overall,tests):
    results = open(os.environ.get('AGHOME')+'/results/results.json', 'w') 
    results.write('{')
    results.write(' "output": "{0}",'.format(msg_overall))
    results.write(' "tests":')
    results.write('  [')

    for i,e in enumerate(tests):
        results.write('   {')
        results.write('    "score": "{0}",'.format(e['score']))
        results.write('    "max_score": "{0}",'.format(e['max_score']))
        results.write('    "name": "{0}",'.format(e['name']))
        results.write('    "output": "{0}"'.format(e['output']))
        if (i<len(tests)-1):
            results.write('   },')
        else:
            results.write('   }')
    results.write('  ]')
    results.write('}')
    results.close()

def getKeySetEqual(x,s):
    return set({e.split(':')[0].strip():e.split(':')[1].strip() for e in x}.keys())

def checkColorWheelCoding(x):
    colors = [
        'red', 'red-orange', 'orange', 'yellow-orange', 'yellow', 'yellow-green', 'green', 
        'blue-green', 'blue', 'blue-violet', 'violet', 'red-violet'
    ]
    answer = {e.split(':')[0].strip():e.split(':')[1].strip() for e in x}
    if set(answer.keys()) != set(colors):
        return False
    if any([len(e)!=4 and re.search(r"[01]{4}", e) for e in answer.values()]):
        return False
    current = answer[colors[-1]]
    used = []
    for c in colors:
        previous = current
        current = answer[c]
        if current in used:
            return False
        used.append(current)
        diff = False
        for i in range(4):
            if previous[i]!=current[i]:
                if diff:
                    return False
                else:
                    diff = True
    return True

def fixBooleanOperators(e):
    a = ""
    for i in range(len(e)):
        if e[i]=='!':
            a=a+'~'
        elif e[i]=='*':
            a=a+'&'
        elif e[i]=='+':
            a=a+'|'
        else:
            a=a+e[i]
    return a

def checkEquivExpr(vars,e1,e2):
    e1 = fixBooleanOperators(e1)
    e2 = fixBooleanOperators(e2)
    #print("checkEquivExpr({0},{1},{2})".format(vars,e1,e2))
    try:
        reply = AutoGraderHelpers.boolEquivalentExpression(vars,e1,e2)
    except:
        #print("Error in checkEquivExpr({0},{1},{2})".format(vars,e1,e2))
        reply = False
    return  reply

def grade_prob_3_4(x,maxscore):
    if len(x)!=4:
        print("Incorrect # of lines in answer for Problem 3.4")
        return 0
    e1 = fixBooleanOperators(x[2])
    e2 = fixBooleanOperators(x[3])
    form = x[1].upper()
    if x[0].strip()!='1':
        print("Incorrect answer for Problem 3.4")
        return 0
    if form not in ['CNF','DNF']:
        print("Incorrect answer for Problem 3.4")
        return 0
    if not checkEquivExpr(['a','b','c'],e1,'(~b & ~c) | (a & ((~b & c) | (b & ~c)))'):
        print("Incorrect answer for Problem 3.4")
        return 0
    if not checkEquivExpr(['a','b','c'],e2,'(~b & ~c) | (a & (~(b & c)))'):
        print("Incorrect answer for Problem 3.4")
        return 0
    if form=='DNF':
        # '(~a&~b&~c)|(a&~b&~c)|(a&~b&c)|(a&b&~c)'
        for v in ['a','b','c']:
            if e1.count(v)!=4 or e2.count(v)!=4:
                print("Incorrect answer for Problem 3.4")
                return 0
        if e1.count('&')!=8 or e2.count('&')!=8:
            print("Incorrect answer for Problem 3.4")
            return 0
        if e1.count('|')!=3 or e2.count('|')!=3:
            print("Incorrect answer for Problem 3.4")
            return 0
        if e1.count('~')!=7 or e2.count('~')!=7:
            print("Incorrect answer for Problem 3.4")
            return 0
    if form=='CNF':
        # (a ∨ ¬b ∨ c) ∧ (a ∨ ¬b ∨ ¬c) ∧ (a ∨ b ∨ ¬c) ∧ (¬a ∨ ¬b ∨ ¬c)
        for v in ['a','b','c']:
            if e1.count(v)!=4 or e2.count(v)!=4:
                print("Incorrect answer for Problem 3.4")
                return 0
        if e1.count('&')!=3 or e2.count('&')!=3:
            print("Incorrect answer for Problem 3.4")
            return 0
        if e1.count('|')!=8 or e2.count('|')!=8:
            print("Incorrect answer for Problem 3.4")
            return 0
        if e1.count('~')!=7 or e2.count('~')!=7:
            print("Incorrect answer for Problem 3.4")
            return 0
    return maxscore

def grade_prob_4_1(x,maxscore):
    # ['0 0 0 0 D', '0 0 0 1 1', '0 0 1 0 0', '0 0 1 1 1', '0 1 0 0 0', '0 1 0 1 1', '0 1 1 0 0', '0 1 1 1 1', '1 0 0 0 1', '1 0 0 1 0', '1 0 1 0 1', '1 0 1 1 0', '1 1 0 0 1', '1 1 0 1 D', '1 1 1 0 D', '1 1 1 1 D']
    TTref = {0: 'D', 1: '1', 2: '0', 3: '1', 4: '0', 5: '1', 6: '0', 7: '1', 
            8: '1', 9: '0', 10: '1', 11: '0', 12: '1', 13: 'D', 14: 'D', 15: 'D'}
    try:
        TTact = {int(''.join(e.split())[:4],base=2):''.join(e.split())[4] for e in x}
    except:
        print("Bad Truth Table syntax in Problem 4.1")
        return 0
    if not set(TTact.keys()).issubset(TTref.keys()):
        print("Bad Truth Table entry in Problem 4.1")
        return 0
    for i in range(16):
        if TTref[i]!=TTact.get(i,'D'):
            print("Incorrect answer for Problem 4.1")
            return 0
    return maxscore

def grade_prob_5_1_1(x,maxscore):
    TTref = {0: '1', 1: '1', 2: '1', 3: '1', 4: '1', 5: '1', 6: '1', 7: '0', 
             8: '1', 9: '1', 10: '1', 11: '0', 12: '1', 13: '0', 14: '0', 15: '0'}
    try:
        TTact = {int(''.join(e.split())[:4],base=2):''.join(e.split())[4] for e in x}
    except:
        print("Bad Truth Table syntax in Problem 5.1 ver1")
        return 0
    if not set(TTact.keys()).issubset(TTref.keys()):
        print("Bad Truth Table entry in Problem 5.1 ver1")
        return 0
    for i in range(16):
        if TTref[i]!=TTact.get(i,'D'):
            print("Incorrect answer for Problem 5.1 ver1")
            return 0
    return maxscore

def grade_prob_5_1_3(x,maxscore):
    # (~a & ~b) | (~a & ~c) | (~a & ~d) | (~b & ~c) | (~b &  ~d) | (~c &  ~d)
    e = fixBooleanOperators(x[0])
    vars = ['a','b','c','d']
    if not checkEquivExpr(vars, e, '(~a & ~b) | (~a & ~c) | (~a & ~d) | (~b & ~c) | (~b &  ~d) | (~c &  ~d)'):
        print("Incorrect answer for Problem 5.3 ver1")
        return 0
    max_literals = 12
    literal_count = sum([e.count(x) for x in vars])
    score = maxscore * (1-0.2*max(0,(literal_count-max_literals)))
    if literal_count<max_literals:
        print("Your # of literals for Problem 5.3 ver1 is {0}, which less than that of the reference solution {1}!".format(
            literal_count, max_literals))
    elif literal_count>max_literals:
        print("Your # of literals for Problem 5.3 ver1 is {0}, which is higher than expected {1}. Penalty of {2} applied.".format(
            literal_count, max_literals, maxscore*0.2*max(0,(literal_count-max_literals))))
    return score


def grade_prob_5_2_3(x,maxscore):
    prime_implicants = set(['~p & r', 'q & r', 'p & q'])
    incorrect_pi = []
    missing_pi = []

    for pi_act in x:
        pi_act = fixBooleanOperators(pi_act)
        if not any([checkEquivExpr(['p','q','r'],pi_act,pi_ref) for pi_ref in prime_implicants]):
            incorrect_pi.append(pi_act)
    for pi_ref in prime_implicants:
        if not any([checkEquivExpr(['p','q','r'],fixBooleanOperators(pi_act),pi_ref) for pi_act in x]):
            missing_pi.append(pi_ref)
    if len(incorrect_pi)>0:
        print("Incorrect Prime Impliants in 5.3 ver2: {0}".format(incorrect_pi))
    if len(missing_pi)>0:
        print("Missing Prime Impliants in 5.3 ver2: {0}".format(missing_pi))
    return max(0,0.5*(len(incorrect_pi)+len(missing_pi)))*maxscore

def grade_prob_5_2_4(x,maxscore):
    # (~p & r) | (p & q)
    if len(x)!=1:
        print("Incorrect # of lines in answer for Problem 5.4 ver2")
        return 0
    e = fixBooleanOperators(x[0])
    if not checkEquivExpr(['p','q','r'],e,'(~p & r) | (p & q)'):
        print("Incorrect answer for Problem 5.4 ver2")
        return 0
    return maxscore

def grade_prob_6_1(x,maxscore):
    # ['out0 = (in2 | in1 | in0)', 'out1 = (in2 | in1)', 'out2 = (in2 | in1) & (in2 | in0)', 'out3 = in2', 'out4 = in2 & (in1 | in0)', 'out5 = in2 & in1', 'out6 = in2 & in1 & in0'], 
    if len(x)!=7:
        print("Incorrect # of lines in answer for Problem 6.1")
        return 0
    y = []
    for e in x:
        y.append(fixBooleanOperators(''.join(e.split('=')[-1].split())))
    ref = ['(in2 | in1 | in0)', '(in2 | in1)', '(in2 | in1) & (in2 | in0)', 'in2', 
        'in2 & (in1 | in0)', 'in2 & in1', 'in2 & in1 & in0']
    literals = [3,2,4,1,3,2,3]
    score = 0
    for i in range(7):
        if y[i].count('in')>literals[i]:
            print("Too many literals in expression for out{0} in Problem 6.1".format(i))
            continue
        if not checkEquivExpr(['in0','in1','in2'],y[i],ref[i]):
            print("Incorrect expression for out{0} in Problem 6.1".format(i))
            continue
        score = score + maxscore/7
    return maxscore


def grade_prob_7_2(x,maxscore):
    # ['x -> 0', '((x -> 0) -> y)'],
    if len(x)!=2:
        print("Incorrect # of lines in answer for Problem 7.2")
        return 0
    ref = ['x->0', '(x->0)->y']
    for i in range(2):
        e = ''.join(fixBooleanOperators(x[i]).split())
        while e[0]=='(' and e[-1]==')':
            e = e[1:-1]
        if e!=ref[i]:
            print("Incorrect answer {0} for Problem 7.2")
            return 0
    return maxscore

def grade_prob_7_3(x,maxscore):
    # ['~p', '1', '(~p&~q)|(p&q)']
    if len(x)!=3:
        print("Incorrect # of lines in answer for Problem 7.3")
        return 0
    score = 0
    count_p = [1,0,2]
    count_q = [0,0,2]
    ref = ['~p', '1', '(~p&~q)|(p&q)']
    for i in range(3):
        e = ''.join(fixBooleanOperators(x[i]).split())
        if not checkEquivExpr(['p','q'],fixBooleanOperators(x[i]),ref[i]) or count_p[i]!=x[i].count('p') or count_q[i]!=x[i].count('q'):
            print("Incorrect answer {0} for Problem 7.3.{1}".format(x[i],i))
        else:
            score = score + maxscore/3
    return score

probspec = [
    {
        'probnum': '1', 
        'maxscores': [1, 4],
        'graderfunc': [
            lambda x: 1 if len(x)==1 and x[0].strip()=='4' else 0,
            lambda x: 4 if len(x)==12 and checkColorWheelCoding(x) else 0
        ],
        'sample': [
            ['4'], 
            ['red: 0000', 'red-orange: 0001 ', 'orange: 0011', 'yellow-orange:  0010', 'yellow: 0110', 'yellow-green: 0111 ', 'green: 0101', 'blue-green: 0100 ', 'blue: 1100', 'blue-violet: 1110 ', 'violet: 1010', 'red-violet: 1000']
        ]
    }, 
    {
        'probnum': '2', 
        'maxscores': [5/7]*7,
        'graderfunc': [
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='2' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='5' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='3' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='3' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='27' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='17' else 0,
            lambda x: 5/7 if len(x)==1 and x[0].strip()=='12' else 0
        ],
        'sample': [['2'], ['5'], ['3'], ['3'], ['27'], ['17'], ['12']]
    }, 
    {
        'probnum': '3',
        'subprobnum': '1',
        'maxscores': [3],
        'graderfunc': [
            lambda x: 3 if (len(x)==1 and all([e in ['a','b','c','d','&','|','~','*','+','!',' ','(',')'] for e in x[0]]) 
                and checkEquivExpr(['a','b','c','d'],x[0],'((a&b)|(c|d))&(~(a&b)|~(c|d))')) else 0
        ],
        'sample': [['((a&b)|(c|d))&(~(a&b)|~(c|d))']]
    },
    {
        'probnum': '3',
        'subprobnum': '2',
        'maxscores': [3],
        'graderfunc': [
            lambda x: 3 if (len(x)==1 and all([e in ['a','b','c','d','&','|','~','*','+','!',' ','(',')'] for e in x[0]]) 
                and checkEquivExpr(['a','b','c'],x[0],'~a & c')
                and x[0].count('a')==2 and x[0].count('b')==2 and x[0].count('c')==2
                and fixBooleanOperators(x[0]).count('|')==1 and fixBooleanOperators(x[0]).count('&')==4 
                and fixBooleanOperators(x[0]).count('~')==3
                ) else 0
        ],
        'sample': [['(~a&~b&c)|(~a&b&c)']]
    },
    {
        'probnum': '3',
        'subprobnum': '3',
        'maxscores': [2.5,0],
        'graderfunc': [
            lambda x: 2.5 if len(x)==1 and x[0].split()[0]=='32' and x[0].split()[1]=='32' else 0,
            None # manual pdf
        ],
        'sample': [['32 32'], ['3_3.pdf']]
    },
    {
        'probnum': '3',
        'subprobnum': '4',
        'maxscores': [4],
        'graderfunc': [
            lambda x: grade_prob_3_4(x,4)
        ],
        'sample': [['1', 'DNF', '(~a&~b&~c)|(a&~b&~c)|(a&~b&c)|(a&b&~c)', '(~a&~b&~c)|(a&~b&~c)|(a&~b&c)|(a&b&~c)']]
    }, 
    {
        'probnum': '4',
        'maxscores': [2.5,2.5,5,0],
        'graderfunc': [
            lambda x: grade_prob_4_1(x,2.5),
            lambda x: 2.5 if len(x)==4 and set([''.join(e.split()) for e in x])=={'0110', '1001', '1DDD', 'D110'} else 0,
            lambda x: 5 if len(x)==1 and checkEquivExpr(['M3','M2','M1','M0'],x[0],'(~M3&M0)|(M3&~M0)') else 0,
            lambda x: 0 # placeholder for .circ
        ],
        'sample': [
            ['0 0 0 0 D', '0 0 0 1 1', '0 0 1 0 0', '0 0 1 1 1', '0 1 0 0 0', '0 1 0 1 1', '0 1 1 0 0', '0 1 1 1 1', '1 0 0 0 1', '1 0 0 1 0', '1 0 1 0 1', '1 0 1 1 0', '1 1 0 0 1', '1 1 0 1 D', '1 1 1 0 D', '1 1 1 1 D'], 
            ['D 1 1 0', '0 1 1 0', '1 D D D', '1 0 0 1'], 
            ['(~M3&M0)|(M3&~M0)'], ['assets_4/month31.circ']
        ]
    },
    {
        'probnum': '5',
        'version': '1', # coolean counting
        'maxscores': [2.5,2.5,5,0],
        'graderfunc': [
            lambda x: grade_prob_5_1_1(x,2.5),
            lambda x: 2.5 if len(x)==4 and set([''.join(e.split()) for e in x])=={'1111','1101','1000','1101'} else 0,
            lambda x: grade_prob_5_1_3(x,5),
            lambda x: 0
        ]
    },
    {
        'probnum': '5',
        'version': '2', # ternary
        'maxscores': [2,2,2,4,0],
        'graderfunc': [
            lambda x: 2 if len(x)==8 and set([''.join(e.split()) for e in x])=={'0000', '0011', '0100', '0111', '1000', '1010', '1101', '1111'} else 0,
            lambda x: 2 if len(x)==2 and set([''.join(e.split()) for e in x])=={'0110', '0011'} else 0,
            lambda x: grade_prob_5_2_3(x,2),
            lambda x: grade_prob_5_2_4(x,4),
            lambda x: 0 # placeholder for .circ
        ],
        'sample': [
            ['0 0 0 0', '0 0 1 1', '0 1 0 0', '0 1 1 1', '1 0 0 0', '1 0 1 0', '1 1 0 1', '1 1 1 1'],
            ['0 1 1 0', '0 0 1 1'],
            ['p & q', '~p & r', 'q &'],
            ['(p&q)|(~p&r)'],
            ['assets_5/ternary_operator.circ']
        ]
    }, 
    {
        'probnum': '6',
        'maxscores': [10,0],
        'graderfunc': [
            lambda x: grade_prob_6_1(x,10),
            lambda x: 0 # placeholder for .circ
        ],
        'text': [
            ['out0 = (in2 | in1 | in0)', 'out1 = (in2 | in1)', 'out2 = (in2 | in1) & (in2 | in0)', 'out3 = in2', 'out4 = in2 & (in1 | in0)', 'out5 = in2 & in1', 'out6 = in2 & in1 & in0'], 
            ['assets_6/thermometer_encoder.circ']
        ]
    },
    {
        'probnum': '7',
        'maxscores': [3,4,3],
        'graderfunc': [
            lambda x: 3 if len(x)==4 and set([''.join(e.split()) for e in x])=={'001', '011', '100', '111'} else 0,
            lambda x: grade_prob_7_2(x,4),
            lambda x: grade_prob_7_3(x,3)
        ],
        'sample': [
            ['0 0 1', '0 1 1', '1 0 0', '1 1 1'],
            ['x -> 0', '((x -> 0) -> y)'],
            ['~p', '1', '(~p&~q)|(p&q)']
        ]
    },
    {
        'probnum': '8',
        'maxscores': [0],
        'graderfunc': [None],
        'sample': [['8.pdf']]
    }, 
    {
        'probnum': '9',
        'maxscores': [0],
        'graderfunc': [None],
        'sample': [['9.pdf']]
    }
]

def main():

    answers = AutoGrader.readAnswerFile("answers.txt")

    tests = []

    error_flag = False

    for e in answers:
        msg_test = []
        print("")
        print(e)
        probnum = e.get('probnum',None)
        subprobnum = e.get('subprobnum',None)
        version = e.get('version',None)
        if probnum==None:
            print("Skipping answer with unknown problem {0}".format(e))
            continue
        ps = None
        for f in probspec:
            if probnum==f.get('probnum',None) and subprobnum==f.get('subprobnum',None) and version==f.get('version',None):
                ps = f
                break
        if ps==None:
            print("Couldn't find how to grade answer {0}".format(e))
            continue
        if len(e.get('text',[]))!=len(ps['graderfunc']):
            print("Mismatch with specification for {0}".format(e))
            continue
        score = 0
        probname = e['probnum'] + ("."+e['subprobnum'] if 'subprobnum' in e else "") +  (".ver"+e['version'] if 'version' in e else "")
        for i,f in enumerate(e.get('text',[])):
            score_incr = (ps['graderfunc'][i](f) if ps['graderfunc'][i] else 0)
            #print("i : f = {0}".format(score_incr))
            if score_incr < ps['maxscores'][i]:
                msg = "Error in part {0} of Problem {1} from answer {2}.".format(i,probname,f)
                error_flag = True
                msg_test.append(msg)
            score = score + score_incr

        tests.append({
            "score": score,
            "max_score": sum(ps['maxscores']), 
            "name": "Problem {0}".format(probname),
            "output": "{0}".format(" ".join(msg_test))
            })
    if error_flag:
        msg_overall = "There were errors in your submission. See test details."
    else:
        msg_overall = "Congratulations - you had no errors!"

    writeResults(msg_overall,tests)

main()