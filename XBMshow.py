# Program to show sequence of compressed XBM files
# (c) Silas S. Brown 2009.

# Just run it to see the first document,
# or call the main() function with a document number.

# Tested on Windows Mobile with Python CE 2.5 and TkInter.
# (We need to use XBM format because others don't always work.)

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Where to find history:
# on GitHub at https://github.com/ssb22/scan-reflow
# and on GitLab at https://gitlab.com/ssb22/scan-reflow
# and on BitBucket https://bitbucket.org/ssb22/scan-reflow
# and at https://gitlab.developers.cam.ac.uk/ssb22/scan-reflow

def lsbMsb(dat):
  tot=0 ; mul=0
  for d in dat:
    tot |= (ord(d)<<mul)
    mul += 8
  return tot
def readDoc(docNo,contentsFile,dataFile=None):
  contentsFile.seek(docNo*4)
  r1=lsbMsb(contentsFile.read(4))
  if not dataFile: return r1 # just the position
  try: r2=lsbMsb(contentsFile.read(4))
  except EOFError: r2=-1 # read from r1 to EOF
  dataFile.seek(r1)
  return dataFile.read(r2-r1)
imageDat=open("images.dat","rb")
sequenceDat=open("sequence.dat","rb")
contentsDat=open("contents.dat","rb")
numDocs = len(contentsDat.read())/4

from Tkinter import *
import zlib,thread

def addViewer(master, docNo, toForget=[], extraText=""):
  scrollbar = Scrollbar(master)
  text = Text(master, yscrollcommand=scrollbar.set)
  scrollbar.config(command=text.yview)
  for i in toForget: i.pack_forget()
  scrollbar.pack(side=LEFT,fill=Y,expand=1)
  text.pack(side=LEFT,fill=BOTH,expand=1)
  text.theImages = [] # must keep references
  if extraText: text.insert(END,extraText)
  if docNo:
    text.tag_config("p",foreground="blue",underline=1)
    text.tag_bind("p","<Button-1>", lambda *args:master.selectDocument(docNo-1))
    text.insert(END, "Previous", "p")
    text.insert(END,"   ")
  text.tag_config("n",foreground="blue",underline=1)
  text.tag_config("m",foreground="blue",underline=1)
  text.tag_bind("n","<Button-1>", lambda *args:master.selectDocument(docNo+1))
  thread.start_new_thread(queue_additions,(master,docNo,text))
  return [text,scrollbar]

def queue_additions(master,docNo,text):
  doc = readDoc(docNo,contentsDat,sequenceDat)
  for i in range(0,len(doc),2):
    imgdata = BitmapImage(data=zlib.decompress( readDoc(lsbMsb(doc[i:i+2]),imageDat,imageDat)))
    text.theImages.append(imgdata) # keep reference
    master.todo.append( lambda i=i,imgdata=imgdata,*args:(
        text.image_create(END,image=imgdata),
        text.insert(END,"   ")))
  if docNo<numDocs: master.todo.append(lambda *args:text.insert(END, "Next", "n"))
  master.todo.append(None)

class MyApp(Frame):
    def __init__(self,master=None):
        Frame.__init__(self, master) ; self.pack()
        self.todo = [] ; self.toForget = []
    def poll(self): # only one GUI-accessing thread.  Careful not to do too many things at once - responsiveness problems.  (Mouse clicks can be MISSED when processing things on WinCE.)
        repoll=1
        if self.todo:
            if self.todo[0]: self.todo[0]()
            elif len(self.todo)==1: repoll=0
            self.todo=self.todo[1:]
        if repoll: self.after(100,self.poll)
    def selectDocument(self,docNo,extraText=""):
      self.after(100,self.poll)
      self.toForget=addViewer(self,docNo,self.toForget,extraText)

def main(startDocNo=0,extraText=""):
  master = MyApp()
  try: master.winfo_toplevel().wm_state("zoomed")
  except: pass
  master.selectDocument(startDocNo,extraText)
  mainloop()
if __name__=="__main__": main()
