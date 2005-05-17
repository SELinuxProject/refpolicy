<?php
  require_once ("./libs.inc.php");
 
  if (!$_GET['page'])
	$page == "index";
  else 
	$page == $_GET['page'];
/* Meh! this is a stupid hack because the stupid template system 
   doesn't like the { } in policy statements */
  $smarty->left_delimiter = '<!--{';
  $body = @$smarty->fetch("$page.html");
  $smarty->left_delimiter = '{';

  if ($body == NULL) 
	$body = @$smarty->fetch("index.html");

  $smarty->assign("body", $body);
  
  $smarty->display ("outer.html");

?> 
