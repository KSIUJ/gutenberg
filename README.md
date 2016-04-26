# project: gutenberg
simple proxy for hp laserjet 500 printer: print pdf and change color restriction policies via web gui - made for internal use of KSI UJ [http://ksi.ii.uj.edu.pl] 

version 2 - UI + printing options

## features
  - upload PDF and print
  - customize print: enable duplex, number of copies, select some pages to print
  - change color policy (allow color or enforce black-white)
  - sudo printing - enable color, print, disable color
  - live preview LCD

## setup
  - printer: make printing and http web panel available for server network 
  - windows server: configure hp printer
  - windows server: install sumatrapdf - latest version (at least 3.1.1 !)
  - webserver on windows: unpack web/ to public html directory
  - change settings in config.php !!!

## debuging
  - if warning is reported - check log.txt file
  - you can inspect uploaded files in files/ directory
