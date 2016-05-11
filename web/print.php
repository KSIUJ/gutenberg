<?php
require_once("config.php");require_once("funcs.php");

function putToLog($text){
	file_put_contents("log.txt", date('Y/m/d H:i:s')." - ".$text."\n", FILE_APPEND | LOCK_EX);
}
function redir($type,$msg){
	header('Location: index.php?action=print&type='.$type.'&msg='.$msg);
}

if ($_POST['passwd']!=$printPassword){
	header('Location: index.php?action=print&type=error&msg=Password does not match. Check on corkboard next to printer.'); die();
}

if ($_POST["sudo"]=='enabled'){
	$PASSWD = $_POST['passwd_sudo'];
	changeColor($PASSWD,'EnableColor');
}

$_POST['pages'] = preg_replace('/[^0-9\-\,]/', '', $_POST['pages']);
$_POST['copies'] = intval($_POST['copies']);
if ($_POST['copies']>10) {
	header('Location: index.php?action=print&type=error&msg=Are you kidding me? Don\'t waste paper! MAX = 10 copies'); die();
}


$_FILES["fileToUpload"]["name"] = preg_replace("/[^A-Za-z0-9\.]/", '-', $_FILES["fileToUpload"]["name"]);
$target_file = $target_dir.basename($_FILES["fileToUpload"]["name"]);
$uploadOk = 1;

if (!move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
	if ($_POST["sudo"]=='enabled'){changeColor($PASSWD,'DisableColor');	}
	redir("error","Cannot upload file. Maybe it\'s too big? Please try again!!!");
	putToLog("failed to move_uploaded_file() - ".$target_file); 	die();
}
if (pathinfo($target_file)["extension"] != "pdf"){
	redir("error","Currently you can print PDFs only. Tip: you can print to PDF on your computer using Bullzip PDF printer and then upload file here."); 
	die();
}

$options = ""; $cnt=0;
if ($_POST['pages']!=""){
	$options.=$_POST['pages'];
	$cnt++;
}
if ($cnt>0) $options.=",";
$options.=$_POST['copies']."x";
$cnt++;

if ($cnt>0) $options.=",";
$options.=($_POST['duplex']=='enabled' ? 'duplex' : 'simplex' );
$cmd = ' "C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe" '.
	'-print-to "'.$printerName.'" '.
	'-print-settings "'.$options.'" '.
	' "'.$target_file.'"'.
	' 2>&1';
$output=shell_exec($cmd);

if ($output==""){
	if ($_POST["sudo"]=='enabled'){changeColor($PASSWD,'DisableColor');	}
	redir("success","Document is printing now. If not - check printer display.");
	putToLog("OK - ".$cmd); die();
}
else if (strpos($output,"font.c:63: not building glyph bbox table")){
	if ($_POST["sudo"]=='enabled'){changeColor($PASSWD,'DisableColor');	}
	redir("success","Document is printing now. There was font warning but don\'t worry.");
	putToLog("OK (font!) - ".$cmd); die();
}
else{
	if ($_POST["sudo"]=='enabled'){changeColor($PASSWD,'DisableColor');	}
	redir("warning","There was some kind of unexpected system behaviour, but document should printing now. If not - contact admin.");
	putToLog("ERROR - ".$_FILES["fileToUpload"]["name"]."\n".$output."\n");  die();
}


?>
