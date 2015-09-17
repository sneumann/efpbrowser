<?php
 header("Content-type: image/png");
   $im    = imagecreatefrompng("stats.png");
   imagepng($im);
   imagedestroy($im);
   
   // figure out what page label is
   $page_name=$_GET["page_name"];
   if (strlen($page_name)==0) {
      $page_name = "undefined page";
   }
   ereg("[^/]*//[^/]*/(.*)", $_SERVER['HTTP_REFERER'], $regs);
   $page_url=$regs[1];
//   echo "URL=".$page_url;
   // update bbclone stats as per installation instructions
   define("_BBC_PAGE_NAME", $page_url);
   define("_BBCLONE_DIR", "");
   define("COUNTER", _BBCLONE_DIR."mark_page.php");
   if (is_readable(COUNTER)) include_once(COUNTER);
?> 
