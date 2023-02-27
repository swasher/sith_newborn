$(document).ready(function() {

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $.fn.dataTable.tables( {visible: true, api: true} ).columns.adjust();
    } );

    $('#table-computer, #table-cpu, #table-memory, #table-storage, #table-devices').DataTable({
        "iDisplayLength": 20,
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        stateSave: true
    });
});

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