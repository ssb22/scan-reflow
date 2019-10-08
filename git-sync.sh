#!/bin/bash
git pull --no-edit
wget -N http://ssb22.user.srcf.net/notes/areas2pdf.sh
wget -N http://ssb22.user.srcf.net/notes/bitmap.py
wget -N http://ssb22.user.srcf.net/notes/derotate.sh
wget -N http://ssb22.user.srcf.net/notes/edit-reflow.py
wget -N http://ssb22.user.srcf.net/notes/latex-papersize.py
wget -N http://ssb22.user.srcf.net/notes/MbmShow.txt
wget -N http://ssb22.user.srcf.net/notes/reflow.c
wget -N http://ssb22.user.srcf.net/notes/savearea.scm
wget -N http://ssb22.user.srcf.net/notes/tex2mbm-fast.py
wget -N http://ssb22.user.srcf.net/notes/tex2mbm.py
wget -N http://ssb22.user.srcf.net/notes/XBMshow.py
git commit -am update && git push
