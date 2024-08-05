// JavaScript Document
var ChartBackgroundColor ='transparent';
function InvalidMsg(textbox) {
	
    if (textbox.value = '') {
        textbox.setCustomValidity('Required email address');
    }
    else if (textbox.validity.typeMismatch){{
        textbox.setCustomValidity('please enter a valid email address');
    }}
    else {
       textbox.setCustomValidity('');
    }
    return true;
}
function validate(evt,num, textbox, regex) {
  var lng = textbox.value.length;
  var theEvent = evt || window.event;
  var key = theEvent.keyCode || theEvent.which;
  key = String.fromCharCode( key );
  if( !regex.test(key) || lng>=num) {
	          
    theEvent.returnValue = false;
    if(theEvent.preventDefault) theEvent.preventDefault();
	
	  }
}




function default_search_date(pdf, pdt)
{
	if(pdf==="" || pdt==="")
	{
		var current_date_obj = new Date();
		date_from = "2000-01-01";
		date_to = current_date_obj.getFullYear()+"-12-31";
	}
	search_text = search_text.replace(' ','');
	
}
 
