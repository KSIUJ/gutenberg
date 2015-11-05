<!DOCTYPE html>
<html>
<head>
<title>Project: Gutenberg</title>
</head>
<body>
<h1>Project: Gutenberg</h1><hr />

<?php
require_once("config.php");
if ($_POST['passwd']!=$printPassword){
	echo "<h2>Wrong password!</h2>";
}
else{
	
	$target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);
	$uploadOk = 1;
	if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
    
		
		if (pathinfo($target_file)["extension"] != "pdf"){
			echo '<h1 style="color: red">Sorry, currently only PDF printing :(</h1><a href="/gutenberg">Main page</a>';
		}
		else{
			echo "The file ". basename( $_FILES["fileToUpload"]["name"]). " has been uploaded.";
			$output=shell_exec(' "C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe" -print-to "'.$printerName.'" "'.$target_file.'" 2>&1');
			if ($output==""){
				echo '<h1 style="color: green">Print OK</h1><script>window.location.replace("ok.php");</script>';
				//unlink($target_file); //store files
			}
			else{
				echo '<h1 style="color: yellow">Printing engine reported something, see log below for details</h1>';
				echo "<pre>".$output."</pre>";
				echo '<a href="/gutenberg">Main page</a>';
			}
		}
		
    } else {
		echo '<h1 style="color: red">Error uploading file</h1><a href="/gutenberg">Main page</a>';
    }
	
}
?>

</body>
</html>
