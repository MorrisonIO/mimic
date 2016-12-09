// Function to generate a unique 32 char string, used to identify which upload we're interested in
function gen_uuid() {
    var uuid = "";
    for (var i = 0; i < 32; i++) {
        uuid += Math.floor(Math.random() * 16).toString(16);
    }
    return uuid;
}

var progress_url = '/upload/progress/'; // which URL to visit to get progress info (must return JSON)
var freq = 1000; // how often (in milliseconds) to poll the progress_url

$(document).ready(function() { 
    $("#progress_container", parent.document).hide();

    var uuid = gen_uuid();

    /* Function to poll the progress url, calculate what percentage has been
     * uploaded so far, and update the visual progressbar on the page. Note that since
     * this code is being called from within an iframe, we have to update elements on 
     * the parent page. */
    function update_progress_info() {
        $.getJSON('/upload/progress/', 
            {
                'X-Progress-ID': uuid
            },
            function(data, status) {
                if (data) {
                    var progress = parseInt(data.received) / parseInt(data.size);
                    var width = $('#progress_container', parent.document).width();
                    var progress_width = Math.floor(width * progress);
                    $("#progress_indicator", parent.document).width(progress_width);
                    var filename = $("#id_file", parent.document).val().split(/[\/\\]/).pop();
                    $("#progress_filename", parent.document).text('Uploading ' + filename + ': ' + parseInt(progress * 100) + '%');
                    if (progress == 1 || data.state == 'done') {
                        window.clearInterval(intervalID);
                    }
                }
            }
        );
    };

    // When the form is submitted, modify the action of the form and call the updating code.
    $("#upload_form", parent.document).submit(
        function(eventObject) {
            $("#submit_button", parent.document).hide();
            this.action += (this.action.indexOf('?') == -1 ? '?': '&') + 'X-Progress-ID=' + uuid;
            intervalID = window.setInterval(update_progress_info, 1000);
            $("#progress_container", parent.document).show();
        }
    );
});
