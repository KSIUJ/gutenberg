<?php
require_once("config.php");
$PASSWD = $_POST['passwd'];
$COLOR = $_POST['enableColor']=='true' ? 'EnableColor' : 'DisableColor';

$loginURL = 'http://'.$printerIP.'/hp/device/SignIn/Index';
$colorURL = 'http://'.$printerIP.'/hp/device/RestrictColor/Save';

error_reporting(0);

$process = curl_init($printerIP);
curl_setopt($process, CURLOPT_URL, $loginURL);
curl_setopt($process, CURLOPT_HEADER, 1);
curl_setopt($process, CURLOPT_TIMEOUT, 30);
curl_setopt($process, CURLOPT_POST, 1);
curl_setopt($process, CURLOPT_POSTFIELDS, "agentIdSelect=hp_EmbeddedPin_v1&PinDropDown=AdminItem&PasswordTextBox=".$PASSWD);
curl_setopt($process, CURLOPT_RETURNTRANSFER, TRUE);
$return = curl_exec($process);
curl_close($process);
preg_match_all('(sessionId=.*?;)', $return, $matches);
$cookies = $matches[0][0];
$cookies=rtrim($cookies,";");

$process = curl_init($printerIP);
curl_setopt($process, CURLOPT_HTTPHEADER, array("Cookie: ".$cookies));
curl_setopt($process, CURLOPT_URL, $colorURL);
curl_setopt($process, CURLOPT_HEADER, 1);
curl_setopt($process, CURLOPT_TIMEOUT, 30);
curl_setopt($process, CURLOPT_POST, 1);
curl_setopt($process, CURLOPT_POSTFIELDS, "ColorAccessControlMode=".$COLOR."&RestrictColorUsingPermissionSets=on&AppDefaultColorAccess=BestColor&SignInMethod__DefaultValue=hp_EmbeddedPin_v1&FormButtonSubmit=Zastosuj");
curl_setopt($process, CURLOPT_RETURNTRANSFER, TRUE);
$return = curl_exec($process);
curl_close($process);

if (strpos($return, "HTTP/1.1 200 OK")!==false){
	header('Location: index.php?action=print&type=success&msg=Color policy successfully changed.'); die();
}
else{
	header('Location: index.php?action=color&type=error&msg=Unknown error - try again or change color policy manually and cotact admin.'); die();
}
?>