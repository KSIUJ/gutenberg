<?php

$target_dir = "/tmp";
$timestamp = microtime(true);

function putToLog($text){
	file_put_contents("/var/log/gutenberg.log", date('Y/m/d H:i:s')." - ".$text."\n", FILE_APPEND | LOCK_EX);
}
function redir($type,$msg){
	global $timestamp;
	header('Location: index.php?action=print&type='.$type.'&msg='.$msg.'&timestamp='.$timestamp);
}

$_POST['copies'] = intval($_POST['copies']);
if ($_POST['copies']>100) {
	header('Location: index.php?action=print&type=error&msg=Are you kidding me? Don\'t waste paper! MAX = 100 copies'); die();
}


$_FILES["fileToUpload"]["name"] = preg_replace("/[^A-Za-z0-9\.]/", '-', $_FILES["fileToUpload"]["name"]);
$target_file = $target_dir."/".$timestamp."__".basename($_FILES["fileToUpload"]["name"]);
$uploadOk = 1;

if (!move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
	redir("error","Cannot upload file. Maybe it's too big? Please try again!!!");
	putToLog("failed to move_uploaded_file() - ".$target_file." - ".$_FILES["fileToUpload"]["tmp_name"]); 	die();
}
if (strtolower(pathinfo($target_file)["extension"]) != "pdf"){
	redir("error","Currently you can print PDFs only. Tip: you can print to PDF on your computer using Bullzip PDF printer and then upload file here."); 
	die();
}

$options="";

$options.=" -o HPColorAsGray=True";

$options.=" -n ".$_POST['copies']." ";

$options.=" -o Duplex=".($_POST['duplex']=='enabled' ? 'DuplexNoTumble' : 'None' );
$cmd = '/usr/bin/lp -d KSI "'.$target_file.'" '.$options;
$output=shell_exec($cmd);

if (preg_match("/request id is KSI/", $output)) {
	redir("success","Document is printing now. If not - check printer display.");
	putToLog("OK - ".$_POST['username'].": ".$cmd."\n"); die();}
else{
	redir("warning","There was some kind of unexpected system behaviour, but document should printing now. If not - contact admin.");
	putToLog("ERROR - ".$_POST['username'].": ".$cmd."\n".$output);  die();
}
?>
