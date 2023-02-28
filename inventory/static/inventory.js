$(document).ready(function() {

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
    } );

    $('.table').dataTable({
        "lengthMenu": [[20, 40, -1], [20, 40, "All"]],
        "searching": true,
        // "lengthChange": false,
        "pageLength": 20,
        "stateSave": true
    });

    $(function () {
      $('[data-toggle="tooltip"]').tooltip()
    });

    $('#quotes').tooltip({
        title: hoverGetData,
        html: true,
        container: 'body',
        placement: 'right'
    });

});

/*function hoverGetData(){
    var element = $(this);

    var id = element.data('id');

    if(id in cachedData){
        return cachedData[id];
    }

    var localData = "error";

    $.ajax('/your/url/' + id, {
        async: false,
        success: function(data){
            localData = data;
        }
    });

    cachedData[id] = localData;

    return localData;
}*/

function hoverGetData(){

    $.ajax('/get_limits/', {
        async: true,
        success: function(json) {
            rate_limit_remaining = json['rate_limit_remaining'];
            rate_limit_reset = json['rate_limit_reset'];
            btn_color =  json['btn_color']
        }
    });

    return rate_limit_remaining;
}

$(function() {
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        // save the latest tab; use cookies if you like 'em better:
        localStorage.setItem('lastTab', $(this).attr('href'));
    });

    // go to the latest tab, if it exists:
    var lastTab = localStorage.getItem('lastTab');
    if (lastTab) {
        $('[href="' + lastTab + '"]').tab('show');
    }
});