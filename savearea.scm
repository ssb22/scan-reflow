;; GIMP "save area" function
;; (c) Silas S. Brown 2005-26.  License: Apache 2
;; Version 1.3
;; (I did say "public domain no warranty" but apparently
;; some corporate offices don't trust that.  Apache 2 lets
;; them know I don't have a silly patent up my sleeve that
;; I'd try to enforce, so their policy might accept it more
;; easily if you need to use this at work.)

;; INSTALLATION INSTRUCTIONS
;; -------------------------

;; 1.  If you haven't already run the Gimp, run it.

;; - If you are running Gimp on a shared system on which
;; you have limited quota, you might like to set it up
;; in /tmp using a command like:
;;
;; mkdir -p /tmp/$USER ; XAUTHORITY=$HOME/.Xauthority HOME=/tmp/$USER gimp
;; then in the step below, note your .gimp or .config/GIMP directory
;; will be in /tmp/$USER
;;
;; (or you could set swap-path and temp-path in .gimprc, but you may
;; then need to alter areas2pdf.sh, unless you symlink from .gimp*/tmp,
;; and you may still need to create a private tmp subdirectory each time)

;; 2.  Find your .gimp directory.  On Unix this will be in
;; your home directory, called .config/GIMP/2.10 or similar
;; (for 2.10+), or .gimp or .gimp-1.2 or .gimp-2.8 or
;; similar.  If there's more than one then pick the one that
;; corresponds to the version of The GIMP that you're
;; using.  On Windows it'll probably be in
;; C:\Documents and Settings\your user ID\.gimp-2.2 or
;; similar (in other words it will be in the CygWin home
;; directory) or you can find it by searching all files and
;; folders for .gimp.
;; On a Mac, try Library/Application Support/Gimp

;; 3.  If your GIMP is 3.x, save this file (savearea.scm)
;; into a subdirectory of the "plug-ins" subdirectory of the
;; gimp directory, e.g. call it
;; ~/.config/GIMP/3.2/plug-ins/savearea/savearea.scm
;; and chmod +x this file and add a line at the top saying:
;; #!/usr/bin/env gimp-script-fu-interpreter-3.0

;; For 2.x and 1.x, save this file into the "scripts"
;; subdirectory of the gimp directory.  (Create any of these
;; directories that don't exist.)

;; 4.  Restart GIMP.

;; 5.  Open a new image, right-click on it, go to "File",
;; and there should be an option called "Save area".  It's
;; a good idea to assign a shortcut key to it.  Personally I
;; use the slash key (/).
;;
;; - In Gimp 2.8, from an image window go to Edit / Preferences,
;; Interface / Configure keyboard shortcuts, search for
;; Save Area, and press the key (/) then Close / OK.
;;
;; - In older Gimp 1.x you may need to find the main window
;; (not the image window), and navigate through
;; File / Preferences / Interface / Configure keyboard
;; shortcuts / Plug-ins, find "Save area" somewhere in the
;; long list that appears, and then type the shortcut key.
;;
;; - In some even older Gimp versions, all you have to
;; do is point at this option on the menu itself and then
;; press the shortcut key that you want to assign to it
;; (and it will then appear next to the menu item).

;; 6. While configuring The GIMP, I also recommend choosing
;; the Selection tool (the box) if it's not already chosen,
;; and going to Preferences (via Edit or File as above),
;; Input Devices, "Save Input Device Settings Now".
;; This will cause The GIMP to load with the selection
;; tool by default, which is useful if you do more work
;; with selections than with actual drawing.
;; (Older versions of The GIMP had the selection tool as
;; the default anyway.)

;; 7.  You should now be able to make a selection and then
;; use that shortcut key to save it quickly, then make
;; another selection and so on.  If this doesn't work in
;; your version of The GIMP then try converting the input
;; images into a different format first (you can use netpbm
;; or imagemagick to batch-convert if necessary).

;; END OF INSTALLATION INSTRUCTIONS

;; Where to find history:
;; on GitHub at https://github.com/ssb22/scan-reflow
;; and on GitLab at https://gitlab.com/ssb22/scan-reflow
;; and on BitBucket https://bitbucket.org/ssb22/scan-reflow
;; and at https://gitlab.developers.cam.ac.uk/ssb22/scan-reflow
;; and in China: https://gitee.com/ssb22/scan-reflow

;; ------------------------------------------------------


(define (CAR x) (cond ((vector? x) (CAR (vector-ref x 0)))
                      ((pair? x) (CAR (car x)))
                      (else x)))
(define (gimp-old?) (let ((v (CAR (gimp-version))))
                   ;; v1/2 = old
                   (and (char=? (string-ref v 1) #\.)
                        (or (char=? (string-ref v 0) #\1)
                            (char=? (string-ref v 0) #\2)))))
(define (saveArea img layer)
  (let* ((selection (gimp-selection-bounds img))
    (x1 (cadr selection))
    (y1 (caddr selection))
    (x2 (CAR (cdr (cdr (cdr selection)))))
    (y2 (CAR (cdr (cdr (cdr (cdr selection))))))
    (width (- x2 x1))
    (height (- y2 y1))
    (newType (CAR (if (gimp-old?)
                  (gimp-image-base-type img)))
                  (gimp-image-get-base-type img))
    (myNewType (if (equal? newType 1) 1 0))  ;; "indexed" type (2) is awkward so convert it to RGB (0).  May get a completely-black area anyway, but at least will be able to save as PNG to get the dimensions for derotate.sh.  For other uses I suggest batch-converting first as mentioned in instructions above.
    (newImg (CAR (gimp-image-new width height myNewType)))
    (newLayer (CAR (if (gimp-old?)
                       (gimp-layer-new newImg width height (* myNewType 2) "layer 1" 100 0) ;; NORMAL was defined as 0 up to GIMP 2.8, need to use 0 in 2.10+
                       (gimp-layer-new newImg "layer 1" width height myNewType 100 0)))) ;; 3.x changed these params around
    (_ (if (gimp-old?)
       (gimp-image-add-layer newImg newLayer 0)
       (gimp-image-insert-layer newImg newLayer 0 0)))
    (disp (CAR (gimp-display-new newImg))) ;; MUST do this otherwise gimp may corrupt when save
    (_ (gimp-edit-copy (if (gimp-old?) layer (vector layer))))
    (floatingLayer (CAR (gimp-edit-paste newLayer 0)))
    (_ (gimp-floating-sel-anchor floatingLayer))
    (_ (if (gimp-old?) (plug-in-autocrop 1 newImg newLayer)
           (gimp-image-autocrop newImg newLayer)))
    (file (CAR
           (if (gimp-old?) (gimp-temp-name "-area.png")
               (gimp-temp-file "-area.png"))))
    (_ (if (gimp-old?) (file-png-save 1 newImg newLayer file file 0 9 0 0 0 0 0)
           (file-png-export #:run-mode 1 #:image newImg #:file file #:options 0)))
    (_ (gimp-display-delete disp))
    ) ()))

(if (gimp-old?)
    (script-fu-register "saveArea"
       "<Image>/File/Save area"
       "Saves the selected area to a PNG file"
       "Silas S. Brown" "Silas S. Brown" "2005"
       "" ;; any image type
       SF-IMAGE "Image" 0 SF-DRAWABLE "Layer" 0))
    ;; 3.0 needs to split into menu-register:
    (begin
      (script-fu-register "saveArea"
         "Save area"
         "Saves the selected area to a PNG file"
         "Silas S. Brown" "Silas S. Brown" "2005"
         "" ;; any image type
         SF-IMAGE "Image" 0 SF-DRAWABLE "Layer" 0)
      (script-fu-menu-register "saveArea" "<Image>/File"))
