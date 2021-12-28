(function($) {
    $('input[type="checkbox"]').click(function () {
  
        try{
            var param = $("#param").val();
           
            if ($("#cb1").prop("checked") == true && param.indexOf("1")<0) {
                var param = $("#param").val();
                $("#from_date_wp").prop('required', true);
                $("#to_date_wp").prop('required', true);
                $("#from_date_wp").attr('readonly', false);
                $("#to_date_wp").attr('readonly', false);                
                $("#param").val(param + "1");

            }
            else if ($("#cb1").prop("checked") == false) {
                var param = $("#param").val();
                $("#from_date_wp").prop('required', false);
                $("#to_date_wp").prop('required', false);
                $("#from_date_wp").attr('readonly', true);
                $("#to_date_wp").attr('readonly', true);                      
                $("#param").val(param.replace("1", ""));
                $("#from_date_wp").val('');
                $("#to_date_wp").val('');
                $("#from_date_wp").val('');
                $("#to_date_wp").val('');
                $("#iswp").val(0);
                $("#istotal").val(parseInt($("#iswp").val())+parseInt($("#iswop").val())+parseInt($("#isut").val()));
                
            }
            if ($("#cb2").prop("checked") == true && param.indexOf("2")<0) {
                var param = $("#param").val();
                $("#from_date_wop").prop('required', true);
                $("#to_date_wop").prop('required', true);
                $("#from_date_wop").attr('readonly', false);
                $("#to_date_wop").attr('readonly', false);
                $("#param").val(param + "2");
            } 
            else if ($("#cb2").prop("checked") == false) {
                var param = $("#param").val();
                $("#from_date_wop").prop('required', false);
                $("#to_date_wop").prop('required', false);
                $("#from_date_wop").attr('readonly', true);
                $("#to_date_wop").attr('readonly', true);                
                $("#param").val(param.replace("2", ""));
                $("#from_date_wop").val('');
                $("#to_date_wop").val('');               
                $("#iswop").val(0);
                $("#istotal").val(parseInt($("#iswp").val())+parseInt($("#iswop").val())+parseInt($("#isut").val()));
            }
            if ($("#cb3").prop("checked") == true && param.indexOf("3")<0) {
                var param = $("#param").val();
                $("#from_date_ut").prop('required', true);
                $("#to_date_ut").prop('required', true);
                $("#no_hours_ut").prop('required', true);
                $("#from_date_ut").attr('readonly', false);                
                $("#to_date_ut").attr('readonly', false);
                $("#no_hours_ut").attr('readonly', false);
                $("#param").val(param + "3");

            } else if ($("#cb3").prop("checked") == false) {
                var param = $("#param").val();
                $("#from_date_ut").prop('required', false);
                $("#to_date_ut").prop('required', false);
                $("#no_hours_ut").prop('required', false);
                $("#from_date_ut").attr('readonly', true);
                $("#to_date_ut").attr('readonly', true);
                $("#no_hours_ut").attr('readonly', true);               
                $("#param").val(param.replace("3", ""));
                $("#from_date_ut").val('');
                $("#to_date_ut").val('');                
                $("#isut").val(0);
                $("#istotal").val(parseInt($("#iswp").val())+parseInt($("#iswop").val())+parseInt($("#isut").val()));
            }            
         
        }
        catch (ex) {
            alert(ex.message);
        }
    });














})(jQuery);




