<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="KSI">
    <link rel="icon" href="https://getbootstrap.com/favicon.ico">
    <title>Gutenberg</title>
    <link href="https://getbootstrap.com/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://getbootstrap.com/examples/starter-template/starter-template.css" rel="stylesheet">
    <script src="http://code.jquery.com/jquery-1.11.3.min.js"></script>
    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>

  <body>
    <div class="container">
      <br />
      <?php if ($_GET['type']=="success"): ?>
	<div class="alert alert-success" role="alert"><strong>Success!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_GET['type']=="error"): ?>
	<div class="alert alert-danger" role="alert"><strong>Error occured!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_GET['type']=="warning"): ?>
	<div class="alert alert-danger " role="alert"><strong>Warning!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_COOKIE["myAlertDismissed"]!="true"): ?>
		<div id="myAlert" class="alert alert-info" role="alert"><strong>Something does not work?</strong><br />If you find any <strike>bug</strike> <i>undocummented feature</i> please email us at admin@ksi.ii.uj.edu.pl</div>
		<?php endif; ?>
		<div class="starter-template" style="padding: 0">
		<!--<h1>Gutenberg</h1>-->
		</div>
<script>
function simpleauthform() {
	var usr = document.getElementById("username").value;
	var passwordw = document.getElementById("password").value;
	var sudo =  document.getElementById("sudo").checked;
	document.getElementById("printform").action = "https://" + usr + ":" + passwordw + "@" + document.location.host + (sudo === true ? "/print-color.php" : "/print.php");
	return 1;
}
</script>
		<noscript>
		<h1>ERROR: Your browser does not support JavaScript</h1>
		</noscript>
		<form action="print.php" method="post" enctype="multipart/form-data" id="printform" onsubmit="simpleauthform()">
		<h3>1)</h3>
		Select <strong>PDF</strong> file to print:
		<input type="file" class="btn btn-default" name="fileToUpload" id="fileToUpload" />
		<h3>2)</h3>
		<input type="checkbox" name="duplex" value="enabled" checked> Duplex enabled<br />
		<table border=0>
		<!--<tr><td> <label for="pages">Pages to print*&nbsp;</label></td><td><input type="text" class="form-control"  name="pages" id="pages"></td></tr>-->
		<tr><td> <label for="copies">How many copies&nbsp;</label></td><td><input type="number"  class="form-control" name="copies" id="copies" value=1 size="2"></td></tr>
		</table>
		<h3>3)</h3>
		Enter credentials (WMII or KSI account)
		<table border=0>
		<tr><td> <label for="username">Username&nbsp;</label></td><td><input type="text"  class="form-control" name="username" id="username" size="32"></td></tr>
		<tr><td> <label for="password">Password&nbsp;</label></td><td><input type="password"  class="form-control" name="password" id="password" size="128"></td></tr>
		</table>
		<h3>4)</h3>
		<button type="submit" name="submit"  class="btn btn-default">
		<span class='glyphicon glyphicon-print' aria-hidden='true'></span>
		<span class='glyphicon glyphicon-upload' aria-hidden='true'></span>
		Upload and print file
		</button>

		<h3>*)</h3>
		<input type="checkbox" name="sudo" value="enabled" id="sudo"> SUDO printing (enable color)<br />
		</form>
		<br />
		<br />
		<center>
		<img src="https://upload.wikimedia.org/wikipedia/commons/3/33/Gutenberg.jpg" height="200px"/><br />
		<br />
		&copy; <a href="http://ksi.ii.uj.edu.pl">KSI UJ</a>
		</center>
		</div><!-- /.container -->


		<!-- Bootstrap core JavaScript
		================================================== -->
		<!-- Placed at the end of the document so the pages load faster -->
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
<script src="https://getbootstrap.com/dist/js/bootstrap.min.js"></script>
<!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
<script src="https://getbootstrap.com/assets/js/ie10-viewport-bug-workaround.js"></script>
</body>
</html>
