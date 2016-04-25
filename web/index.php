<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">
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
    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="?action=print">Gutenberg</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
          <ul class="nav navbar-nav">
            <li class="active"><a href="?action=print">Print PDF</a></li>
            <li><a href="?action=color">Change color policy</a></li>
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>

    <div class="container">
      <br />
      <?php if ($_GET['type']=="success"): ?>
        <div class="alert alert-success" role="alert"><strong>Success!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_GET['type']=="error"): ?>
        <div class="alert alert-danger" role="alert"><strong>Error occured!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_GET['type']=="warning"): ?>
        <div class="alert alert-danger " role="alert"><strong>Warning!</strong> <?php echo(htmlspecialchars($_GET['msg'])); ?></div>
      <?php elseif ($_COOKIE["myAlertDismissed"]!="true"): ?>
        <script>
        $( document ).ready(function() {
        $('#myAlert').on('closed.bs.alert', function () {
        document.cookie = "myAlertDismissed=true; expires=Sun, 01 Jan 2017 00:00:00 UTC"; 
    });});</script>
        <div id="myAlert" class="alert alert-info alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>This system has been recently rebuilt!</strong> If you find any bug please add issue at <a href="https://github.com/KSIUJ/gutenberg/issues/new">Github</a>.</div>
      <?php endif; ?>
      <div class="starter-template" style="padding: 0">
        <!--<h1>Gutenberg</h1>-->
      </div>
      <?php if ($_GET['action']=='color'): ?>
        <h2> Admin: change color restriction policies </h2>
    <form action="color.php" method="post" enctype="multipart/form-data">
      Provide target printer admin password: <input type="password" name="passwd"  class="form-control" id="passwd">
      <br />
      <input type="radio" name="enableColor" value="true">Enable color<br />
      <input type="radio" name="enableColor" value="false">Disable color (enforce white-black mode)<br />
      <br />
        <button type="submit" name="submit" class="btn btn-default">Change settings</button>
    </form>
    <?php else: ?>
      <form action="print.php" method="post" enctype="multipart/form-data">
        <h3>1)</h3>
        Select <strong>PDF</strong> file to print:
      <input type="file" class="btn btn-default" name="fileToUpload" id="fileToUpload" /> 
    <h3>2)</h3> 
    Provide ksi WiFi WPA2 key as authorization:<br />
    <input type="text" name="passwd"  class="form-control" id="passwd"><br /> 
    <h3>3)</h3> 
    <input type="checkbox" name="duplex" value="enabled"> Duplex enabled<br />
    <table border=0>
    <tr><td> <label for="pages">Pages to print*&nbsp;</label></td><td><input type="text" class="form-control"  name="pages" id="pages"></td></tr>
    <tr><td> <label for="copies">How many copies&nbsp;</label></td><td><input type="number"  class="form-control" name="copies" id="copies" value=1 size="2"></td></tr>
    </table>
    *) you can type values as in normal printer dialog, eg. 1-7,9,12; empty = all
    <h3>4)</h3>
    <button type="submit" name="submit"  class="btn btn-default">
      <span class='glyphicon glyphicon-print' aria-hidden='true'></span>
      <span class='glyphicon glyphicon-upload' aria-hidden='true'></span>
      Upload and print file
    </button>
    
    <h3>*)</h3> 
    <input type="checkbox" name="sudo" value="enabled"> SUDO printing (enable color, print file, disable color)<br />
    <input type="password" name="passwd_sudo"  class="form-control" id="passwd"><br />
    </form>
    <?php endif; ?>

      <br />
      <hr />
      <center>
        <br />
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/33/Gutenberg.jpg" height="200px"/><br />
        <br />
        &copy; <a href="http://dsinf.net">Daniel Skowroński</a> &amp; <a href="http://ksi.ii.uj.edu.pl">KSI UJ</a>
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