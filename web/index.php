<!DOCTYPE html>
<html>
<head>
<title>Project: Gutenberg</title>
</head>
<body>
<h1>Project: Gutenberg</h1><hr />

<form action="print.php" method="post" enctype="multipart/form-data">
    Select <b><u>PDF</u></b> file to print:<br />
    <input type="file" name="fileToUpload" id="fileToUpload">
	
	<br />
	
	Provide ksi-wifi wpa2 key as authorization:<br />
	<input type="text" name="passwd" id="passwd">
	
	<br />
	
    <input type="submit" value="Upload file" name="submit">
</form>
<br />
<hr />
<hr />
<hr />
<h2> Admin: change color restriction policies </h2>
<form action="color.php" method="post" enctype="multipart/form-data">
	Provide this printer admin password:<br />
	<input type="password" name="passwd" id="passwd">
	
	<br />
	
	<input type="radio" name="enableColor" value="true">Enable<br />
	<input type="radio" name="enableColor" value="false">Disable<br />
	
    <input type="submit" value="Submit" name="submit">
</form>

</body>
</html>