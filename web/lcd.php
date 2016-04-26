<?php

header("Content-type: image/jpeg");
require_once("config.php");
$loginURL = 'http://'.$printerIP.'/hp/device/SignIn/Index';
$lcd1URL = 'http://'.$printerIP.'/hp/device/ControlPanelSnapshot/Index';
$lcd2URL = 'http://'.$printerIP.'/hp/device/ControlPanelSnapshot/Image';

error_reporting(0);

$process = curl_init($printerIP);
curl_setopt($process, CURLOPT_URL, $loginURL);
curl_setopt($process, CURLOPT_HEADER, 1);
curl_setopt($process, CURLOPT_TIMEOUT, 30);
curl_setopt($process, CURLOPT_POST, 1);
curl_setopt($process, CURLOPT_POSTFIELDS, "agentIdSelect=hp_EmbeddedPin_v1&PinDropDown=AdminItem&PasswordTextBox=".$admin_pwd);
curl_setopt($process, CURLOPT_RETURNTRANSFER, TRUE);
$return = curl_exec($process);
curl_close($process);
preg_match_all('(sessionId=.*?;)', $return, $matches);
$cookies = $matches[0][0];
$cookies=rtrim($cookies,";");

$process = curl_init($printerIP);
curl_setopt($process, CURLOPT_HTTPHEADER, array("Cookie: ".$cookies));
curl_setopt($process, CURLOPT_URL, $lcd1URL);
curl_setopt($process, CURLOPT_HEADER, 1);
curl_setopt($process, CURLOPT_TIMEOUT, 30);
curl_setopt($process, CURLOPT_GET, 1);
curl_setopt($process, CURLOPT_RETURNTRANSFER, TRUE);
$return = curl_exec($process);

$process = curl_init($printerIP);
curl_setopt($process, CURLOPT_HTTPHEADER, array("Cookie: ".$cookies));
curl_setopt($process, CURLOPT_URL, $lcd2URL);
curl_setopt($process, CURLOPT_HEADER, 1);
curl_setopt($process, CURLOPT_TIMEOUT, 30);
curl_setopt($process, CURLOPT_GET, 1);
curl_setopt($process, CURLOPT_RETURNTRANSFER, TRUE);
$return = curl_exec($process);

$header_size = curl_getinfo($process, CURLINFO_HEADER_SIZE);
$header = substr($return, 0, $header_size);
$body = substr($return, $header_size);

echo $body;


curl_close($process);