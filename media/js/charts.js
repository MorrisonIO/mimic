/*
    Name:   charts.js
    Title:  Custom javascript/flot parameters for drawing various charts. 
    Author: Dieter Limeback <dieter.limeback@mimicprint.com>

    NOTE:   Requires jQuery and flot
*/

function makeChart(data, hide) {

    if ( hide ) {
        var colorVal = '#ffffff';
        var tickColorVal = '#ffffff';
    } else {
        var colorVal = '#444444';
        var tickColorVal = '#dddddd';
    }

    monthNames = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ];

    var placeholder = $("#placeholder");
    var datasets = data;

    var options = {
        lines: { show: true },
        points: { show: true },
        legend: { container: $("#legend") },
        yaxis: { min: 0 },
        xaxis: { mode: "time", minTickSize: [1, "month"] },
        grid: {
            clickable: true,
            hoverable: true,
            hoverFill: '#444',
            hoverRadius: 5,
            color: colorVal,
            tickColor: tickColorVal
        },
        hints: {
            show: true
        }
    };

    // hard-code color indices to prevent them from shifting as
    // countries are turned on/off
    var i = 0;
    $.each(datasets, function(key, val) {
        val.color = i;
        ++i;
    });
    
    // insert checkboxes 
    var choiceContainer = $("#choices");
    $.each(datasets, function(key, val) {
        choiceContainer.append('<br/><input type="checkbox" name="' + key +
                               '" checked="checked" id="id' + key + '">' +
                               '<label for="id' + key + '">'
                                + val.label + '</label>');
    });
    choiceContainer.find("input").click(plotAccordingToChoices);

    
    // draw the chart based on which data is selected
    function plotAccordingToChoices() {
        var data = [];

        choiceContainer.find("input:checked").each(function () {
            var key = $(this).attr("name");
            if (key && datasets[key])
                data.push(datasets[key]);
        });

        if (data.length > 0) {
            $.plot(placeholder, data, options);
        }
    }
    plotAccordingToChoices();
    

    // tooltips
    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
    $("#placeholder").bind("plothover", function (event, pos, item) {
        if (item) {
            if (previousPoint != item.datapoint) {
                previousPoint = item.datapoint;
                
                $("#tooltip").remove();
                
                var d = new Date(item.datapoint[0]);
                var month = monthNames[d.getUTCMonth()];
                var year = d.getUTCFullYear();
                var qty = item.datapoint[1];

                showTooltip(item.pageX, item.pageY,
                            item.series.label + " <br /> " + month + " " + year + ": " + qty + " ordered");
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;            
        }
    });

    // IE6 cannot toggle the products on/off
    if(typeof document.body.style.maxHeight === "undefined") {
        $("#choices").hide();
    }
}
