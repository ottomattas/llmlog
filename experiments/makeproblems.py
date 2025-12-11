#!/usr/bin/env python3

# Creating nlp problems
#
# Run the program and it will print out the problems, to be piped to a file.
#
#-----------------------------------------------------------------
# Copyright 2025 Tanel Tammet (tanel.tammet@gmail.com)
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

import sys
import json

import random, math, time

# ======== configuration ======

# probs_for_onecase number of problems will be created 
# for each triple of params below:
# varnr,cllen,hornflag

# the range of variable numbers for which problems are made; 
# problems with fewer variables will be smaller and simpler
varnr_range=[3,4,5,6,7,8,9,10,11,12,13,14,15] # ok varns are between 3 and 15, inclusive

varnr_range=[3,4,5,6,7,8,9,10,11,12,13,14,15]

# the range of max clause lengths of problems, for each variable number
cl_len_range=[3,4] # ok lens are between 2 and 5, inclusive 

# this small list will be iterated over: for True only horn problems are generated,
# for False all kinds of problems are generated, not just horn
horn_flags=[True,False] # should be a list of one or two booleans

# the number of problems created for a fixed triple of varnr, cllen, hornflag
# it has to be an even number!
probs_for_onecase=20 # 100 will contain 50 satisfiable and 50 non-satisfiable, interleaved


# ======== generator ======


def main(): 
  global allcls
  problems=[]
  # maxvars: [general_ratio,horn_ratio]
  goodratios={
    2: [1.9,1.3],
    3: [4.0,2.0],
    4: [[0,0,0,3.2,4.4,5.6,6.4,6.9,6.7,7.6],3.1],
    5: [[0,0,0,3.3,5.5,7.7,9.4,10.8,11.6,12.4,12.9,13.9,14.1],4.6]
  }
  probnr=0
  for varnr in varnr_range:
    for cllen in cl_len_range:
      for hornflag in horn_flags:
        ratios=goodratios[cllen]
        if hornflag: ratios=ratios[1]
        else: ratios=ratios[0]
        #print("ratios",ratios)
        if type(ratios)==list:
          if varnr>=len(ratios): ratio=ratios[-1]
          else: ratio=ratios[varnr] 
        else:
          ratio=ratios       
        # we get a list [truecount,falsecount,true_problems,false_problems]  
        #print("probs_for_onecase,varnr,cllen,ratio,hornflag",probs_for_onecase,varnr,cllen,ratio,hornflag)
        problst=make_balanced_prop_problem_list(probs_for_onecase,varnr,cllen,ratio,hornflag)
        #print("problst",problst)
        # interleave problems from the list, add proof/model and metainfo
        truelist=problst[2]
        falselist=problst[3]
        choosefrom=True       
        while True:
          if not truelist and not falselist: break
          if choosefrom==True:
            if truelist:
              # true problem 
              prob=truelist[0]
              truelist=truelist[1:]  
              res=truth_table_solve(prob) 
              proof=[]
              for el in res[0]:
                proof.append(int(el))              
          else:
            if falselist: 
              # false problem 
              prob=falselist[0]
              falselist=falselist[1:]  
              res=solve_prop_problem(prob)          
              proof=makeproof(res,allcls)                
          # build a problem with proof and metainfo    
          probnr+=1            
          if hornflag: horn=1
          else: horn=0
          if choosefrom: truth=1
          else: truth=0
          horn_solve_res=resolve_res=solve_prop_horn_problem(prob)
          newprob=[probnr,varnr,cllen,horn,truth,prob,proof,horn_solve_res]
          problems.append(newprob)
          choosefrom= not choosefrom
  simpcount=0  
  fline="""["id","maxvarnr","maxlen","mustbehorn","issatisfiable","problem","""
  fline+=""" "proof_of_inconsistency_or_satisfying_valuation","units_derived_by_horn_clauses"]"""
  print(fline)
  for prob in problems:
    print (prob)  

    for cl in prob[5]:   
      fullneg=True
      for v in cl:
        if v>0: 
          fullneg=False
          break
      if fullneg: break  
    for cl in prob[5]:   
      fullpos=True
      for v in cl:
        if v<0: 
          fullpos=False
          break
      if fullpos: break  
    #print(prob[4],len(prob[5][0]),fullneg,"\n")      
    #print(prob[4],fullpos and fullneg,"\n") 
    #if prob[4]==1 and (len(prob[5][0])!=1 or not fullneg):
    if prob[4]==0 and not (fullpos and fullneg):
      #print("****","\n")
      return
    if not (fullpos and fullneg):
    #if not fullneg:
      simpcount+=1
  #print("simpcount",simpcount)    


def testing_main():  
  global allcls
  #test_ratios()
  #return
  #timetest()
  #return

  #tmp=make_balanced_prop_problem_list(5,4,5,4,True)
  #print(tmp)
  #return

  p=[[-2], [2, -2], [2, -1], [-2, 2, -1], [2, 1, -2], [-1, 1, 2], [-2], [2, 1]]
  #p=[[1],[2],[-1,-2,3],[5,-3],[4,-3],[-4],[-5,-1,6]]
  p=[[1],[2],[-1,-2,3],[-1,2],[-1,3],[-1,7],[5,-3],[4,-3],[-4,-6],[-5,-1,6]]
  m=[]
  for el in p:
    el.sort()
    m.append(el)
  m.sort(key=lambda x: (len(x),x))  
  resolve_res=solve_prop_horn_problem(m)
  print(resolve_res)
  return
  for el in allcls:
    print(el,allcls[el])
  proof=makeproof(resolve_res,allcls)  
  for el in proof:
    print (el)
  return

  for i in range(3):
    """
    p=[[-2], [2, -2], [2, -1], [-2, 2, -1], [2, 1, -2], [-1, 1, 2], [-2], [2, 1]]
    resolve_res=solve_prop_problem(p)
    print(resolve_res)

    p=[[-2], [2, -2], [2, -1], [-2, 2, -1], [2, 1, -2], [-1, 1, 2], [-2], [2, 1]]
    resolve_res=solve_prop_problem(p)
    print(resolve_res)
    return
    """
    while False:
      x=make_prop_problem(5,3,4,False)
      horn=False
      for cl in x:
        if not is_horn(cl):
          horn=False
          break
      if horn: break
          

    print(x)
    for cl in x:
      s=""
      for el in cl:
        s+=str(el)+" "
      print(s)  
    #p=[[1],[-1,-2,3,5],[2],[-3],[-5]]
    #p=[[1],[-1,-2,3,5],[2],[-3],[-6]]
    #p=[[1,2],[-1,-2],[1,-2],[-1,2]]
    #p=[[1],[-1]]
    #p=[[-1],[1,-2]]
    table_res=truth_table_solve(x)
    resolve_res=solve_prop_problem(x)
    print(" \ntable gave "+str(table_res)+"\nresolution gave "+str(resolve_res))
    if table_res:
      if table_res[0]:
        if resolve_res:
          print("err:\ntable gave "+str(table_res)+"\nresolution gave "+str(resolve_res))
          break
      else:
        if not resolve_res:
          print("err:\ntable gave "+str(table_res)+"\nresolution gave "+str(resolve_res))
          break
  return
  p=x
  p=[[1, -2], [2, -1], [1, -2, 2], [1, -1, -2], [-1, 2], [-2, 2], [1, 2], [2, 1]]
  r=solve_prop_problem(p)
  print(r)
  return


  varnr=3
  prop=make_prop_problem(varnr)
  print(prop)


# wanted: number of problems we want to get
# varnr: number of vars
# maxlen: max length of a clause
# ratio: multiplied with n gives the number of clauses
# hornflag: if true, only horn are OK

def make_balanced_prop_problem_list(wanted,varnr,maxlen,ratio,hornflag): 
  true_problems=[]
  false_problems=[]
  truecount=0
  falsecount=0
  while True:
    raw_problem=make_prop_problem(varnr,maxlen,ratio,hornflag)
    problem=normalize_problem(raw_problem)
    if not problem: continue
    table_res=truth_table_solve(problem) 
    if not table_res:
      print("error while solving a problem")
      return None
    if table_res[0]:
      # true
      truecount+=1
      if len(true_problems)>len(false_problems): continue
      else:
        true_problems.append(problem)
        #print("true",problem)
    else:
      # false
      falsecount+=1
      if len(false_problems)>len(true_problems): continue
      else:
        false_problems.append(problem)   
        #print("false",problem)
    if len(true_problems)+len(false_problems)>=wanted:
      break
  #print("true problems: ",len(true_problems),"false problems: ",len(false_problems)) 
  #print("total checked true problems: ",truecount,"total checked false problems: ",falsecount) 
  return([truecount,falsecount,true_problems,false_problems])

# varnr: number of vars
# maxlen: max length of a clause
# ratio: multiplied with n gives the number of clauses
# hornflag: if true, only horn are OK

def old_make_prop_problem(varnr,maxlen,ratio,hornflag): 
  if varnr<2: return []

  # see the discussion of the ratio 4 in the classic
  # http://www.aaai.org/Papers/AAAI/1992/AAAI92-071.pdf :
  # 4 is the integer closest to the "hardest" ratio

  nr=int(varnr*ratio) # how many 3-element clauses
  
  res=[]
  for i in range(nr):  
    clause=[]
    poscount=0
    for j in range(maxlen):      
      r1=random.random()
      if r1<0.5: s=0-1
      else:         
        if hornflag and poscount>0: 
          continue
        s=1
        poscount+=1
      r2=random.random()
      v=math.floor((r2*varnr)+1)
      if s*v not in clause:
        clause.append(s*v)
    if is_tautology(clause): continue
    res.append(clause)
  return res

def make_prop_problem(varnr,maxlen,ratio,hornflag): 
  if varnr<2: return []

  # see the discussion of the ratio 4 in the classic
  # http://www.aaai.org/Papers/AAAI/1992/AAAI92-071.pdf :
  # 4 is the integer closest to the "hardest" ratio

  nr=int(varnr*ratio) # how many 3-element clauses
  
  # loop until the clause set contains at least one
  # fully negative and one fully positive clause
  while True:
    res=[]
    count=0
    units={}
    fullneg=False    
    fullpos=False
    # loop until enough clauses have been generated
    while count<nr:
      clause=[]
      poscount=0
      negcount=0
      for j in range(maxlen):      
        r1=random.random()
        if r1<0.5: s=0-1
        else:         
          if hornflag and poscount>0: 
            continue
          s=1
          poscount+=1
        r2=random.random()
        v=math.floor((r2*varnr)+1)
        if s*v not in clause:
          clause.append(s*v)
          if s<0: negcount+=1
      if is_tautology(clause): continue
      if len(clause)==1:
        var=clause[0]
        if 0-var in units: continue
        if var in units: continue
        units[var]=True    
      clause.sort()
      if clause in res: continue  
      if negcount==len(clause): fullneg=True
      if negcount==0: fullpos=True
      res.append(clause)
      count+=1
    if fullneg and fullpos: break  
  return res

def normalize_problem(problem):
  l=[]
  for cl in problem:
    l.append(frozenset(cl))
  pset=set(l)
  lst=list(pset)
  l=[]
  for el in lst:
    l.append(sorted(el))
  s=sorted(l,key=lambda x: (len(x),x))  
  return s 

# ========== a simple resolution solver for prop logic ================

trace_flag=False

usablecls_maxlen=100

# these are again initialized and changed:
lastclid=0
usablecls=[]
usablecls_bylen=[]
allcls={}

# solve_prop_problem returns a proof clause if proof is found,
# else None

def solve_prop_problem(clauses):
  global lastclid,usablecl,usablecls_bylen
  selected_clauses_count=0
  # prepare working arrays
  processed_clauses=[]
  lastclid=0
  usablecls=[]
  allcls={}
  usablecls_bylen=[]
  for i in range(usablecls_maxlen+1):
    usablecls_bylen.append([])
  for cl in clauses:
    varset=set(cl)
    if is_tautology_set(varset): continue
    lastclid+=1         
    newcl=[lastclid,None,varset] 
    add_usable(newcl)
  # main loop runs until no more usable clauses: if this happens, clause set is satisfiable
  result=None # unless made to a proof clause later
  while True: 
    selected=select_usable()    
    if not selected:
      return None    
    if is_tautology_set(selected[2]): continue
    if trace_flag: print_trace(0,"selected "+clause_to_str(selected))
    # check whether the selected clause is subsumed by some processed clause
    found=False
    for oldclause in processed_clauses:
      if naive_subsumed(oldclause,selected):
        found=True
        break
    if found: 
      # do not use this selected clause, just throw away
      if trace_flag: print_trace(1," was subsumed")
      continue    
    selected_clauses_count+=1
    # resolve all processed clauses with the selected clause
    for processed in processed_clauses:       
      if trace_flag: print_trace(2,"processed "+clause_to_str(processed))
      # do all resolution steps for selected and processed
      contra_cl=do_resolution_steps(selected,processed)
      if contra_cl:
        result=contra_cl
        break
    if result:
      break
    processed_clauses.append(selected)
  return result


def make_internal_cl(cl):
  lastclid+=1         
  newcl=[lastclid,None,set(cl)]      
  return newcl

def do_resolution_steps(clx,cly):
  # clause format:
  #[id, history, {element0,...,elementN}]
  global lastclid
  clxels=clx[2]
  clyels=cly[2]
  clxmin=min(clxels)
  clymin=min(clyels)
  if clxmin<0 and clymin>0:   
    cutvar=clxmin 
    cl=clyels
  elif clymin<0 and clxmin>0:
    cutvar=clymin
    cl=clxels
  else:
    return None
  if 0-cutvar in cl:
    newraw=clxels.union(clyels)
    newraw.discard(cutvar)
    newraw.discard(0-cutvar) 
    lastclid+=1         
    newcl=[lastclid,[clx[0],cly[0]],newraw]          
    if trace_flag: print_trace(2,"derived "+clause_to_str(newcl))
    if is_tautology_set(newraw):
      if trace_flag: print_trace(2,"was tautology")
      return None
    add_usable(newcl)
    if not newraw:
      return newcl
  else:
    return None

def add_usable(cl):
  global usablecls,usablecls_bylen
  usablecls.append(cl)
  allcls[cl[0]]=cl
  l=len(cl[2])
  if l>usablecls_maxlen: l=usablecls_maxlen
  usablecls_bylen[l].append(cl)


def select_usable():
  global usablecls_bylen
  for i in range(len(usablecls_bylen)):
    if usablecls_bylen[i]:
      selected=usablecls_bylen[i].pop()
      return selected
  return None

def is_tautology_set(varset):
  for el in varset:
    if el>0 and 0-el in varset:
      return True
  return False

def is_tautology(varlist):  
  for el in varlist:
    if el>0 and 0-el in varlist:
      return True
  return False

def is_horn(varlist):
  count=0
  for el in varlist:
    if el>0: 
      if count>0: return False
      else: count=1
  return True 


def naive_subsumed(general,special):
  if general[2].issubset(special[2]):
    return True
  else:
    return False

def clause_to_str(cl):
  s = ""
  els=cl[2]
  lst=list(els)
  lst.sort()
  for i in range(len(lst)):
    s += str(lst[i]) + " "
  s=str(cl[0])+": "+s
  return s

def print_trace(depth,x):
  s = " " * depth
  print(s+x)

#proofcls={}

def makeproof(resolve_res,allcls):  
  #global proofcls
  #print("resolve_res",resolve_res)
  proofcls={}
  if type(resolve_res)!=list:
    return []  
  # built full proof
  makeproof_aux(resolve_res,allcls,proofcls)
  # make list-form clauses
  lst=[]
  for el in proofcls:       
    lst.append(proofcls[el])
  lst.sort(key=lambda x: x[0])  
  # collect cl numbers and renumber from 1
  nr=0
  nrs={}
  for el in lst: 
    if el[0] not in nrs:
      nr+=1
      nrs[el[0]]=nr
  # rename clause numbers in clauses and histories
  lst2=[]
  for el in lst:    
    newhist=[]
    for hel in el[1]:
      newhist.append(nrs[hel])
    newcl=[nrs[el[0]],newhist,el[2]] 
    lst2.append(newcl)
  return lst2

def makeproof_aux(incl,allcls,proofcls):
  #global proofcls
  if type(incl)!=list: return
  if incl[0] in proofcls: return
  lst=list(incl[2])
  lst.sort()
  if incl[1]: proof=incl[1]
  else: proof=[]
  lstcl=[incl[0],proof,lst]
  proofcls[incl[0]]=lstcl
  if not proof: return
  for el in proof:
    if el not in proofcls:
      cl=allcls[el]      
      makeproof_aux(cl,allcls,proofcls)      


# ============== a linear complexity horn logic solver version of the resolution prover =======


# solve_prop_horn_problem returns a list of derived variables,
# where everything is derived using only horn rules and
# unit variables
# in case the last element of the list is 0, the contradiction was derived

def solve_prop_horn_problem(inclauses): 
  #print("inclauses",inclauses)
  newunits=[] # a list of new units derived during one iteration
  posunits={} # derived units
  hornrules=[] # all horn rules
  derivedunits=[] # this will be resulting list of derived units
  # sort clauses to a unique order
  clauses=inclauses.copy()
  clauses.sort(key=lambda x: (len(x),x))
  # sort clauses into posunits and hornrules,
  # discard non-horn-rules
  for cl in clauses:
    cl.sort()
    if len(cl)==1 and cl[0]>0:
      v=cl[0]     
      if v not in posunits:
        posunits[v]=True
        newunits.append(v)     
    else:
      poscount=0
      for var in cl:
        if var>0:
          poscount+=1
          if poscount>1: break
      if poscount<2:
        hornrules.append(cl)
  # loop over all new variables  
  # print("posunits",posunits)
  # print("hornrules",hornrules)
 
  # initially newunits is the list of input pos units
  while True:    
    # in each turn of this loop we have a set of
    # new vars (newunits) generated during the previous turn
    nextunits=[] # units generated during this turn will be added here
    posvar=None
    # print("newunits",newunits)
    for newunit in newunits:
      # print("newunit",newunit)
      negunit=0-newunit
      for rule in hornrules:
        # print("rule",rule)
        posvar=None # the derived unit or 0 if contradiction
        canuse=False # do we have all the assumptions of the rule
        if negunit in rule:
          canuse=True          
          for var in rule:
            # check if all assumptions of a rule present as units
            if var<0:
              if 0-var not in posunits:
                canuse=False
                break
            else:
              posvar=var # the positive var in the rule
              if var in posunits:
                canuse=False
                break
          if canuse and not posvar:
            # contradiction found
            posvar=0
        # print("canuse",canuse,"posvar",posvar)    
        if not canuse: 
          continue
        if posvar!=None and posvar not in posunits:       
          #print("keeping posvar",posvar)
          posunits[posvar]=True
          nextunits.append(posvar)
          derivedunits.append(posvar)
          if posvar==0:
            break
      if posvar==0:
        break  
    # all newunits have been processed      
    if posvar==0 or not nextunits:
      #print("cp0 posvar nextunits",posvar,nextunits)
      break
    else:
      newunits=nextunits  
  return derivedunits



# ================ a truth table solver for prop logic ===========

def truth_table_solve(clauses):
  #print("len(clauses)",len(clauses))
  maxvar=0
  for cl in clauses:
    for el in cl:
      if abs(el)>maxvar: maxvar=abs(el)
  if maxvar>20:
    print("too many variables for truth table solver: max is 20")
    return None
  res=search(clauses, maxvar, "nodes", False,{})
  #print("res",res)
  return res


trace_flag=False # false if no trace
trace_method="text" # ok values: text, html or console
trace_list=[]  #list of strings 
origvars=[] # original variable names to use in trace, if available and not false
result_model=[] # set by solver to a resulting model: values of vars
  
# statistical counts:
  
truth_value_leaves_count=0; 
truth_value_calc_count=0; 
  

def search(clauses, maxvarnr, algorithm, trace, varnames):
  global truth_check_place, trace_flag, trace_method, origvars
  global truth_value_calc_count, truth_value_leaves_count, trace_list, result_model

  # store algorithm choice, trace and origvars to globals
  truth_check_place = algorithm
  trace_flag = bool(trace)
  trace_method = trace if trace else None
  origvars = varnames if varnames else False

  # zero statistics counters
  truth_value_calc_count = 0
  truth_value_leaves_count = 0
  trace_list = []
  result_model = []

  # find maxvarnr if not given
  if maxvarnr is None:
    maxvarnr = 0
    for c in clauses:
      for j in c:
        nr = abs(j)
        if nr > maxvarnr:
          maxvarnr = nr

  # variable values are 0 if not set, 1 if positive, -1 if negative
  varvals = [0] * (maxvarnr + 1)

  # start search
  res = (satisfiable_by_table_at(clauses, varvals, 1, 1, 1) or
       satisfiable_by_table_at(clauses, varvals, 1, -1, 1))

  txt = f"finished: evaluations count is {truth_value_calc_count}, leaves count is {truth_value_leaves_count}"
  trace_list.append(txt)

  return [result_model, "\r\n".join(trace_list)] if res else [False, "\r\n".join(trace_list)]


def satisfiable_by_table_at(clauses, varvals, varnr, val, depth):
  global truth_value_leaves_count, trace_flag, truth_check_place

  #print("varnr",varnr,"varvals",varvals)
  varvals[varnr] = val
  if varnr == len(varvals) - 1:
    truth_value_leaves_count += 1

  # naive: evaluate only leaves; better: evaluate partial solutions
  if trace_flag:
    print_trace(depth, f"setting var {str(varnr)} to {val}")

  if truth_check_place != "leaves" or varnr == len(varvals) - 1:
    tmp = clauses_truth_value_at(clauses, varvals, depth)  # check the value at a partial assignment
    if tmp == 1:
      store_model(varvals)
      varvals[varnr] = 0
      return True
    if tmp == -1:
      varvals[varnr] = 0
      return False

  if varnr < len(varvals) - 1:
    if (satisfiable_by_table_at(clauses, varvals, varnr + 1, 1, depth + 1) or
        satisfiable_by_table_at(clauses, varvals, varnr + 1, -1, depth + 1)):
      varvals[varnr] = 0
      return True

    varvals[varnr] = 0
    return False
  else:
    # error case: should not happen
    errtxt = "Error in the satisfiable_by_table algorithm"
    print(errtxt)
    return

def clauses_truth_value_at(clauses, varvals, depth):
  global truth_value_calc_count
  truth_value_calc_count += 1
  allclausesfound = True
  
  for clause in clauses:
    clauseval = 0
    allvarsfound = True
    
    for nr in clause:
      polarity = 1
      if nr < 0:
        nr = -nr
        polarity = -1
      vval = varvals[nr]
      if vval == polarity:
        clauseval = 1
        break
      elif vval == 0:
        allvarsfound = False
    
    if clauseval != 1 and allvarsfound:
      if trace_flag:
        print_trace(depth, "value is false")
      return -1
    
    if not allvarsfound:
      allclausesfound = False
  
  if allclausesfound:
      if trace_flag:
        print_trace(depth, "value is true")
      return 1
  
  if trace_flag:
      print_trace(depth, "value is undetermined")
  return 0

def store_model(varvals):
  global result_model
  for i in range(1, len(varvals)):
      if varvals[i] != 0:
        result_model.append(str(i * varvals[i]))



# ================ optional experiments: not used directly for problem creation =====================


def timetest():
  iterable=[1,2,3,4,5,6,7,8,9,10]
  #iterable=[1,2,3,4,5]
  
  start = time.time()
  x=0
  for n in range(1000):
    for i in range(1000):
      if i in iterable: x+=1
  end = time.time()
  print(end - start)  

  iterable=set([1,2,3,4,5,6,7,8,9,10])
  #iterable=set([1,2,3,4,5])
  
  start = time.time()
  x=0
  for n in range(1000):
    for i in range(1000):
      if i in iterable: x+=1
  end = time.time()
  print(end - start)  

# varnr 2, general case
# varnr 3 bestratio 2.1 bestpnegratio 0.01298701298701288
# varnr 4 bestratio 2.2 bestpnegratio 0.027397260273972712
# varnr 5 bestratio 2.1 bestpnegratio 0.0547945205479452
# varnr 6 bestratio 2.0 bestpnegratio 0.16249999999999998
# varnr 7 bestratio 2.1 bestpnegratio 0.1685393258426966
# varnr 8 bestratio 1.9 bestpnegratio 0.08750000000000002
# varnr 9 bestratio 1.8 bestpnegratio 0.05633802816901412
# varnr 10 bestratio 1.8 bestpnegratio 0.05714285714285716
# varnr 11 bestratio 1.9 bestpnegratio 0.1428571428571429
# varnr 12 bestratio 1.8 bestpnegratio 0.08108108108108103
# varnr 13 bestratio 1.9 bestpnegratio 0.09638554216867468
# varnr 14 bestratio 1.8 bestpnegratio 0.2222222222222222
#
# varnr 2, horn case
# varnr 3 bestratio 1.8 bestpnegratio 0.038461538461538436
# varnr 4 bestratio 1.8 bestpnegratio 0.19047619047619047
# varnr 5 bestratio 1.6 bestpnegratio 0.051948051948051965
# varnr 6 bestratio 1.6 bestpnegratio 0.14492753623188404
# varnr 7 bestratio 1.5 bestpnegratio 0.21333333333333337
# varnr 8 bestratio 1.4 bestpnegratio 0.11475409836065564
# varnr 9 bestratio 1.4 bestpnegratio 0.3666666666666667
# varnr 10 bestratio 1.3 bestpnegratio 0.19444444444444442
# varnr 11 bestratio 1.3 bestpnegratio 0.03488372093023251
# varnr 12 bestratio 1.3 bestpnegratio 0.1875
# varnr 13 bestratio 1.2 bestpnegratio 0.17910447761194037
# varnr 14 bestratio 1.2 bestpnegratio 0.17105263157894735

# varnr 3, general case
# varnr 3 bestratio 2.7 bestpnegratio 0.07042253521126751
# varnr 4 bestratio 3.4 bestpnegratio 0.050000000000000044
# varnr 5 bestratio 3.9 bestpnegratio 0.026666666666666616
# varnr 6 bestratio 3.5 bestpnegratio 0.10000000000000009
# varnr 7 bestratio 4.2 bestpnegratio 0.06172839506172845
# varnr 8 bestratio 4.0 bestpnegratio 0.10227272727272729
# varnr 9 bestratio 4.0 bestpnegratio 0.16666666666666663
# varnr 10 bestratio 4.0 bestpnegratio 0.171875
# varnr 11 bestratio 4.0 bestpnegratio 0.11111111111111116
# varnr 12 bestratio 4.3 bestpnegratio 0.05633802816901401
# varnr 13 bestratio 4.0 bestpnegratio 0.0923076923076922

# varnr 3, horn case
# varnr 3 bestratio 2.6 bestpnegratio 0.26190476190476186
# varnr 4 bestratio 2.3 bestpnegratio 0.0547945205479452
# varnr 5 bestratio 2.2 bestpnegratio 0.060975609756097615
# varnr 6 bestratio 2.2 bestpnegratio 0.027397260273972712
# varnr 7 bestratio 2.2 bestpnegratio 0.18888888888888888
# varnr 8 bestratio 2.2 bestpnegratio 0.08974358974358965
# varnr 9 bestratio 2.2 bestpnegratio 0.05555555555555558
# varnr 10 bestratio 1.9 bestpnegratio 0.08219178082191791
# varnr 11 bestratio 2.0 bestpnegratio 0.08333333333333326
# varnr 12 bestratio 2.0 bestpnegratio 0.08333333333333337
# varnr 13 bestratio 2.0 bestpnegratio 0.1686746987951807
# varnr 14 bestratio 2.0 bestpnegratio 0.19318181818181823

# varnr 4, general case

#varnr 3 bestratio 3.2 bestpnegratio 0.07246376811594213
#varnr 4 bestratio 4.4 bestpnegratio 0.03947368421052633
#varnr 5 bestratio 5.6 bestpnegratio 0.10126582278481011
#varnr 6 bestratio 6.4 bestpnegratio 0.024096385542168752
#varnr 7 bestratio 6.9 bestpnegratio 0.012499999999999956
#varnr 8 bestratio 6.7 bestpnegratio 0.0
#varnr 9 bestratio 7.6 bestpnegratio 0.0
#varnr 10 bestratio 7.6 bestpnegratio 0.025974025974025983
#varnr 11 bestratio 7.8 bestpnegratio 0.012658227848101333
#varnr 12 bestratio 7.6 bestpnegratio 0.10294117647058831

# varnr 4, horn case
#varnr 3 bestratio 3.0 bestpnegratio 0.34693877551020413
#varnr 4 bestratio 3.2 bestpnegratio 0.10000000000000009
#varnr 5 bestratio 3.2 bestpnegratio 0.044117647058823595
#varnr 6 bestratio 3.1 bestpnegratio 0.01388888888888884
#varnr 7 bestratio 3.2 bestpnegratio 0.048192771084337394
#varnr 8 bestratio 3.1 bestpnegratio 0.07042253521126762
#varnr 9 bestratio 3.1 bestpnegratio 0.0
#varnr 10 bestratio 3.3 bestpnegratio 0.07692307692307687
#varnr 11 bestratio 3.1 bestpnegratio 0.12345679012345678
#varnr 12 bestratio 3.2 bestpnegratio 0.11827956989247312
#varnr 13 bestratio 3.0 bestpnegratio 0.17647058823529416
#varnr 14 bestratio 3.2 bestpnegratio 0.3763440860215054

# varnr 5, general case
# varnr 3 bestratio 3.3 bestpnegratio 0.15384615384615374
# varnr 4 bestratio 5.5 bestpnegratio 0.16049382716049387
# varnr 5 bestratio 7.7 bestpnegratio 0.014705882352941124
# varnr 6 bestratio 9.4 bestpnegratio 0.14634146341463417
# varnr 7 bestratio 10.8 bestpnegratio 0.026666666666666616
# varnr 8 bestratio 11.6 bestpnegratio 0.10000000000000009
# varnr 9 bestratio 12.4 bestpnegratio 0.014084507042253502
# varnr 10 bestratio 12.9 bestpnegratio 0.01449275362318836
# varnr 11 bestratio 13.9 bestpnegratio 0.05063291139240511
# varnr 12 bestratio 14.1 bestpnegratio 0.024691358024691468

# varnr 5, horn case
# varnr 3 bestratio 3.1 bestpnegratio 0.03797468354430378
# varnr 4 bestratio 4.2 bestpnegratio 0.09090909090909083
# varnr 5 bestratio 4.8 bestpnegratio 0.06153846153846154
# varnr 6 bestratio 4.7 bestpnegratio 0.01449275362318847
# varnr 7 bestratio 4.9 bestpnegratio 0.025000000000000022
# varnr 8 bestratio 4.5 bestpnegratio 0.01449275362318836
# varnr 9 bestratio 4.6 bestpnegratio 0.012820512820512775
# varnr 10 bestratio 4.4 bestpnegratio 0.03947368421052633
# varnr 11 bestratio 4.6 bestpnegratio 0.011494252873563315
# varnr 12 bestratio 4.5 bestpnegratio 0.11267605633802824
# varnr 13 bestratio 4.6 bestpnegratio 0.025316455696202445
# varnr 14 bestratio 4.2 bestpnegratio 0.025316455696202556

# suggested ratios to use:
# maxvars: [general_ratio,horn_ratio]
"""
{
 2: [1.9,1.3],
 3: [4.0,2.0],
 4: [[0,0,0,3.2,4.4,5.6,6.4,6.9,6.7,7.6],3.1],
 5: [[0,0,0,3.3,5.5,7.7,9.4,10.8,11.6,12.4,12.9,13.9,14.1],4.6]
}
"""

def test_ratios():  
  #timetest()
  #return
  for varnr in range(3,15):
    #print("varnr",varnr)
    bestpnegratio=100000000
    bestratio=0
    for xratio in range(30,50):
      ratio=xratio/10
      #print("varnr",varnr,"ratio",ratio)
      wanted=100
      maxlen=3
      hornflag=False
      tmp=make_balanced_prop_problem_list(wanted,varnr,maxlen,ratio,hornflag)
      #print("pos and neg tries:",tmp[0],tmp[1])
      pnegratio=tmp[0]/tmp[1]
      #print("pnegratio",pnegratio,"abs(pnegratio-1)",abs(pnegratio-1))
      if abs(pnegratio-1)<bestpnegratio:
        bestpnegratio=abs(pnegratio-1)
        bestratio=ratio
    print("varnr",varnr,"bestratio",bestratio,"bestpnegratio",bestpnegratio)    
  return


# ========= run the program ======

if __name__ == "__main__":        
  main()  


# ========= the end =============
