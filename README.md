# scan-reflow
Unix scripts for large-print handouts etc, from https://ssb22.user.srcf.net/notes
(also [mirrored on GitLab Pages](https://ssb22.gitlab.io/notes) just in case)

Enlarging material in LaTeX
---------------------------

Simply adding instructions such as `\Large` is not enough, as it doesn’t enlarge everything, and it may be difficult to achieve exactly the desired size.

It’s more effective to change the LaTeX paper size and margin settings to simulate small paper, then magnify this up to the real paper size.  The exact settings can be adjusted to achieve virtually any desired font size, and everything is enlarged to that size.

You can generate the settings using my Python script `latex-papersize.py` (works in both Python 2 and Python 3).  See the `--help` text or the comments at the beginning of the script for how to use it.

latex-papersize is also on CTAN and in the TeX Live distribution, usually packaged in `texlive-extra-utils` or `texlive-latex-extra` by GNU/Linux distributions.  It was previously called `LatexPaper.py` and older versions are Python 2 only.

It is also available as a PyPI module: you can use `pip install latex-papersize` or `pipx run latex-papersize`

Enlarging material using The GIMP
---------------------------------

In some cases you will not have the files that produced the original handout.  If obtaining these is out of the question, and if you do not have the resources to reproduce them, then you may still be able to produce an enlarged handout with the aid of an image manipulation program such as The GIMP.  Here are some scripts to speed up this process.

Another use-case of these is if someone has captured their handwriting using Microsoft OneNote on iPad (or other mobile version) whose PDF export becomes a single continuous page, due to that application’s “infinite canvas” and lack of page size settings—printing these without further processing is likely to lead to an unreadably small column. If processing such files using these scripts, you may need to reduce GIMP’s rendering DPI to 150 or 75 to avoid load errors on excessively tall pages.

For each page, you can select areas that will be printed larger on pages of their own.  If the printout has one column then you will be able to print the top half on one page and the bottom half on another page.  If the printout has two columns then you will normally be able to select four areas (top half of left column, bottom half of left column, top half of right column, bottom half of right column).  More complex layouts may need more complex selections.  When selecting areas, try to put the boundaries in sensible places.  The areas should roughly match the proportions of the paper that you will be printing on (either portrait or landscape) but slight irregularities in their size don’t matter (the script will adjust the scale accordingly).

`savearea.scm` is a GIMP plugin to save the selection quickly (it will go to a temporary file without any further prompting).  Installation instructions are in the comments at the top of the file (you will need to read these).

Once you have done the selecting, run `areas2pdf.sh` to put the selections in order.  It should write the result to a file called handout.pdf in your home directory, and clean up the temporary files.  Requires pdflatex and netpbm (already present on most installations).  Sometimes the handout.pdf file has a blank page at the start; I think this is a pdflatex bug (you can work around it by printing from page 2 onward).

An image reflow utility
-----------------------

The program `reflow.c` takes an arbitrary document (perhaps scanned) and magnifies it, re-flowing the words to fit the paper.  This can be used when very large magnification is needed and the original files are not available.  The program also facilitates highlighting, re-ordering and editing (see below) and it has a function for processing documents with interlinear annotations such as pinyin.  It does not always work, but it works often enough to be useful.

See the comments at the start for details.  For highlighting and other editing, you may also need the Python 2 script `edit-reflow.py`.

If using a scanner, you will need the images in PNG format, one per page, 600dpi greyscale. (Some scanning software says PPI instead of DPI; it’s the same thing.)

If you are working from a typeset PDF, convert it into a series of PNG images like this:

`gs -sDEVICE=pngmono -sOutputFile=myfile%03d.png -r600 -q -dNOPAUSE - < myfile.pdf`

which will create myfile001.png, myfile002.png etc.  (If your PDF is from a greyscale scan, use `pnggray` instead of `pngmono`. You can also add `-dFirstPage=3 -dLastPage=17` or whatever to limit the page range.)

(If gs fails, you might get somewhere by first using the `pdftops` utility that comes with `xpdf`, or by using `acroread -toPostScript`, and then repeating the above on the resulting .ps file.  If acroread reports “Segmentation fault” then it might still have converted all the pages, and if not then try running acroread in graphical mode and print to a `.ps` file.)

If a fast computer will be in use, then it may be best to use the `--html` option which will create an HTML page that can be zoomed dynamically in most modern browsers (changing the browser’s text size will scale and reflow the images).  The HTML can also be edited in SeaMonkey etc, in which case `edit-reflow.py` can still be used to colour the images but don’t follow its instruction to re-run reflow.c afterwards. (However note that Seamonkey has been known to delete the spacing between the images, which you then need to restore by replacing `><img` with `> <img` unless you’re using the `--edit` option which produces different markup.)

If HTML cannot be used, try the `--slides` option to generate a PDF slide show which will at least save printing (the page count can get very high at high scale factors).  `--slides` ensures that all pages are produced at the same orientation, default landscape.  You can display this full-screen in Adobe Reader by pressing Control-L (some older versions require Control-Shift-L), or you can convert the PDF to a device-specific bitmap sequence (see help text for how to set non-standard display dimensions).

PDF can also be produced by generating HTML, editing it in Seamonkey etc, and printing to PDF. If the result is to be displayed on older hardware then there will be less page-turn lag if the PDF is all bitmaps at approxmiately the screen’s resolution; the script `bitmap.py` can help automate this. (The resulting file may have extra blank pages at the start and end, but it should be fast to render and compatible with Acrobat 3.)

Compensating for rotated scans
------------------------------

If you have low vision then you may find it difficult and time-consuming to get a perfectly straight scan of a page.  If you are scanning many pages then it can be quicker to take rotated scans and compensate in software.  The above image reflow utility does compensate for slight rotation but not major rotation.  However, if you install the above GIMP plugin then you can try `derotate.sh`, a shell script to help you quickly correct rotations. It also converts the images to PNG for you if they’re not already in that format, so if your scanning software outputs a batch of TIFF files then you can simply run it on that batch without further ado.  Follow the instructions that it gives on startup.  Note: some slight rotation may still remain, so do not use the reflow utility’s `--norotate` option; that option is to be used only if the source material is not a scan.

Other
-----
* [Large-print notes on EPOC or Symbian](psion.md)

Copyright and Trademarks
------------------------

© Silas S. Brown, licensed under Apache 2.
Acrobat is an Adobe trademark.
Apache is a registered trademark of The Apache Software Foundation, which from February to July 2023 acknowledged the Chiricahua Apache, the Choctaw Apache, the Fort Sill Apache, the Jicarilla Apache, the Mescalero Apache, the Lipan Apache, the Apache Tribe of Oklahoma, the Plains Apache, the San Carlos Apache, the Tonto Apache, the White Mountain Apache, the Yavapai Apache and the Apache Alliance.
PostScript is a registered trademark of Adobe Systems Inc.
Python is a trademark of the Python Software Foundation.
SeaMonkey is a registered trademark of The Mozilla Foundation.
Any other trademarks I mentioned without realising are trademarks of their respective holders.
