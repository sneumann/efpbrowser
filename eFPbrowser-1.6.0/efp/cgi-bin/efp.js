var MAX = 0;
var MEDIAN = 1;
var COMPARISON = 2;

function disableElement(id) {
    var elem = document.getElementById(id)
    if(elem) {
    	elem.disabled = true;
    }
}

function enableElement(id) {
    var elem = document.getElementById(id)
    if(elem) {
    	elem.disabled = false;
    }
}

function checkboxClicked(form) {
    var checkbox = form.override;
    if (checkbox.checked)
        enableElement("t0");
    else
        disableElement("t0");
}

function changeMode(form) {
    var mode = form.modeInput.selectedIndex;
    switch (mode) {
        case MAX:
            disableElement("g2");
            //disableElement("t0");
	    var input = document.getElementById("t0");
	    input.setAttribute("value", "500");
	    var header = document.getElementById("t1");
	    //header.innerHTML = "Threshold";
            break;
        case MEDIAN:
            disableElement("g2");
            //enableElement("t0");
	    var input = document.getElementById("t0");
	    input.setAttribute("value", "2.0");
	    var header = document.getElementById("t1");
	    //header.innerHTML = "Threshold (log2)";
            break;
        case COMPARISON:
            enableElement("g2");
            //enableElement("t0");
	    var input = document.getElementById("t0");
	    input.setAttribute("value", "2.0");
	    var header = document.getElementById("t1");
	    //header.innerHTML = "Threshold";
            break;            
    }
}	

function checkAGIs(form) {
    var primary = form.primaryGene.value;
	var secondary = form.secondaryGene.value;
	if (primary == ""){
		alert("The Primary AGI Field Cannot Be Empty!");
		return false;
	}else if (primary.match(regId) == null){
		alert("Invalid Primary AGI: Not in Correct Format!");
		return false;
	}else if (form.modeInput.selectedIndex == COMPARISON){
		if(secondary == ""){
			alert("The Secondary AGI Field Cannot Be Empty in Compare Mode!");
			return false;
		}else if (secondary.match(regId) == null) {
			alert("Invalid Secondary AGI: Not in Correct Format!");
			return false;
		}
	}
	return true;
}

function openChart(element)
{
	var layer = document.getElementById(element);
	layer.style.visibility='visible';
}

function closeChart(element)
{
	var layer = document.getElementById(element);
	layer.style.visibility='hidden';
}

function resizeIframe(iframeId, iframe) 
{
	var target = document.getElementById(iframeId);
	target.height = iframe.document.body.offsetHeight + 25 // Firefox
	target.style.height = iframe.document.body.scrollHeight + 25 // Opera and IE
}
