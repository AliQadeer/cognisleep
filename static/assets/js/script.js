// $(document).off('.datepicker.data-api');

$(document).ready(function () {
    jQuery(document).ready(function(){
        jQuery('#add-btn').click(function(){
            jQuery('.add-div').addClass("open");
            jQuery( '.view-div').removeClass("open");
        });
    });
    jQuery(document).ready(function(){
        jQuery('#view-btn').click(function(){
            jQuery('.add-div').removeClass("open");
            jQuery( '.view-div').addClass("open");
        });
    });
    $('#contact_no').trigger("change");
$('#card_number').on('keypress change blur', function () {
  $(this).val(function (index, value) {
    return value.replace(/[^0-9]+/gi, '').replace(/(.{4})/g, '$1 ');
  });
});

$('#card_number').on('copy cut paste', function () {
  setTimeout(function () {
    $('#card_number').trigger("change");
  });
});


 if(!window.matchMedia("(max-width: 700px)").matches){
         $('header').css('height', $('header').outerHeight());
         $(window).scroll(function () {
             if ($(document).scrollTop() > $('header').outerHeight()) {
                 $('body').addClass('navfixed');
//                  var attrib='data-fixed';
             } else {
                 $('body').removeClass('navfixed');
//                  var attrib='data-original';
             }
//                 $('.logo img').attr('src',$('.logo img').attr(attrib))
         });

         window.scrollTo(0, $(document).scrollTop() - 1);
     }

    // $(".owl-carousel").owlCarousel({
    //     autoplay: true,
    //     autoplayTimeout: 3000,
    //     autoplayHoverPause: true,
    //     loop: true,
    //     margin: 10,
    //     responsiveClass: true,
    //     nav: false,
    //     responsive: {
    //         0: {
    //             items: 1,
    //             nav: true,
    //             loop: true
    //         },
    //         600: {
    //             items: 1,
    //             nav: true,
    //             loop: true
    //         },
    //         1025: {
    //             items: 3,
    //             nav: true,
    //             loop: true
    //         },
    //         1400: {
    //             items: 5,
    //             nav: true,
    //             loop: true
    //         }
    //     }
    // });


});

// //
// $(function () {
// //     // $(".datepicker").datepicker("hide");
//     $('.timepicker').timepicker({
//         timeFormat: 'h:mm a',
//         });
// //
// });

$("#id_date").prop("readonly", true);
$("#id_date").prop("disabled", true);

function week_days(sdate, date, is_Updated, id_time_went_to_bed, id_time_fell_asleep, id_time_got_up,id_out_of_bed, id_nap_time_asleep, id_no_of_times_awakend, id_total_time_awakened,
id_lights_out,id_minutes_fall_asleep,id_minutes_fellback_sleep,id_desire_wakeup_time,id_number_of_naps,id_totlatime_napping_minutes) {

    if (is_Updated == 'True') {
        // var date = new Date(date);
        //$('.datepicker').datepicker('update', new Date(date.getFullYear(), date.getMonth(), date.getDate()));
        var id_time_out_to_bed = "";
        $('#id_date').val(sdate);
        $('#sdate').val(date);
        $('#id_time_went_to_bed').val(id_time_went_to_bed);
        $('#id_lights_out').val(id_lights_out);
        $('#id_minutes_fall_asleep').val(id_minutes_fall_asleep);
        $('#id_minutes_fellback_sleep').val(id_minutes_fellback_sleep);
        $('#id_desire_wakeup_time').val(id_desire_wakeup_time);
        $('#id_number_of_naps').val(id_number_of_naps);
        $('#id_totlatime_napping_minutes').val(id_totlatime_napping_minutes);
        //$('#id_time_out_to_bed').val(id_time_out_to_bed);
        $('#id_time_fell_asleep').val(id_time_fell_asleep);
        $('#id_no_of_times_awakend').val(id_no_of_times_awakend);
        $('#id_out_of_bed').val(id_out_of_bed);
        $('#id_total_time_awakened').val(id_total_time_awakened);
        //$('#id_nap_time_asleep').val(id_nap_time_asleep);
        $('#id_time_got_up').val(id_time_got_up);
        $("#id_date").prop("disabled", true);
        $("#id_time_went_to_bed").prop("disabled", true);
        $('#id_lights_out').prop("disabled", true);
        $('#id_minutes_fall_asleep').prop("disabled", true);
        $('#id_minutes_fellback_sleep').prop("disabled", true);
        $('#id_desire_wakeup_time').prop("disabled", true);
        $('#id_number_of_naps').prop("disabled", true);
        $('#id_totlatime_napping_minutes').prop("disabled", true);
        $("#id_time_fell_asleep").prop("disabled", true);
        $("#id_time_got_up").prop("disabled", true);
        $("#id_out_of_bed").prop("disabled", true);
        //$("#id_nap_time_asleep").prop("disabled", true);
        $("#id_no_of_times_awakend").prop("disabled", true);
        $("#id_total_time_awakened").prop("disabled", true);
        $("#openPopup").prop("disabled", true);
        $("#addcomment").prop("disabled", true);
    } else {
        // var date = new Date(date);
        //$('.datepicker').datepicker('update', new Date(date.getFullYear(), date.getMonth(), date.getDate()));
        $('#id_date').val(sdate);
        $('#sdate').val(date);
        $("#id_date").prop("readonly", true);
        $("#id_date").prop("disabled", true);
        $('#id_nap_time_asleep').val('');
        $('#id_time_went_to_bed').val('');
        $('#id_out_of_bed').val('');
        $('#id_time_fell_asleep').val('0');
        $('#id_time_got_up').val('');
        $('#id_no_of_times_awakend').val('0');
        $('#id_total_time_awakened').val('0');
        $('#id_lights_out').val('');
        $('#id_minutes_fall_asleep').val('0');
        $('#id_minutes_fellback_sleep').val('0');
        $('#id_desire_wakeup_time').val('');
        $('#id_number_of_naps').val('0');
        $('#id_totlatime_napping_minutes').val('0');
        $("#id_nap_time_asleep").prop("disabled", false);
        $("#id_time_went_to_bed").prop("disabled", false);
        $("#id_out_of_bed").prop("disabled", false);
        $("#id_time_fell_asleep").prop("disabled", false);
        $("#id_time_got_up").prop("disabled", false);
        $("#id_no_of_times_awakend").prop("disabled", false);
        $("#id_total_time_awakened").prop("disabled", false);
        $('#id_lights_out').prop("disabled", false);
        $('#id_minutes_fall_asleep').prop("disabled", false);
        $('#id_minutes_fellback_sleep').prop("disabled", false);
        $('#id_desire_wakeup_time').prop("disabled", false);
        $('#id_number_of_naps').prop("disabled", false);
        $('#id_totlatime_napping_minutes').prop("disabled", false);
        $("#openPopup").prop("disabled", false);
        $("#addcomment").prop("disabled", false);
    }

}

function get_weeks_days(wday,patient) {
if(patient > 0){
    if (wday == 0) {
        window.location.href = "/dashboard/diary/" + wday+"/"+patient+"/";
    } else {
        window.location.href = "/dashboard/diary/" + (wday - 1)+"/"+patient+"/";
    }
    }else{
     if (wday == 0) {
        window.location.href = "/dashboard/diary/" + wday+"/"+patient+"/";
    } else {
        window.location.href = "/dashboard/diary/" + (wday - 1)+"/"+patient+"/";
    }
}

}


function goDashboard(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/patient/'+patient+'/';
    else
    window.location.href = '/dashboard/';
}

function goDiary(patient) {
    if(patient > 0)
        window.location.href = '/dashboard/diary/0/'+patient+"/";
    else
        window.location.href = '/dashboard/diary/0/0';
}
function magoDiary(patient) {
    if(patient > 0)
        window.location.href = '/dashboard/ma_diary/0/'+patient+"/";
    else
        window.location.href = '/dashboard/ma_diary/0/0';
}
function viewDiary(patient) {
     if(patient > 0)
        window.location.href = '/dashboard/patient/view-diary/0/'+patient+"/";
     else
         window.location.href = '/dashboard/view-diary/0/0/';
}
function maviewDiary(patient) {
     if(patient > 0)
        window.location.href = '/dashboard/ma-view-diary/0/'+patient+"/";
     else
         window.location.href = '/dashboard/ma-view-diary/0/0/';
}

function goDashboardsub(id,patient) {
    if(patient > 0)
    window.location.href = '/dashboard/patient/' + id + '/'+patient;
    else
    window.location.href = '/dashboard/' + id + '/';
}
function magoDashboardsub(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/ma-progress/'+patient;
    else
    window.location.href = '/dashboard/ma-progress/0/';
}

function goVideos(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/patient/videos/0/'+patient;
    else
    window.location.href = '/dashboard/videos/0/';

}
function magoVideos(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/ma_videos/0/'+patient;
    else
    window.location.href = '/dashboard/ma_videos/0/';

}

function goSE(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/patient/calculator/';
    else
    window.location.href = '/dashboard/calculator/';

}


function goNtl(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/ntl/';
    else
    window.location.href = '/dashboard/ntl/';

}
function magoNtl(patient) {
    if(patient > 0)
    window.location.href = '/dashboard/ma_ntl/'+patient;
    else
    window.location.href = '/dashboard/ma_ntl/';

}


//var aud = document.getElementById("video_" + 1);
$("#video_1,#video_2,#video_3,#video_4,#video_5,#video_6").on("ended",function () {
    $("#video_1_btn").html('Please proceed with your sleep diary');
    $("#video_1_btn").attr('onclick', 'goDiary()');
    $("#video_1_btn").show();
      $(".videowizard .welnextbtn").show();
      $(".videowizard .nextprevbtn").show();
});
// aud.onended = function () {
//     $("#video_1_btn").html('Please proceed with your sleep diary');
//     $("#video_1_btn").attr('onclick', 'goDiary()');
//     $("#video_1_btn").show();
// };
if(document.getElementsByTagName('video').length > 0){
var video = document.getElementsByTagName('video')[0];

video.onended = function (e) {
    $("#video_1_btn").show();
      $(".videowizard .welnextbtn").show();
      $(".videowizard .nextprevbtn").show();
};
}
function loadVideo(id, url) {

    $("#tabs_" + id).attr('data-toggle', 'pill');
    window.location.href = url;
}


// function openCity(evt, cityName) {
//     var i, tabcontent, tablinks;
//     tabcontent = document.getElementsByClassName("tabcontent");
//     for (i = 0; i < tabcontent.length; i++) {
//         tabcontent[i].style.display = "none";
//     }
//     tablinks = document.getElementsByClassName("tablinks");
//     for (i = 0; i < tablinks.length; i++) {
//         tablinks[i].className = tablinks[i].className.replace(" active", "");
//     }
//     document.getElementById(cityName).style.display = "block";
//     evt.currentTarget.className += " active";
// }

// Get the element with id="defaultOpen" and click on it
if(document.getElementById("defaultOpen"))
document.getElementById("defaultOpen").click();
$(document).off('.datepicker.data-api');
$(document).ready(function () {
    $('.datepicker').datepicker({format: "yyyy/mm/dd"});
});


$(".daybtn").click(function name(params) {
    $(".daybtn").each(function name(params) {
        $(this).parent().removeClass("active-day");
        $(this).parent().removeClass("active");
    });
   $(this).parent().addClass("active-day");
   $(this).parent().addClass("active");
});