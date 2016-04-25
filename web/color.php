<?php

$PASSWD = $_POST['passwd'];
$COLOR = $_POST['enableColor']=='true' ? 'EnableColor' : 'DisableColor';
require_once("funcs.php");
$result = changeColor($PASSWD,$COLOR);
if ($result){
	header('Location: index.php?action=print&type=success&msg=Color policy successfully changed.'); die();
}
else{
	header('Location: index.php?action=color&type=error&msg=Unknown error - try again or change color policy manually and cotact admin.'); die();
}

?>
