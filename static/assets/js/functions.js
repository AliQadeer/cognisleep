function auth_login(url) {

    email = document.getElementById("txtuseremail").value;
    password = document.getElementById("pwd").value;
    csrfmiddlewaretoken = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    $("#errorlogin").html("");
    $.ajax({
        type: "POST",
        url: url + 'login/',
        data: $('#login_form').serialize(),
        success: function (data) {
            console.log(data);
            if (data['message'] == "Success") {
                location.reload();
            } else if (data['message'] == "inactive") {
                $("#errorlogin").html("Please verify this E-mail address.");
            } else {
                $("#errorlogin").html("The E-mail and Password do not match.");
            }
        }
    });
}






function create_patient_event() {
    if ($('#ref_chk').is(':checked')) {
        window.location.href = "/accounts/patientregform/";
    } else {
        window.location.href = "/questions/cogni_questions";
    }
}


function passeye() {

    var x = document.getElementById("password1");
    var y = document.getElementById("password2");
    if (x.type === "password") {
        x.type = "text";
        y.type = "text";
        return false;
    } else {
        x.type = "password";
        y.type = "password";
    }
}

function passeye_2() {

    var x = document.getElementById("id_password1");
    var y = document.getElementById("id_password2");
    if (x.type === "password") {
        x.type = "text";
        y.type = "text";
        return false;
    } else {
        x.type = "password";
        y.type = "password";
    }
}