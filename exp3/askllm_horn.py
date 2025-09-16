#!/usr/bin/env python3
#
# Experimenting with the gpt api
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
import http.client
import time

# ==== import other source files ====


# ======= llm configuration ===

secrets_file="secrets.json"

gpt2="davinci-002"         # text-davinci-002 code-davinci-002 babbage-002 
gpt3="gpt-3.5-turbo-0125"  # 
gpt4="gpt-4-0125-preview"  # gpt-4  gpt-4-32k 
gpt4="gpt-4o-2024-11-20"

#gpt-4o-2024-11-20
#gpt-4o-2024-08-06
#gpt-4o-2024-05-13

gpt3_instruct="gpt-3.5-turbo-instruct-0914"  # "gpt-3.5-turbo-instruct" 

temperature=0
seed=1234
max_tokens=2000

# ======= other configuration globals ===

outfile="horn_gptresults.js" # the results will be appended to this file

gpt_model=gpt4 # default

debug=False # set to True to get a printout of data, call and result

helptext="""Usage example: ./askllm.py 4 someprop.js
Use 4 for gpt4, 3 for gpt3, 2 for gpt and instruct for gpt3 instruct version.
Another example: ./askllm.py 4 10 someprop.js
Here 10 (or any number above 4) is the number of rows to be actually processed.
NB! you must have a file secrets.json with the content {"gpt_key": keystring} in the folder."""

# ========= code ===================

def main():
  if len(sys.argv)<2:
    print(helptext)
    return
  gptversion=gpt_model
  pfile=""
  texts=[]  
  nextprompt=False
  max_rows=1000000000
  # parse command line
  problemfile=None
  for el in sys.argv[1:]:   
    if el=="3" or el=="3.5":
      gptversion=gpt3
    elif el=="2":
      gptversion=gpt2  
    elif el=="4":
      gptversion=gpt4  
    elif el=="instruct":
      gptversion=gpt3_instruct
    elif el.strip().isnumeric():
      max_rows=int(el.strip())
    elif len(el)<100 and " " not in el:
      problemfile=el 
  if not problemfile:
     show_error("problemfile not given")                  
  # read problemfile rows line by line, ignoring the first one
  try:
    f=open(problemfile, "r")
  except:
    show_error("could not read problem file "+problemfile)   
  problems=[]
  rowcount=0  
  while True:  
    try:
      row=f.readline().strip()
      rowcount+=1
      if rowcount<2: continue
      if not row: break
      if rowcount-1>max_rows: break
      parsedrow=json.loads(row)
      hornflag=parsedrow[3]
      if hornflag==0: continue
      problems.append(parsedrow)
    except:
      show_error("could not read problem file "+el)  
  f.close()
  #for el in problems:
  #  print(max_rows)
  #  print(el)
  # open output file
  try:
    of=open(outfile, "w")
  except:
    show_error("could not open output file "+outfile)    
  # run problems read, one by one
  count=0
  processed=0
  correct=0
  correctsat=0
  correctunsat=0
  for problem in problems:
    hornflag=problem[3]
    if hornflag==0: continue
    count+=1
    #if count<270: continue
    #if count>285: break
    sysprompt=None
    prompt=makeprompt(problem)
    debug_print("gpt:",gptversion)
    #debug_print("sysprompt:",sysprompt)
    debug_print("prompt:",prompt)
    # actual call
    print(prompt)
    #continue
    result=call_gpt(gptversion,prompt,sysprompt,max_tokens)
    processed+=1
    #print("result:",result)
    parsedres=parse_result(result)
    iscorrect=None
    if parsedres==problem[4]:
      iscorrect=True
      correct+=1      
      if problem[4]: correctsat+=1
      else: correctunsat+=1
    cleanres=result.replace("\n"," ").replace("\r"," ")
    newdata=[parsedres,cleanres]
    outdata=problem+newdata
    of.write(json.dumps(outdata)+"\n")
    if iscorrect: print("Correct answer:")
    else: print("Wrong answer:")
    print(outdata)
  of.close()  
  print("Summmary:")
  print("processed problems:",processed)
  print("correct answers altogether:",correct)
  print("correct answers for satisfiable problems (half):",correctsat)
  print("correct answers for unsatisfiable problems (half):",correctunsat)

def parse_result(txt):
  txt=txt.replace(".","").replace(","," ").replace(":"," ").replace("*","").replace("'","").replace("\n","").replace("\r","")
  txt=txt.strip().lower()
  sp=txt.split(" ")
  if sp[-1] in ["contradiction","contradictory","false","wrong"]:
    return 0
  elif sp[-1] in ["satisfiable","true","satisfied"]:
    return 1
  elif sp[-1] in ["unknown","uncertain"]:
    return 1
  else:
    return 2
  


# ========= prompt creation =======


def makeprompt(problem):
  clauses=problem[5]
  prefix="Your task is to solve a problem in propositional logic.\n"
  prefix+="You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\n"
  prefix+="If the statements form a contradiction, the last word of your answer should be 'contradiction',\n"
  prefix+="otherwise the last word should be either 'satisfiable' or 'unknown'.\n\n"

  details="Propositional variables are represented as 'pN' where N is a number. They are either true or false.\n"
  details+="pN means that pN is true. not(pN) means that pN is false.\n"
  details+="'X or Y' means that X is true or Y is true or both X and Y are true.\n"
  details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\n"
  details+="All the statements are horn clauses: this means that a statement is not allowed to contain more than one positive (without the 'not') variable.\n\n"

  details+="In order to solve a problem, you must use the following method:\n"
  details+="First, print out all the true variables which can be derived directly by some given statement from the given true variable statements in the input\n"
  details+="and which are not already present in the given statements as one-variable statements.\n"
  details+="Then, print out all the true variables which can be similarly derived by some given statement from both the newly printed true variables and\n"
  details+="possibly other true variable statements in the input, and which have not been printed earlier.\n"
  details+="Then continue the same procedure of printing out new directly derivable true variables, until either no new variables can be derived or a direct contradiction\n"
  details+="is found with input and derived variables on one hand and some fully negative given statement on the other hand.\n"
  details+="In case a contradiction is found, finally print 'contradiction'. In case no direct contradiction is found and no new true variables can be derived,\n"
  details+="finally print 'satisfiable'.\n\n"

  details+="Do not print out anything except the derivable true variables, separated by a blank space, and the final answer."

  example="Twelve examples:\n"
  example+="Example 1. Statements: p1. p2. not(p1). Answer: contradiction.\n"
  example+="Example 2. Statements: p1. p2. not(p3). Answer: satisfiable.\n"
  example+="Example 3. Statements: p1. not(p1) or p2. not(p2). Answer: p2 contradiction.\n"
  example+="Example 4. Statements: p1. not(p1) or p3. not(p2) or not(p1). Answer: p3 satisfiable.\n"
  example+="Example 5. Statements: p1. not(p1) or p2. not(p2) or p3. not(p3). Answer: p2 p3 contradiction.\n"
  example+="Example 6. Statements: p1. not(p1) or p2. not(p2) or p1. not(p3). Answer: p2 satisfiable.\n"
  example+="Example 7. Statements: p1. p3. not(p1) or p2. not(p2) or not(p3) or p4. not(p4). Answer: p2 p4 contradiction.\n"
  example+="Example 8. Statements: p1. not(p1) or p2. not(p2) or not(p3) or p3. not(p3). Answer: p2 satisfiable.\n"
  example+="Example 9.  Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p5) or not(p4). not(p1) or not(p6) or p4. Answer: p1 p4 p5 contradiction.\n"
  example+="Example 10. Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p1) or not(p6) or p4. Answer: p1 p4 p5 satisfiable.\n"
  example+="Example 11. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p5.  Answer: p7 p3 p4 p5 contradiction.\n"
  example+="Example 12. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p7.  Answer: p7 p3 p4 satisfiable.\n"

  statements="Statements:\n"
  for clause in clauses:
    statement=""
    for var in clause:
      if var>0: s="p"+str(var)
      else: s="not("+"p"+str(0-var)+")"
      if statement: statement+=" or "+s
      else: statement=s
    statement=statement+".\n"
    statements=statements+statement

  final="\nPlease answer whether the following given statements form a logical contradiction or are satisfiable, using the method described above\n" 
  final+="and not printing out anything except the derivable true variables, separated by a blank space, and the final answer.\n\n" 

  prompt=prefix+details+example+final+statements
  return prompt  



  

  return str(clauses)

# ========= llm connection =========


def call_gpt(gptversion,sentences,sysprompt,max_tokens):
  try:
    sf=open(secrets_file,"r")
    txt=sf.read()
  except:
    show_error("Could not read file containing gpt api key: "+str(secrets_file))
  try:  
    data=json.loads(txt)
  except:
    show_error("Could not parse json text containing gpt api key in: "+str(secrets_file))  
  if "gpt_key" not in data or not (data["gpt_key"]):
    show_error("Could not find gpt api key in: "+str(secrets_file))
  else:    
    key=data["gpt_key"]
  # key found ok    
  #sentences="A fork is a tool you use in the kitchen or when you eat."
  messages=[]
  if sysprompt:
    message1={"role": "system", "content": sysprompt}
    messages.append(message1)   
  message2={"role": "user", "content": sentences}
  messages.append(message2)  

  if gptversion in [gpt3_instruct, gpt2]:
    prompt=""
    if sysprompt: 
      prompt+=sysprompt+"\nInput sentences: "+sentences
    if sentences: 
      prompt+=sentences
    baseurl="/v1/completions"  
    call={
     "model": gptversion,
     "prompt": prompt,
     #"seed": seed,
     #"logprobs": True,
     "temperature": temperature
    }
  else:  
    baseurl="/v1/chat/completions"
    call={
       "model": gptversion,
       "messages": messages,
       "seed": seed,
       #"logprobs": True,
       "logprobs": False,
       "temperature": temperature
    }
  if max_tokens:
    call["max_tokens"]=max_tokens

  debug_print("gpt call",call)
  calltxt=json.dumps(call) 
  debug_print("gpt call:",calltxt)

  host = "api.openai.com"
  
  errcount=0
  while(True):
    conn = http.client.HTTPSConnection(host)
    conn.request("POST", baseurl, calltxt,
                headers={
      "Host": host, "Content-Type": "application/json", "Authorization": "Bearer "+key 
    })
    
    response = conn.getresponse()
    if response.status!=200 or response.reason!="OK":
      errcount+=1            
      #if str(response.status)==502:
      if errcount>2:
        print("gpt repeatedly responded with error")
        try:
          data=json.loads(response.read())    
          if "error" in data and "message" in data["error"]:
            message=": "+data["error"]["message"]
        except:
          message="" 
          show_error("gpt error reason not found: data cannot be parsed")
        show_error("gpt error, finally "+str(response.status)+" "+str(response.reason)+message)
      else:
        print("gpt responded with error, but we retry")
        if conn: conn.close()  
        time.sleep(2)
    else:
      # everything OK
      break      
    
  rawdata = response.read()
  try:
    data=json.loads(rawdata)
  except KeyboardInterrupt:
    raise  
  except:
    show_error("gpt response is not a correct json: "+  str(rawdata))
  if "choices" not in data:
    show_error("gpt response does not contain choices")

  # OK answer received  
  debug_print("gpt response:",data)  
  part=data["choices"]  
  res=""
  for el in part:
    if "message" in el:
      msg=el["message"]
      if "content" in msg:
        tmp=msg["content"]
        if len(tmp)>2 and tmp[0] in ["\"","'"] and tmp[-1] in ["\"","'"]:
          tmp=tmp[1:-1]
        tmp2=tmp.split("\n")
        if len(tmp2)>1:
          tmp3=""
          for line in tmp2:
            if len(line)>3 and (line[0].isnumeric() or line[0] in ["*","-"]) and line[1] in [".",":"," "]:
              tmp3+=line[2:]+" "
            else:
              tmp3+=line+" "  
          tmp=tmp3    
        res+=tmp
    elif "text" in el:
      if res: res+="\n"
      res+=el["text"].strip()      
              
  conn.close()
  #debug_print("res",res)  
  return res


def debug_print(a,b):  
  if debug:
    print(a,b)

def show_error(a):
  print("Error:",a)
  exit(0)  

if __name__ == "__main__":
  main()

# =========== the end ==========
