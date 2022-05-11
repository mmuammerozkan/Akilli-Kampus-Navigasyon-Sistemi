$(document).ready(function(){

    $(".btn").click(function(){
        $.ajax({
            url:"",
            type: "get",
            data:{
                button_text: $(this).text()
            },
            success: function(response) {
                $(".btn").text(response.seconds)
                $("#seconds").append('<li>'+response.seconds+'</li>')
            }
        });
    });

});