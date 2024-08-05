var op_total_page=0;
var op_per_page=10;
var search_text="";
var query;
var date_from="";
var date_to="";
var pagi_query;
var chk_box_id=[];
var current_page=0;
var pagi_next_limit=true;
var pagi_prev_limit=true;





function next_pagination_data()
{
    if(pagi_next_limit)
    {
        pagination_data(current_page+op_per_page,"pegi_next");
    }
}


function previouse_pagination_button()
{
    if(pagi_prev_limit)
    {
        pagination_data(current_page-op_per_page,"pegi_prev");
    }
}



//===================================================================================
//==================================== Print search Results  ========================
//===================================================================================
function print_record()
{
	//search_text = document.getElementById("search").value;	
	window.location = "print.php?printing_type=normal_print&&query="+query+"&&tittle_name="+page_record_title;
}
//===================================================================================
//============================= excell export result by search ==========================
//===================================================================================
function export_record()
{ 
	//search_text = document.getElementById("search").value;
	//query = "CALL `sp_student_result_download_excell`('"+search_text+"', 0, 100000);";
	window.location = "excell.php?excel_type=write&&tittle_name="+page_record_title+"&&query="+query;

}

function export_record_by_report(convert_table_excel)
{ 
    open_popup("submit-form-popup-pane"); 
    
    date_from = document.getElementById("date_from").value;
    date_to = document.getElementById("date_to").value;
   // alert(convert_table_excel);
    //query = "CALL `sp_student_result_download_excell`('"+search_text+"', 0, 100000);";
    /*var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            close_popup("submit-form-popup-pane");
            //document.write(xmlhttp.responseText);
        }
    };

    xmlhttp.open("GET", "excell.php?excel_type="+convert_table_excel+"&&report_title="+page_record_title+"&&date_from="+date_from+"&&date_to="+date_to, true);

    xmlhttp.send();*/  

    window.location = "excell.php?excel_type="+convert_table_excel+"&&report_title="+page_record_title+"&&date_from="+date_from+"&&date_to="+date_to;
    setTimeout(function() 
    {
        close_popup("submit-form-popup-pane");
    }, 3000);
}

function testing()
{
    alert('workint');
}


// Polling for the sake of my intern tests
    
        








//===================================================================================
//============================== Default Date and time===============================
//===================================================================================
function default_search_date(pdf, pdt)
{
    if(pdf==="" || pdt==="")
    {
        var current_date_obj = new Date();
        date_from = "2000-01-01";
        date_to = current_date_obj.getFullYear()+"-12-31";
    }
    
}
//===================================================================================
//==================================== pagi button ==================================
//===================================================================================
function pagination_data(start_from,type)
{
    current_page = start_from;
    //alert(current_page);
    search_text = document.getElementById("search").value;
    pagi_query = " CALL `"+procedure_name+"`('"+search_text+"','"+date_from+"','"+date_to+"','"+start_from+"','"+op_per_page+"');";
   // alert(pagi_query);
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            document.getElementById("table_rows").innerHTML = xmlhttp.responseText;    
            var no_record = document.getElementById("no-record");
            //alert();
            if(no_record)
            {
                if(type == "pegi_next")
                {
                    pagi_next_limit = false;
                    //alert("next");
                }
                else if(type == "pegi_prev")
                {
                    pagi_prev_limit = false;
                   // alert("prev");
                }
                //alert("workingx");
            }
            else
            {
                pagi_prev_limit = true;
                pagi_next_limit = true;
            }
            
            //document.write(xmlhttp.responseText);
        }
    };

    xmlhttp.open("GET", "functions.php?function_name=grid_view_pagi&&query="+pagi_query, true);

    xmlhttp.send();         
}
//===================================================================================
//==================================== pagi button creator ==================================
//===================================================================================
    function grid_data(search_text) {
        date_from = document.getElementById("date_from").value;
        date_to = document.getElementById("date_to").value;
        search_text = document.getElementById("search").value;
        default_search_date(date_from,date_to);                 
        query = " CALL `"+procedure_name+"`('"+search_text+"','"+date_from+"','"+date_to+"', 0, 10);";
        //document.write(query);
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                var splitResult=xmlhttp.responseText.split("|");
                var html_output = "";               
                var op_total_page = (splitResult.length-1)/op_per_page;
                for(var ab=0; ab < op_per_page; ab++)
                {   
                    if(splitResult[ab] != null)
                    {
                        html_output += splitResult[ab];
                    }
                }
                
                var pag_link="";
                var pg_plus=0;
                pag_link += '<button type="button" class="pagi_btn" onClick="previouse_pagination_button()">previouse</button>';
                for(var ab=1; ab < op_total_page+1; ab++)
                {
                    pag_link += '<button type="button" class="pagi_btn" onClick="pagination_data('+pg_plus+')">'+ab+'</button>';
                    pg_plus+=op_per_page;
                    if(ab>=3)
                    {
                        break;
                    }

                }
                pag_link += '<button type="button" class="pagi_btn" onClick="next_pagination_data()">Next</button>';
                
                if(html_output == "")
                    {
                    html_output ="No Record Enter Correct Text";
                    document.getElementById("table_rows").innerHTML = html_output;
                    }
                else if(html_output != ""){
                    document.getElementById("table_rows").innerHTML = html_output ;
                    document.getElementById("pag_link").innerHTML = pag_link;
                    }
            }
        };
        xmlhttp.open("GET", "functions.php?function_name=grid_view&&query="+query, true);
        xmlhttp.send();
    }
//===================================================================================
//==================================== delete record  ========================
//===================================================================================
function delete_record(id)
{
    alert(id +" "+table_name);
}

function open_popup(id='popup-pane')
{
    document.getElementById(id).className = "popup-pane open";
}

function close_popup(id='popup-pane')
{
    document.getElementById(id).className = "popup-pane";
}
function form_submit_loading_popup()
{
    open_popup("submit-form-popup-pane");
    return false;
}

function select_edit_record_by_id(id)
    {    
            
        //var query = "CALL `"+edit_record_procedure+"`("+id+");";
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function() {
            if (xmlhttp.readyState == 4 && xmlhttp.status == 200) 
            {
               alert(xmlhttp.responseText);
                var result = xmlhttp.responseText.split("|");
                for (var i =0; i< result.length-1; i++) 
                {
                    document.getElementById(field_variables[i]).value = result[i];
                }

               document.getElementById("edit_record_btn").style.display = "block";
               document.getElementById("add-div").className = "add-div open";
               document.getElementById("view-div").className = "view-div"; 
            }
        };
        xmlhttp.open("GET", "functions.php?function_name=select_edit_record_by_id&&id="+id+"&&procedure_name="+edit_record_procedure, true);
        xmlhttp.send();    
    }

function update_fetch_record()
{

    var field_values = new Array(field_variables.length);
    //alert(field_variables.toString());
    for (var i =0; i< field_variables.length; i++) 
    {
        //field_values[i] = document.getElementById(field_variables[i]).value;
        //alert(field_variables[i]);
        field_values[i] = "'"+document.getElementById(field_variables[i]).value+"'";
    }
   
    field_values = field_values.toString();
   // alert(field_values.toString());
    //var query = "CALL sp_select_patient_names("+id+");";
    
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) 
        {
            if(xmlhttp.responseText == "Record updated successfully")
            {
                alert("Successfully<br> Updated");
                window.location = "";
            }
            else
            {
                alert("record not update here is the error<br> as");
            }
            
            //document.getElementById("edit_record_btn").style.display = "none";
        }
    }; 
    xmlhttp.open("GET", "functions.php?function_name=update_fetch_record&&procedure_name="+update_record_procedure+"&&field_values="+field_values, true);
    xmlhttp.send();    
}

function drop_down_fill(drop_down_detail)
{
        //alert(drop_down_detail.length);
    var procedure_name = drop_down_detail[0];
    var fill_field_name = drop_down_detail[1];
    var confition_values = new Array(drop_down_detail.length-2); 

    for (var i =0; i< drop_down_detail.length-2; i++) 
    { 
        confition_values[0] = "'"+drop_down_detail[i+2]+"'"; 
    }
   
    confition_values = confition_values.toString(); 
    
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if(xmlhttp.readyState == 4 && xmlhttp.status == 200) 
        {
            document.getElementById(fill_field_name).innerHTML = xmlhttp.responseText;
           // window.location = "";
            //document.getElementById("edit_record_btn").style.display = "none";
        }
    }; 
    xmlhttp.open("GET", "functions.php?function_name=drop_down_fill&&procedure_name="+procedure_name+"&&confition_values="+confition_values, true);
    xmlhttp.send();    
}

function disable_button(btn_id)
{
    //alert('working');
    document.getElementById(btn_id).disabled = true;
}

function enable_button(btn_id)
{
    //alert('working');
    document.getElementById(btn_id).disabled = false;
}

var current_date_variable="start_date";
var graph_type="";

function get_today_date()
{
    graph_type = "date";
    var yesterday = new Date(Date.now());  
    yesterday = yesterday.toLocaleDateString();
    finalDateGraph(formatDate(yesterday),formatDate(yesterday));
}

function get_yesterday_date()
{
    graph_type = "date";
    var yesterday = new Date(Date.now() - 864e5);  
    yesterday = yesterday.toLocaleDateString();
    finalDateGraph(formatDate(yesterday),formatDate(yesterday));

}

function get_last_week()
{
      graph_type = "date";
      var today = new Date();
      var lastWeeklastday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
      var lastWeekdfirstday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1);
      
      finalDateGraph(formatDate(lastWeekdfirstday),formatDate(lastWeeklastday)); 
}

function get_this_week()
{
    graph_type = "date";
    var curr = new Date; // get current date
    var first = curr.getDate() - curr.getDay(); // First day is the day of the month - the day of the week
    var last = first + 6; // last day is the first day + 6
    var firstday = new Date(curr.setDate(first)).toUTCString();
    var lastday = new Date(curr.setDate(last)).toUTCString();
    finalDateGraph(formatDate(firstday),formatDate(lastday));
}

function get_this_month()
{
    graph_type = "month";
    var date = new Date();
    var firstDayofthemonth = new Date(date.getFullYear(), date.getMonth(), 1);
    var lastDayofthemonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    firstDayofthemonth = formatDate(firstDayofthemonth.toLocaleDateString());
    lastDayofthemonth = formatDate(lastDayofthemonth.toLocaleDateString()); 
    finalDateGraph(firstDayofthemonth,lastDayofthemonth);
}

function get_last_month()
{
    graph_type = "month";
    var now = new Date();
    var prevMonthLastDate = new Date(now.getFullYear(), now.getMonth(), 0);
    var prevMonthFirstDate = new Date(now.getFullYear() - (now.getMonth() > 0 ? 0 : 1), (now.getMonth() - 1 + 12) % 12, 1);
    prevMonthLastDate = formatDate(prevMonthLastDate);
    prevMonthFirstDate = formatDate(prevMonthFirstDate);
    finalDateGraph(prevMonthFirstDate,prevMonthLastDate);
}

function get_this_year()
{
    graph_type = "year";
    var first_day_year = new Date(new Date().getFullYear(), 0, 1);
    var last_day_year = new Date(new Date().getFullYear(), 11, 31);
    first_day_year = formatDate(first_day_year.toLocaleDateString());
    last_day_year = formatDate(last_day_year.toLocaleDateString());
    finalDateGraph(first_day_year,last_day_year);
}

function get_last_year()
{
    graph_type = "year";
    var first_day_year_p = new Date(new Date().getFullYear()-1, 0, 1);
    var last_day_year_p = new Date(new Date().getFullYear()-1, 11, 31); 
    first_day_year_p = formatDate(first_day_year_p.toLocaleDateString());
    last_day_year_p = formatDate(last_day_year_p.toLocaleDateString());
    finalDateGraph(first_day_year_p,last_day_year_p);
}



function get_date_range()
{
   // alert('working');
    graph_type = "date";
    var range_date = document.getElementById("date-range0").value;
    array_date = range_date.split("to");
    finalDateGraph(array_date[0],array_date[1]);
    //alert(array_date[0]); 
    
} 

function finalDateGraph(start_date,end_date)
{ 
    var path = window.location.pathname;
    var page = path.split("/").pop(); 
    var url = page+"?start_date="+start_date+"&&end_date="+end_date+"&&graph_type="+graph_type; 
    window.location = url;  
}

function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}

function on_select_date(date)
{
    alert(date);
    var array_date = split("to",date);
    if(current_date_variable == "start_date")
    { 
        document.getElementById("start_date").click();
        document.getElementById("start_date").value = date;
        current_date_variable = "end_date";
        //alert(date);
    }
    else
    { 
        document.getElementById("start_date").click();
        document.getElementById("end_date").value = date;
        current_date_variable = "start_date";
    }
    
}