<?php
require_once("config.php");
if ($_POST['passwd']!=$printPassword){
	header('Location: index.php?action=print&type=error&msg=Password does not match. Check on corkboard next to printer.'); die();
}

$_POST['pages'] = preg_replace('/[^0-9\-\,]/', '', $_POST['pages']);
$_POST['copies'] = intval($_POST['copies']);
if ($_POST['copies']>10) {
	header('Location: index.php?action=print&type=error&msg=Are you kidding me? Don\'t waste paper!'); die();
}

$options = ""; $cnt=0;
if ($_POST['pages']!=""){
	$options.=$_POST['pages'];
	$cnt++;
}
if ($cnt>0){
	$options.=",";
	$options.=$_POST['copies']."x";
	$cnt++;
}
if ($cnt>0){
	$options.=",";
	$options.=($_POST['duplex']=='enabled' ? 'duplex' : 'simplex' );
	$cnt++;
}

$_FILES["fileToUpload"]["name"] = preg_replace("/[^A-Za-z0-9 \.]/", '-', $_FILES["fileToUpload"]["name"]);
$target_file = $target_dir.basename($_FILES["fileToUpload"]["name"]);
$uploadOk = 1;
if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
	if (pathinfo($target_file)["extension"] != "pdf"){
		header('Location: index.php?action=print&type=error&msg=Currently you can print PDFs only. Tip: you can print to PDF on your computer and then upload file here.'); die();
	}
	else{
		$output=shell_exec(' "C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe" '.
			'-print-to "'.$printerName.'" '.
			'-print-settings "'.$options.'" '.
			' "'.$target_file.'"'.
			'" 2>&1');
		if ($output==""){
			header('Location: index.php?action=print&type=success&msg=Document is printing now.'); die();
		}
		else{
			header('Location: index.php?action=print&type=warning&msg=There was some kind of unexpected system behaviour, but document should printing now. If not - contact admin.');
			file_put_contents("log.txt", date('Y/m/d H:i:s')." - ".$_FILES["fileToUpload"]["name"]."\n".$output."\n\n", FILE_APPEND | LOCK_EX); die();
		}
	}
} else {
	header('Location: index.php?action=print&type=error&msg=Cannot upload file. Maybe it\'s too big?'); die();
}

?>