# project: gutenberg (linux mutation)
simple proxy for hp laserjet 500 printer: print pdf via web gui - made for internal use of KSI UJ [http://ksi.ii.uj.edu.pl] 

version 2.1 - Quick and dirty port of gutenberg to work on linux
**NOT SUPPORTED**


## features
  - upload PDF and print
  - customize print: enable duplex, number of copies
  - sudo printing - color print

## setup
  - printer: make printing available for server network 
  - linux server: install drivers, configure cups
  - linux server: test lp command
  - setup web server with php (tested with nginx + php-fpm)
  - (optional) configure basic auth for /print.php and /print-color.php

## debuging
  - if warning is reported - check /var/log/gutenberg.log, web server and php log files
  - you can inspect uploaded files in /tmp directory
