#!/usr/bin/env python3
#
# Analyzing the gpt result file.
# Run without arguments to get instructions.
#
#-----------------------------------------------------------------
# Copyright 2023 Tanel Tammet (tanel.tammet@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------

# ==== standard libraries ====

import sys
import json
from collections import OrderedDict

import matplotlib.pyplot as plt



# ==== import other source files ====


# ======= configuration globals ===

debug=False # set to True to get a printout of data, call and result

helptext="""Usage example: ./analyze.py gptresults.js"""


varnr_range=[3,4,5,6,7,8,9,10,11,12,13,14,15]

# the range of max clause lengths of problems, for each variable number
cl_len_range=[3,4] # ok lens are between 2 and 5, inclusive 

# this small list will be iterated over: for True only horn problems are generated,
# for False all kinds of problems are generated, not just horn
horn_flags=[1,0]

# ========= code ===================

def main():
  if len(sys.argv)<2:
    print(helptext)
    return
  problemfile=None
  for el in sys.argv[1:]:       
    if " " not in el:
      problemfile=el 
  if not problemfile:
     show_error("problemfile not given")                  
  # read problemfile rows line by line, ignoring the first one
  try:
    f=open(problemfile, "r")
  except:
    show_error("could not open problem file "+problemfile)   
  problems=[]
  rowcount=0  
  while True:  
    try:
      row=f.readline().strip()
      if not row: break
      rowcount+=1     
      parsedrow=json.loads(row)
      problems.append(parsedrow)
    except:
      show_error("could not read problem file "+el)  
  f.close()
  # prepare empty result counters
  counts=makecounts() # this will be a key/value struct by maxvars 
  """
  {
   3 (maxvars): {3: (maxlen) : {0: (hornflag): [probcount,sat_correct_count,unsat_correct_count,answer_not_clear_count], 1(hornflag): ... }}
   4 (maxvars): { ... }
   ...
  }"
  """
  # analyze problems read, one by one, for basic details of statistics
  processed=0 
  print("Detailed results by maxvarnr/maxlen/hornflag:")
  print("Each sublist contains [problemcount,sat_correct,unsat_correct,unclear_answer_count]")
  for problem in problems:
    maxvars=problem[1]
    maxlen=problem[2]
    hornflag=problem[3]
    satflag=problem[4]
    if satflag==problem[8]: correctflag=1
    else: correctflag=0
    lst=counts[maxvars][maxlen][hornflag]
    lst[0]=lst[0]+1
    if satflag:
      lst[1]=lst[1]+correctflag
    else:
      lst[2]=lst[2]+correctflag
    if problem[8]==2:
      lst[3]=lst[3]+1   
  
  for key in counts:
    s=json.dumps(counts[key])
    s=s.replace("\"","")
    if key<10:
      print(key," : ",s)
    else:
      print(key,": ",s)

  # again analyze problems read, one by one, for combined sat/unsat percentage
  counts=makecounts() # this will be a key/value struct by maxvars 
  processed=0 
  print("Correctness percentages by maxvarnr/maxlen/hornflag:")
  print("Each sublist contains a correctness percentage for sat-and-unsat combined")
  for problem in problems:
    maxvars=problem[1]
    maxlen=problem[2]
    hornflag=problem[3]
    satflag=problem[4]
    if satflag==problem[8]: correctflag=1
    else: correctflag=0
    lst=counts[maxvars][maxlen][hornflag]
    lst[0]=lst[0]+1
    if satflag:
      lst[1]=lst[1]+correctflag
    else:
      lst[2]=lst[2]+correctflag
    if problem[8]==2:
      lst[3]=lst[3]+1   
  
  stopflag=False
  resgen=[]
  for varnr in varnr_range:
    if stopflag: break
    if varnr<10:
      print(varnr," :",end="")
    else:
      print(varnr,":",end="")      
    vardata=counts[varnr]
    overlens_ok_horn=0
    overlens_ok_gen=0
    overlens_total_horn=0
    overlens_total_gen=0
    for cllen in cl_len_range:
      print(" *len"+str(cllen),": ",end="")
      lendata=vardata[cllen]
      for hornflag in horn_flags:    
        horndata=lendata[hornflag]
        if horndata[0]==0: 
          stopflag=True
          break
        showdata=round((horndata[1]+horndata[2])/horndata[0],2)
        if hornflag:
          overlens_ok_horn+=(horndata[1]+horndata[2])
          overlens_total_horn+=horndata[0]
        else:
          overlens_ok_gen+=(horndata[1]+horndata[2])
          overlens_total_gen+=horndata[0]
        if cllen==4 and hornflag:
          resgen.append(showdata)
        s=f"{showdata:3.2f}"
        if hornflag:
          print("horn ",s,end="")
        else:
          print(" gene ",s,end="")
    print()

  # draw a diagram
  """
  ys = resgen
  xs = [x for x in range(3,13)]

  plt.plot(xs, ys)
  plt.show()
  # Make sure to close the plt object once done
  plt.close()"
  """

  # again analyze problems read, one by one, for proof depth stats
  counts=makecounts() # this will be a key/value struct by maxvars 
  processed=0 
  allstepcounts=[]
  provedstepcounts=[]
  provedcount=0
  for steps in range(0,1000):
    allstepcounts.append(0)
    provedstepcounts.append(0)
  print("Correctness percentages for provable, by proof depth:") 
  for problem in problems:
    maxvars=problem[1]
    maxlen=problem[2]
    hornflag=problem[3]
    satflag=problem[4]
    if satflag: continue
    # now we only consider provable ones
    provedcount+=1
    proof=problem[6]
    steps=0
    for el in proof:
      if el[1]: steps+=1
    #print(steps)  
    allstepcounts[steps]+=1
    if satflag==problem[8]: 
      # correctly solved
      provedstepcounts[steps]+=1
  print("total count of proofs",provedcount)    
  for i in range(0,1000):
    if allstepcounts[i]==0: continue
    print(i,allstepcounts[i],provedstepcounts[i],provedstepcounts[i]/allstepcounts[i])  


  # again analyze problems read, one by one, for horn proof depth stats
  counts=makecounts() # this will be a key/value struct by maxvars 
  processed=0 
  allstepcounts=[]
  provedstepcounts=[]
  provedcount=0
  for steps in range(0,1000):
    allstepcounts.append(0)
    provedstepcounts.append(0)
  print("Correctness percentages for provable horn problems, by proof depth:") 
  for problem in problems:
    maxvars=problem[1]
    maxlen=problem[2]
    hornflag=problem[3]
    satflag=problem[4]
    if satflag: continue
    # now we only consider provable ones
    if not hornflag: continue
    # now we only consider horn ones
    provedcount+=1
    proof=problem[6]
    steps=0
    for el in proof:
      if el[1]: steps+=1
    #print(steps)  
    allstepcounts[steps]+=1
    if satflag==problem[8]: 
      # correctly solved
      provedstepcounts[steps]+=1
  print("total count of horn problem proofs",provedcount)    
  for i in range(0,1000):
    if allstepcounts[i]==0: continue
    print(i,allstepcounts[i],provedstepcounts[i],provedstepcounts[i]/allstepcounts[i])    
  


def makecounts():
  counts=OrderedDict() # this will be a key/value struct by maxvars
  for varnr in varnr_range:
    cllendata=OrderedDict()
    for cllen in cl_len_range:
      horndata=OrderedDict()
      for hornflag in horn_flags:
        lst=[0,0,0,0]
        horndata[hornflag]=lst
      cllendata[cllen]=horndata
    counts[varnr]=cllendata   
  return counts  
   
def show_error(a):
  print("Error:",a)
  exit(0)  

if __name__ == "__main__":
  main()

# =========== the end ==========
