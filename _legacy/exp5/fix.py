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



# ==== import other source files ====


# ======= configuration globals ===


helptext="""Usage example: ./fix.py gptresults.js"""


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
  # fix problemfile
  fixed_problems=[]
  for i in range(0,len(problems)):
    problem=problems[i]
    #if i==0: 
    #  fixed_problems.append(problem)
    #  continue
    satflag=problem[4]
    assumedsat=problem[8]
    txt=problem[9]
    txt=txt.replace("."," ").replace(","," ").replace(":"," ").replace("*"," ").replace("'"," ").replace("\n"," ").replace("\r"," ").replace("`"," ")
    
    place=txt.find("Answer")
    if place>0:
      txt=txt[place:]
    else:
      place=txt.find("answer")
      if place>0:
        txt=txt[place:] 
    txt=txt.lower()  
    sp=txt.split(" ")
    res=1
    for el in sp:
      if el.strip() in ["yes"]:
        res=0
        break
    if res!=assumedsat:
      problem[8]=res
      #print("initially given: ",assumedsat)
      #print(problem[9])
      #print()
    s=json.dumps(problem)
    print(s)



def show_error(a):
  print("Error:",a)
  exit(0)  

if __name__ == "__main__":
  main()

# =========== the end ==========
