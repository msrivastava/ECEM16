#!/usr/bin/env python3
# coding: utf-8

# In[1]:


import pickle
import csv
import os
import yaml
import sys
import argparse


# In[2]:


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


# In[3]:


def readRosterFile(roster_filename='roster.csv'):
    with open(roster_filename, newline='') as csvfile:
        roster_reader = csv.reader(csvfile, delimiter=',', 
                                   quotechar='|', skipinitialspace=True)
        roster = []
        for row in roster_reader:
            roster.append([row[0].strip(), row[1].strip().split()[0],row[2].strip().split()[0]])
    return roster


# In[48]:


def readAnswerFile(answerfilename):
    with open(answerfilename,'r') as f:
        content = f.read()
    header,_ = extractHeader(content)
    return header


# In[57]:


def main(args):
    roster = readRosterFile(args.roster)
    student = readAnswerFile(args.answers)['student'].split()
    fn = student[0]
    ln = student[1]
    student_record = [e for e in roster if e[1].lower()==ln.lower() and e[2].lower()==fn.lower()]
    assert len(student_record)==1, "There should be exactly one student named {0} {1}".format(fn,ln)
    student_record = tuple(student_record[0])
    grading_info = pickle.load(open(args.gradinginfo,'rb'))[student_record]
    prob_info = [e for e in grading_info if e['probnum']==str(args.probnum)][0]
    print(prob_info.get('version',0))


# In[62]:


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser(description='Get version of problem assigned to the student.')
    parser.add_argument("probnum",help="Problem number.",type=int)
    parser.add_argument("-a","--answers",nargs=1,default="answers.txt",help="Answers file.")
    parser.add_argument("-r","--roster",nargs=1,default="/autograder/source/roster.csv",help="Roster file.")
    parser.add_argument("-g","--gradinginfo",nargs=1,default="/autograder/source/grading_info.pkl",help="Instructor mode.")
    if ("ipykernel_launcher" in sys.argv[0]):
        args = parser.parse_args("5 -r ../source/roster.csv -g ../source/grading_info.pkl -a answers_sample_1.txt".split())
        os.chdir('/Users/mbs/Google Drive/Courses/ECEM16/2020 Spring/psets/pset1/Autograder/submission')
    else:
        args = parser.parse_args()
    if type(args.answers)==list:
        args.answers = args.answers[0]
    if type(args.roster)==list:
        args.roster = args.roster[0]
    if type(args.gradinginfo)==list:
        args.gradinginfo = args.gradinginfo[0]
    main(args)


# In[ ]:





# In[ ]:




