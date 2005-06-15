<?php
  # the exact path is defined.
  $fixpath = dirname(__FILE__);

  # changes this value according to your uploaded smarty distribution.
  # don't forget to add trailing back slash
  # change 'username' to your username on web hosting account
  define ("SMARTY_DIR", "$fixpath/smarty/");

  require_once (SMARTY_DIR."Smarty.class.php");
  $smarty = new Smarty;
  $smarty->compile_dir = "/home/groups/s/se/serefpolicy/t_c";
  $smarty->template_dir = "$fixpath/html";

  $smarty->assign("border", "0");

/*
  $menu = array (
	array("name" => "Home", "url" => "index.php?page=home"),
	array("name" => "Modules", "url" => "index.php?page=modules"),
	array("name" => "IPC", "url" => "index.php?page=ipc"),
	array("name" => "Tutorial", "url"  => "index.php?page=howto")
  );

  $smarty->assign("menuitems", $menu);
*/


  
  
?> 
