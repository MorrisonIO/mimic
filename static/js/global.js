/********************************************************************************
 *
 * Name:    global.js
 * Desc:    Custom js for mimicprint2.com
 * Author:  Dieter Limeback <dieter.limeback@mimicprint.com>
 *
 *******************************************************************************/


/* Function to toggle things with a fade instead of mere visibility, as
 * is the default with .toggle()
 */
jQuery.fn.fadeToggle = function(speed, easing, callback) {
   return this.animate({opacity: 'toggle'}, speed, easing, callback);
}; 

/* Function to close an open facebox dialog
 */
function closeDialog() {
    jQuery(document).trigger('close.facebox');
}

/* Functions for fading out background color. 
 * Modified from http://www.codylindley.com/blogstuff/js/jquery/
 */
function easeInOut(minValue,maxValue,totalSteps,actualStep,powr) {
	var delta = maxValue - minValue;
	var stepp = minValue+(Math.pow(((1 / totalSteps)*actualStep),powr)*delta);
	return Math.ceil(stepp)
}
function addFade() {
    var str = $(this).css('background-color');
    var colors = str.slice(4,-1).split(',');
    var r = new Number(colors[0]);
    var g = new Number(colors[1]);
    var b = new Number(colors[2]);
    doBGFade(this,[r,g,b],[255,255,255],'transparent',75,10,4);
}
function doBGFade(elem,startRGB,endRGB,finalColor,steps,intervals,powr) {
	if (elem.bgFadeInt) window.clearInterval(elem.bgFadeInt);
	var actStep = 0;
	elem.bgFadeInt = window.setInterval(
		function() {
			elem.style.backgroundColor = "rgb("+
				easeInOut(startRGB[0],endRGB[0],steps,actStep,powr)+","+
				easeInOut(startRGB[1],endRGB[1],steps,actStep,powr)+","+
				easeInOut(startRGB[2],endRGB[2],steps,actStep,powr)+")";
			actStep++;
			if (actStep > steps) {
			elem.style.backgroundColor = finalColor;
			window.clearInterval(elem.bgFadeInt);
			}
		}
		,intervals)
}

/* Hide spinners on page load; show them when submit buttons are
 * clicked. Called from regular pages, but also from within dialog
 * boxes. 
 */
function toggleSpinner() { 
    $("img.spinner").hide();
    $("button[type='submit']").css('margin-left', '20px');
    $("button[type='submit']").click(function(){
            $(this).css('margin-left', '0px'); 
            var spinner = $(this).prev(); 
            spinner.show(); 
            var img = $(this).find("img");
            $(this).addClass('processing');
            $(this).html('<img src="' + img.attr('src') + '"> Processing...'); 
    }); 
}

// ----- ON PAGE LOAD -----
$(document).ready(function(){
        
    // Datepickers
    $(".datepicker").datepick({
        showOn:'button', 
        buttonImage: MEDIA_URL + 'img/calendar_month.png', 
        buttonImageOnly:true, 
        dateFormat:'yy-mm-dd' 
    });       

    // tablesorter
    $(".tablesorter").tablesorter();

    // print buttons
    $('a[rel*=print]').click(function(){
        window.print();
        return false;
    });

    // facebox 
    $.facebox.settings.opacity = 0.5;
    $.facebox.settings.loadingImage = MEDIA_URL + 'img/loading.gif';
    $.facebox.settings.closeImage = MEDIA_URL + 'img/closelabel.gif';
    $('a[rel*=dialog]').facebox();

    // fade alert boxes (except error ones) after a few seconds
    if (!$.browser.msie) { // TODO
        var msgbox = $("div.msgbox");
        if (!msgbox.hasClass('alert_e')) {
            msgbox
            .animate({opacity: 1.0}, 2000, "linear", function(){ // pause first (http://www.learningjquery.com/2007/01/effect-delay-trick) then remove border
                $(this).css('border', "1px solid #fff")
            })
            .animate({opacity: 1.0}, 0, "linear", addFade) // fade background
        }
    }

    // hide spinner on page load; show when submit buttons clicked
    toggleSpinner();

    // clear search input boxes of placeholder text on focus
    $("#search_input").labelify({ labelledClass: 'labelled' });


    // CURRENT ORG MENU
    // See no_current_org.html template for setting error condition
    if ( $.cookie('setorg') == 'done' ) { // user just selected, show success and then hide
        $("div#org_menu").addClass('success');
        $('#setorg select').after('<img src="' + MEDIA_URL + 'img/tick_circle.png" alt="" class="success" id="success_icon">');
        $("div#org_menu").animate({opacity: 1.0}, 1000).fadeOut();
        $.cookie('setorg', '');
    } else { // hide by default
        $("div#org_menu").hide();
    }
    $("#show_orgmenu").click(function(){ 
        $("div#org_menu").removeClass('success'); 
        $('div#org_menu img.success').hide();
        $("div#org_menu").slideToggle();
        return false;
    });
    $("#org_list").change(function(){ 
        $.cookie('setorg', 'done'); // set cookie when selecting org to show success on next pageload
        $("form#setorg").submit();
    });


    // ADDRESS BOOK
    // toggle open more address details in business card view
    $("td.address a.toggle").click(function(){
        var $more = $(this).prev();
        var $text = $(this).text();
//        $more.fadeToggle();
        $more.toggle();
        if ( $text == "Show") {
            $(this).text("Hide");
        } else {
            $(this).text("Show");
        }
        return false;
    });

    // address view switching; remember pref with cookie
    $("#ab_view_bc").click(function(){
        $("#ab_view_table").toggleClass("icon_selected");
        $("#ab_view_bc").toggleClass("icon_selected");
        $("#address_table").fadeOut("normal");
        $("#address_bc").fadeIn("normal");
        $.cookie('ab_view', 'bc');
        return false;
    });
    $("#ab_view_table").click(function(){
        $("#ab_view_table").toggleClass("icon_selected");
        $("#ab_view_bc").toggleClass("icon_selected");
        $("#address_bc").fadeOut("normal");
        $("#address_table").fadeIn("normal");
        $.cookie('ab_view', 'table');
        return false;
    });


    // PRODUCT LIST
    $("h3.category").click(function(){
        var table = $(this).next();
        var self = $(this)
        if ( table.is(':visible') ) {
            self.addClass('cat-closed');
        } else {
            if(!self.hasClass('loaded')) {
                var loader = '<div id="floatingCirclesG">' +
                                '<div class="f_circleG" id="frotateG_01"></div>' + 
                                '<div class="f_circleG" id="frotateG_02"></div>' + 
                                '<div class="f_circleG" id="frotateG_03"></div>' + 
                                '<div class="f_circleG" id="frotateG_04"></div>' + 
                                '<div class="f_circleG" id="frotateG_05"></div>' + 
                                '<div class="f_circleG" id="frotateG_06"></div>' + 
                                '<div class="f_circleG" id="frotateG_07"></div>' + 
                                '<div class="f_circleG" id="frotateG_08"></div>' +
                            '</div>'
                table.find('tbody').html(loader)
                $.get({
                    url: 'category/',
                    data: {
                        id: self.attr('data-id')
                    }
                }).done(function(res){
                    self.addClass('loaded')
                    console.log('res', res)
                    table.find('tbody').html(res)
                })
            }
            self.removeClass('cat-closed');
        }
        table.fadeToggle();
        // reattach facebox to preview links, otherwise if the page
        // starts out with categories collapsed, facebox doesn't work
        $('a[rel*=dialog]').facebox(); 
    });


    // ORDERING
    // Cart Summary
    $("form.qty_modify").hide();
    $("a.toggle_qty_modify").click(function(){
        var form = $(this).next();
        form.fadeToggle();
        return false;
    });

    // Provide shipto
    $("a#t_provide_shipto").click(function(){
//        $("div#address").slideUp();
        $("div#provide_shipto").slideToggle();
        return false;
    });
    $("a#t_address_form").click(function(){
        $("div#address_form").slideToggle();
        $("div#continue").hide();
        return false;
    });
    $("#shipto_menu").change(function(){ 
        $("form#shipto_form").submit();
    });

    $("#id_pickup_in_address").click(function(){
        $("div.address_form-address").slideToggle();
        // $("div#continue").hide();
        // return false;
    });


	// REPORTING
	$("#report_form fieldset").hide();
	$("#narrow_default").show();
	$("#n_date").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_date").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
	$("#n_org").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_org").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
	$("#n_product").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_product").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
	$("#n_user").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_user").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
	$("#n_schedule").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_schedule").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
	$("#n_category").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_categories").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
    $("#n_states").click(function(){
		$("#report_form fieldset").hide();
		$("#narrow_states").show();
		$("#report_nav li a").removeClass("active");
		$(this).addClass("active");
		return false;
	})
});
