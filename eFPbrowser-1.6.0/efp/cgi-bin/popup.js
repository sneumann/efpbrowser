var dropdowncompleted = 0;
function popupLeftPosition(popup_width)
{
	var myWidth=0,outputWidth;
	if(typeof(window.innerWidth)=='number')
	{
		myWidth=window.innerWidth;
	}else if(document.documentElement && (document.documentElement.clientWidth)) {
		myWidth=document.documentElement.clientWidth;
	}else if(document.body && (document.body.clientWidth)){
		myWidth=document.body.clientWidth;
	}
	outputWidth=(myWidth/2)-(popup_width/2);
	outputWidth=outputWidth;
	return outputWidth;
}

function popupTopPosition(target){
	var targetHeight = target.offsetHeight
	var outputHeight,myHeight=0;
	var scrollY = getScrollHeight()
	myHeight = getWindowHeight();
	outputHeight=((myHeight-targetHeight)/2);
	if (outputHeight < 0)
		outputHeight = 0;
	return outputHeight+scrollY;
}

function getWindowHeight()
{
	var myHeight=0;
	if(typeof(window.innerHeight)=='number') {
		myHeight=window.innerHeight;
	} else if(document.documentElement && (document.documentElement.clientHeight)) {
		myHeight=document.documentElement.clientHeight;
	} else if(document.body && (document.body.clientHeight)) {
		myHeight=document.body.clientHeight;
	}
	return parseInt(myHeight);
}

function getScrollHeight()
{
	var h = window.pageYOffset ||
			document.body.scrollTop ||
			document.documentElement.scrollTop;
	return h ? h : 0;
}

function getPageHeight(){
	var pagescroll,winHeight;
	if (window.innerHeight && window.scrollMaxY) {
		pagescroll=window.innerHeight+window.scrollMaxY;
	} else if(document.body.scrollHeight>document.body.offsetHeight) {
		pagescroll=document.body.scrollHeight;
	} else {
		pagescroll=document.body.offsetHeight;
	}
	
	windowHeight = getWindowHeight();
	if(pagescroll<winHeight) {
		pageHeight=winHeight;
	} else {
		pageHeight=pagescroll;
	}
	return pageHeight;
}

function DropDownEffect(target,destinationTop,maxSpeed) {
	var currentTop=parseInt(target.style.top);
	if(isNaN(currentTop))
		currentTop=-(target.clientHeight) + getScrollHeight();
	var dropSpeed=1+Math.abs(destinationTop-currentTop)/10;
	if(dropSpeed>maxSpeed)
		dropSpeed=maxSpeed;
	if(currentTop<destinationTop) {
		currentTop+=dropSpeed;
		if(currentTop>destinationTop)
			currentTop=destinationTop;
	} else {
		currentTop-=dropSpeed;
		if(currentTop<destinationTop)
			currentTop=destinationTop;
	}
	target.style.top=parseInt(currentTop)+"px";
	if (currentTop==destinationTop) {
		dropdowncompleted=1;
	}
	else 
		setTimeout('DropDownEffect(document.getElementById("'+target.id+'"),'+destinationTop+', '+maxSpeed+')',30);
}

function fadeIn(target) {
	if(target.fade==null)
		target.fade = 0;
	if(target.fade <= 100) {
		if(target.style.MozOpacity!=null) {
			target.style.MozOpacity=(target.fade/100)-.001;
		} else if(target.style.opacity!=null) {
			target.style.opacity=(target.fade/100)-.001;
		} else if(target.style.filter!=null) {
			target.style.filter="alpha(opacity="+target.fade+")";
		}
		target.style.visibility="visible";
		target.fade+= 10;
		if(target.fade>100) {
			dropdowncompleted=1;
		}
		else
			setTimeout('fadeIn(document.getElementById("'+target.id+'"))',20);
	}
}

function lightbox(target){
	if(target.style.MozOpacity!=null){
		target.style.MozOpacity=0.7;
	}else if(target.style.opacity!=null){
		target.style.opacity=0.7;
	}else if(target.style.filter!=null){
		target.style.filter="alpha(opacity=70)";
	}
	target.style.visibility="visible";
}

function loadPopup(popupId, popup_content,popup_bgcolor,popup_width){
	if (popupId == null)
		popupId="popup_message";
	var popupStyleLeft;

	var popupStyleBorder="solid medium #000000";
	var popupStyleVisibility = "hidden";
	var pageheight = getPageHeight();
	document.write('<div id="lightbox_div" style="width:100%;height:'+pageheight+'px;'+
					'background-color:#000000;z-index:50;position:absolute;left:0px;top:0px;visibility:hidden"></div>');
	document.write('<div id="'+popupId+'" class="popup" style="width:'+popup_width+'px;'+
					'background-color:'+popup_bgcolor+';visibility:'+popupStyleVisibility+'">'+html_entity_decode(popup_content)+'</div>');
}

function addListener(element, type, expression, bubbling)
{
	bubbling = bubbling || false;
	if(window.addEventListener) { // Standard
		element.addEventListener(type, expression, bubbling);
		return true;
	} else if(window.attachEvent) { // IE
		element.attachEvent('on' + type, expression);
		return true;
	} else return false;
}

function recalc(target)
{
	target.style.top = popupTopPosition(target)+"px";
}

function popup(popupId, effect, popup_top, delay){
	if (popupId == null)
		popupId="popup_message";
	var popupElem = document.getElementById(popupId);
	popupElem.style.height = parseInt(getWindowHeight()*0.8)+"px";
	var popupStyleTop=popupTopPosition(popupElem);
	if(popup_top!="center"){
		popupStyleTop=popup_top;
	}
// register onScroll event listener to keep popup always in view
	addListener(window, "scroll", function() {recalc(popupElem);}, false);

	if(effect=="popup"){
		popupElem.style.top=popupStyleTop+"px";
		if(delay>0){
			setTimeout("document.getElementById('"+popupId+"').style.visibility = 'visible'",delay);
		} else {
			document.getElementById(popupId).style.visibility = "visible";
		}
	} else if(effect == "dropdown"){
		popupElem.style.visibility="visible";
		if(delay>0){
			setTimeout("DropDownEffect(document.getElementById(\""+popupId+"\"),popupStyleTop,50)",delay);
		} else {
			DropDownEffect(popupElem,popupStyleTop,10);
		}
	} else if(effect=="fadein"){
		popupElem.fade = 0
		popupElem.style.top=popupStyleTop+"px";
		if(delay>0){
			setTimeout("fadeIn(document.getElementById(\""+popupId+"\"))",delay);
		}else{
			fadeIn(popupElem);
		}
	}else if(effect=="lightbox"){
		popupElem.style.top=popupStyleTop+"px";
		if(delay>0){
			setTimeout("lightbox(document.getElementById('lightbox_div'))",delay);
			setTimeout("document.getElementById('"+popupId+"').style.visibility=\"visible\"",delay);
		}else{
			lightbox(document.getElementById('lightbox_div'));
			popupElem.style.visibility="visible";
		}
	}
}

function popdown (popupId) {
	if (popupId == null)
		popupId="popup_message";
	document.getElementById(popupId).style.visibility='hidden';
	document.getElementById('lightbox_div').style.visibility='hidden';
	document.getElementById(popupId).style.top = "";
	document.body.onscroll = null;
}

function switchPopup(source, target){
	popdown(source);
	popup(target, "popup", "center", 0);
}

function zoomElement(targetId, change)
{
	target = document.getElementById(targetId);
	if(target.originalWidth == null || target.originalHeight == null)
	{
		target.originalWidth = target.clientWidth;
		target.originalHeight = target.clientHeight;
	}
	if(change > 0)
	{
		target.style.height = parseInt(target.clientHeight * (1.0 +change))+"px";
		target.style.width = parseInt(target.clientWidth * (1.0 +change))+"px";
	} else if(change < 0)
	{
		change = Math.abs(change);
		target.style.height = parseInt(target.clientHeight / (1.0 +change))+"px";
		target.style.width = parseInt(target.clientWidth / (1.0 +change))+"px";
	} else
	{
		target.style.height = target.originalHeight+"px";
		target.style.width = target.originalWidth+"px";
	}
}


function html_entity_decode(string,quote_style){
	var hash_map={}, symbol='', tmp_str='', entity='';
	tmp_str=string.toString();
	if(false===(hash_map=this.get_html_translation_table('HTML_ENTITIES',quote_style))){
		return false;
	}
	delete(hash_map['&']);
	hash_map['&']='&amp;';
	for(symbol in hash_map){
		entity=hash_map[symbol];
		tmp_str=tmp_str.split(entity).join(symbol);
	}
	tmp_str=tmp_str.split('&#039;').join("'");
	return tmp_str;
}

function get_html_translation_table(table,quote_style){
	var entities={},hash_map={},decimal=0,symbol='';
	var constMappingTable={},constMappingQuoteStyle={};
	var useTable={},useQuoteStyle={};
	constMappingTable[0]='HTML_SPECIALCHARS';
	constMappingTable[1]='HTML_ENTITIES';
	constMappingQuoteStyle[0]='ENT_NOQUOTES';
	constMappingQuoteStyle[2]='ENT_COMPAT';
	constMappingQuoteStyle[3]='ENT_QUOTES';
	useTable=!isNaN(table)?constMappingTable[table]:table?table.toUpperCase():'HTML_SPECIALCHARS';
	useQuoteStyle=!isNaN(quote_style)?constMappingQuoteStyle[quote_style]:quote_style?quote_style.toUpperCase():'ENT_COMPAT';
	if(useTable!=='HTML_SPECIALCHARS' && useTable!=='HTML_ENTITIES'){
		throw new Error("Table: "+useTable+' not supported');
	}
	entities['38']='&amp;';
	if (useTable==='HTML_ENTITIES'){
		entities['160']='&nbsp;	';
		entities['161']='&iexcl;';
		entities['162']='&cent;';
		entities['163']='&pound;';
		entities['164']='&curren;';
		entities['165']='&yen;';
		entities['166']='&brvbar;';
		entities['167']='&sect;';
		entities['168']='&uml;';
		entities['169']='&copy;';
		entities['170']='&ordf;';
		entities['171']='&laquo;';
		entities['172']='&not;';
		entities['173']='&shy;';
		entities['174']='&reg;';
		entities['175']='&macr;';
		entities['176']='&deg;';
		entities['177']='&plusmn;';
		entities['178']='&sup2;';
		entities['179']='&sup3;';
		entities['180']='&acute;';
		entities['181']='&micro;';
		entities['182']='&para;';
		entities['183']='&middot;';
		entities['184']='&cedil;';
		entities['185']='&sup1;';
		entities['186']='&ordm;';
		entities['187']='&raquo;';
		entities['188']='&frac14;';
		entities['189']='&frac12;';
		entities['190']='&frac34;';
		entities['191']='&iquest;';
		entities['192']='&Agrave;';
		entities['193']='&Aacute;';
		entities['194']='&Acirc;';
		entities['195']='&Atilde;';
		entities['196']='&Auml;';
		entities['197']='&Aring;';
		entities['198']='&AElig;';
		entities['199']='&Ccedil;';
		entities['200']='&Egrave;';
		entities['201']='&Eacute;';
		entities['202']='&Ecirc;';
		entities['203']='&Euml;';
		entities['204']='&Igrave;';
		entities['205']='&Iacute;';
		entities['206']='&Icirc;';
		entities['207']='&Iuml;';
		entities['208']='&ETH;';
		entities['209']='&Ntilde;';
		entities['210']='&Ograve;';
		entities['211']='&Oacute;';
		entities['212']='&Ocirc;';
		entities['213']='&Otilde;';
		entities['214']='&Ouml;';
		entities['215']='&times;';
		entities['216']='&Oslash;';
		entities['217']='&Ugrave;';
		entities['218']='&Uacute;';
		entities['219']='&Ucirc;';
		entities['220']='&Uuml;';
		entities['221']='&Yacute;';
		entities['222']='&THORN;';
		entities['223']='&szlig;';
		entities['224']='&agrave;';
		entities['225']='&aacute;';
		entities['226']='&acirc;';
		entities['227']='&atilde;';
		entities['228']='&auml;';
		entities['229']='&aring;';
		entities['230']='&aelig;';
		entities['231']='&ccedil;';
		entities['232']='&egrave;';
		entities['233']='&eacute;';
		entities['234']='&ecirc;';
		entities['235']='&euml;';
		entities['236']='&igrave;';
		entities['237']='&iacute;';
		entities['238']='&icirc;';
		entities['239'] = '&iuml;';
		entities['240']='&eth;';
		entities['241']='&ntilde;';
		entities['242']='&ograve;';
		entities['243']='&oacute;';
		entities['244']='&ocirc;';
		entities['245']='&otilde;';
		entities['246']='&ouml;';
		entities['247']='&divide;';
		entities['248']='&oslash;';
		entities['249']='&ugrave;';
		entities['250']='&uacute;';
		entities['251']='&ucirc;';
		entities['252']='&uuml;';
		entities['253']='&yacute;';
		entities['254']='&thorn;';
		entities['255']='&yuml;';
	}
	if(useQuoteStyle!=='ENT_NOQUOTES'){
		entities['34']='&quot;';
	}
	if(useQuoteStyle==='ENT_QUOTES'){
		entities['39']='&#39;';
	}
	entities['60']='&lt;';
	entities['62']='&gt;';
	for(decimal in entities){
		symbol=String.fromCharCode(decimal);
		hash_map[symbol]=entities[decimal];
	}
	return hash_map;
}