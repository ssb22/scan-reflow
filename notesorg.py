# -*- coding: iso-8859-1 -*-

# notesorg v1.01 - organise some notes - (C) 2006-07 Silas S. Brown.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# If running on desktop systems, it will read
# stdin and write organised version to stdout.

# From within Emacs, you can put the following
# in your init file (without the #s at the start
# of the lines) :

# (defun organise-notes () (interactive) (set-buffer-file-coding-system 'iso-8859-1) (shell-command-on-region (point-min) (point-max) "python $HOME/.xemacs/organise.py" t t) )
# (defun insert-times () (interactive) (insert "×"))
# (global-set-key [(control ?f)] 'insert-times)

# then use Control-F to insert a × (times) character
# and use M-x organise-notes to organise a buffer.

# If running on epoc32 PDAs, it should be used
# in conjunction with Macro5, and the following
# macro should be used (again remove #s from the
# beginning of the lines).  Then invoke this
# macro to organise the contents of C:\Documents\Word.
# (Python2.1 must be installed on the PDA.
# Do not change fonts etc in the middle of the text.)

# Include "System.oxh"
# PROC Macro:
# FgDoc%:("C:\Documents\Word")
# SendKey:("Ct+Fn+Up")
# SendString:("~SOF€÷")
# SendKey:("Ct+Fn+Down")
# SendString:("~EOF€×÷")
# SendKey:("Ct+e") :REM exit
# pause 15
# UseDoc%:("C:\System\Apps\Python\Python.app","C:\System\organise.py",0)
# while not exist("C:\sorted.done")
# pause 20
# endwh
# KillApp%:("C:\System\Apps\Python\Python.app")
# DELETE "C:\sorted.done"
# FgDoc%:("C:\Documents\Word")
# SendKey:("Ct+a"):SendKey:("Del")
# SendKey:("Menu"):SendKey:("Up"):SendKey:("Up"):SendKey:("Right"):SendKey:("Up"):SendKey:("Up"):SendKey:("Enter")
# pause 10
# SendKey:("Down"):SendKey:("Ct+Fn+Left"):SendKey:("Up"):SendKey:("Tab")
# pause 5
# SendString:("sorted.out.txt")
# SendKey:("Enter"):SendKey:("Enter")
# pause 5
# SendKey:("Ct+Fn+Up")
# DELETE "C:\sorted.out.txt"
# ENDP

# Organisation codes
# ------------------

# × at the start of a line precedes a category name, e.g.
# ×town something to do in town
# ×mtg something about a meeting

# ×× categorises this line only

# ×o is a special 'order' category - will be
# interpreted as list of other categories to go
# 1st (space-separated)

# Numeric categories (1, etc) always come first.
# 0 causes all numbers to be incremented
# including the 0 to 1.  Similarly for numbers
# after a name. (cat2 goes after cat, but
# cat1,cat2 goes before cat)

# Where to find history:
# on GitHub at https://github.com/ssb22/bits-and-bobs
# and on GitLab at https://gitlab.com/ssb22/bits-and-bobs
# and on BitBucket https://bitbucket.org/ssb22/bits-and-bobs
# and at https://gitlab.developers.cam.ac.uk/ssb22/bits-and-bobs
# and in China: https://gitee.com/ssb22/bits-and-bobs

import sys
if sys.platform=="epoc32":
    print "Loading and parsing"
    fp=open("c:/Documents/Word")
    Str="".join(fp.readlines()) # don't use .read() - MemError - readlines better
    fp.close()
    Str=Str[Str.find('×',Str.find("~SOF€÷")):Str.find('~EOF€×÷')].replace('\x10',' ').split('\x06')
    print "Organising"
else:
    Str=sys.stdin.read()
    Str=Str[Str.find('×'):].split('\n')

projList = [] ; projDict = {}
for i in Str:
    if not i: continue
    old_prjName = None
    if i[0]=="×":
        if len(i)==1: continue
        j=i.split(" ",1)
        if len(j)>1: dat=j[1]
        else: dat=""
        if i[1]=="×":
            # Double x, so switch for 1 line only
            old_prjName = prjName ; prjName = j[0][2:]
        else: prjName = j[0][1:]
        if not projDict.has_key(prjName):
            projDict[prjName] = []
            projList.append(prjName) # keep order
    else: dat = i
    projDict[prjName].append(dat)
    if old_prjName: prjName = old_prjName

if sys.platform=="epoc32": print "Reordering categories"

def getNameNum(p):
    for i in range(len(p)-1,-1,-1):
        if not (p[i] in "0123456789"):
            i += 1 ; return p[:i],int(p[i:])
    return "",int(p)

# Deal with any special 'order' category:
if projDict.has_key("o"):
    wList = " ".join(projDict["o"]).split()
    for i in range(len(wList)):
        if not projDict.has_key(wList[i]):
            del wList[i:] ; break
    wList.reverse() # right order for insertion at top
    for w in wList:
        projList.remove(w)
        projList.insert(0,w)
    projList.remove("o") ; projList.insert(0,"o")

# Renumber 0s to 1s (and 1s to 2s etc if necessary) :
zerosToRenumber = {}
for p in projList:
    if p=="0" or (p[-1] == "0" and p[-2] not in "0123456789"): zerosToRenumber[p[:-1]] = 1
if zerosToRenumber:
    projList2 = projList[:] ; projList2.sort() ; projList2.reverse() # encounter higher numbers 1st, for renaming
    for p in projList2:
        if p[-1] in "0123456789":
            name, num = getNameNum(p)
            if zerosToRenumber.has_key(name):
                newP = name+str(num+1)
                projList.insert(projList.index(p),newP)
                projList.remove(p)
                projDict[newP] = projDict[p]
                del projDict[p]

# Put the numbered items where they should go :
projList2 = projList[:] ; projList2.sort() # so encounter earlier numbers first
for p in projList2:
    if p[-1] in "0123456789":
        name, num = getNameNum(p)
        if num == 1:
            if projDict.has_key(name):
                projList.remove(p)
                projList.insert(projList.index(name),p)
            elif not name:
                projList.remove(p)
                projList.insert(0,p)
            # else leave it alone
        elif num > 1:
            prevP = name+str(num-1)
            if projDict.has_key(prevP):
                projList.remove(p)
                projList.insert(projList.index(prevP)+1,p)
            elif projDict.has_key(name):
                projList.remove(p)
                projList.insert(projList.index(name)+1,p)
            # else leave it alone

# summary - rm some duplicates
projList3=[] ; lastN=None
for p in projList:
    if p[-1] in "0123456789": name=getNameNum(p)[0]
    else: name=p
    if not name: projList3.append(p)
    elif not name==lastN: projList3.append(name)
    lastN=name

if sys.platform=="epoc32":
    print "Outputting"
    fp=open("c:/sorted.out.txt",'w')
else: fp=sys.stdout
fp.write("labels: ") ; fp.write(", ".join(projList3))
fp.write("\n")
for p in projList:
    fp.write("×"+p+" ")
    for i in projDict[p]: fp.write(i+"\n")
    fp.write("\n")
fp.close()
if sys.platform=="epoc32": open("C:/sorted.done",'w').close()
