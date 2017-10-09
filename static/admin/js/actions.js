/*global _actions_icnt, gettext, interpolate, ngettext*/
(function($) {
    'use strict';
    var lastChecked;
    console.log('new actions loaded')
    $.fn.actions = function(opts) {
        var options = $.extend({}, $.fn.actions.defaults, opts);
        var actionCheckboxes = $(this);
        var list_editable_changed = false;
        var showQuestion = function() {
            $(options.acrossClears).hide();
            $(options.acrossQuestions).show();
            $(options.allContainer).hide();
        },
        showClear = function() {
            $(options.acrossClears).show();
            $(options.acrossQuestions).hide();
            $(options.actionContainer).toggleClass(options.selectedClass);
            $(options.allContainer).show();
            $(options.counterContainer).hide();
        },
        reset = function() {
            $(options.acrossClears).hide();
            $(options.acrossQuestions).hide();
            $(options.allContainer).hide();
            $(options.counterContainer).show();
        },
        clearAcross = function() {
            reset();
            $(options.acrossInput).val(0);
            $(options.actionContainer).removeClass(options.selectedClass);
        },
        checker = function(checked) {
            if (checked) {
                showQuestion();
            } else {
                reset();
            }
            $(actionCheckboxes).prop("checked", checked)
                .parent().parent().toggleClass(options.selectedClass, checked);
        },
        updateCounter = function() {
            var sel = $(actionCheckboxes).filter(":checked").length;
            // _actions_icnt is defined in the generated HTML
            // and contains the total amount of objects in the queryset
            $(options.counterContainer).html(interpolate(
            ngettext('%(sel)s of %(cnt)s selected', '%(sel)s of %(cnt)s selected', sel), {
                sel: sel,
                cnt: _actions_icnt
            }, true));
            $(options.allToggle).prop("checked", function() {
                var value;
                if (sel === actionCheckboxes.length) {
                    value = true;
                    showQuestion();
                } else {
                    value = false;
                    clearAcross();
                }
                return value;
            });
        };
        // Show counter by default
        $(options.counterContainer).show();
        // Check state of checkboxes and reinit state if needed
        $(this).filter(":checked").each(function(i) {
            $(this).parent().parent().toggleClass(options.selectedClass);
            updateCounter();
            if ($(options.acrossInput).val() === 1) {
                showClear();
            }
        });
        $(options.allToggle).show().click(function() {
            checker($(this).prop("checked"));
            updateCounter();
        });
        $("a", options.acrossQuestions).click(function(event) {
            event.preventDefault();
            $(options.acrossInput).val(1);
            showClear();
        });
        $("a", options.acrossClears).click(function(event) {
            event.preventDefault();
            $(options.allToggle).prop("checked", false);
            clearAcross();
            checker(0);
            updateCounter();
        });
        lastChecked = null;
        $(actionCheckboxes).click(function(event) {
            if (!event) { event = window.event; }
            var target = event.target ? event.target : event.srcElement;
            if (lastChecked && $.data(lastChecked) !== $.data(target) && event.shiftKey === true) {
                var inrange = false;
                $(lastChecked).prop("checked", target.checked)
                    .parent().parent().toggleClass(options.selectedClass, target.checked);
                $(actionCheckboxes).each(function() {
                    if ($.data(this) === $.data(lastChecked) || $.data(this) === $.data(target)) {
                        inrange = (inrange) ? false : true;
                    }
                    if (inrange) {
                        $(this).prop("checked", target.checked)
                            .parent().parent().toggleClass(options.selectedClass, target.checked);
                    }
                });
            }
            $(target).parent().parent().toggleClass(options.selectedClass, target.checked);
            lastChecked = target;
            updateCounter();
        });
        $('form#changelist-form table#result_list tr').find('td:gt(0) :input').change(function() {
            list_editable_changed = true;
        });
        $('form#changelist-form button[name="index"]').click(function(event) {
            if (list_editable_changed) {
                return confirm(gettext("You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost."));
            }
        });
        $('form#changelist-form .field-invnum_form [type="button"]').click(function(event){
            var el = $(this);
            var parent = el.parent();
            var inputInvoice = parent.find('input[name="invoice_number"]');
            var inputOrderId = parent.find('input[name="order_id"]');

            var invoiceValue = inputInvoice.val().trim();
            var orderId = inputOrderId.val().trim();

            if (invoiceValue === '' || orderId === '') { return; }
            
            var URL_POST = '/admin/orders/save_invnum/';

            var data = {
                'invoice_number': invoiceValue,
                'order_id': orderId
            }

            $.post(URL_POST, data, function(data, status){
                if (status == 'success') {
                    window.location.reload();
                }
            });

        });
        $('form#changelist-form .field-printed_button input[type="button"]').click(function(event){
            var el = $(this);
            var parent = el.parent();
            var inputOrderId = parent.find('input[name="order_id"]');
            var orderId = inputOrderId.val().trim();
            if (orderId === '') { return; }

            var URL_CONFIRM_PRINT = '/admin/orders/save_printed/';

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
            el.hide()
            parent.append(loader)
            var data = { 'order_id': orderId }
            $.post(URL_CONFIRM_PRINT, data, function(data, status){
                if (status == 'success') {
                    parent.html('Printed');
                } else {
                    $('#floatingCirclesG').remove()
                }
            });

        });
        $('form#changelist-form .field-email_client input[type="button"]').click(function(event){
            var el = $(this);
            var parent = el.parent();
            var inputOrderId = parent.find('input[name="order_id"]');
            var orderId = inputOrderId.val().trim();
            if (orderId === '') { return; }

            var URL_CONFIRM_PRINT = '/admin/orders/save_printed_client/';

            var loader = '<div id="floatingCirclesG">' +
                                '<div class="f_circleG" id="frotateG_01"></div>' +
                                '<div class="f_circleG" id="frotateG_02"></div>' +
                                '<div class="f_circleG" id="frotateG_03"></div>' +
                                '<div class="f_circleG" id="frotateG_04"></div>' +
                                '<div class="f_circleG" id="frotateG_05"></div>' +
                                '<div class="f_circleG" id="frotateG_06"></div>' +
                                '<div class="f_circleG" id="frotateG_07"></div>' +
                                '<div class="f_circleG" id="frotateG_08"></div>' +
                            '</div>';
            el.hide();
            parent.append(loader);
            var data = { 'order_id': orderId };
            $.post(URL_CONFIRM_PRINT, data, function(data, status){
                $('#floatingCirclesG').remove();
                if (status == 'success') {
                    // window.location.reload();
                    parent.html('Sent');
                } else {
                    el.show();
                }
            });
        });
        $('form#changelist-form input[name="_save"]').click(function(event) {
            var action_changed = false;
            $('select option:selected', options.actionContainer).each(function() {
                if ($(this).val()) {
                    action_changed = true;
                }
            });
            if (action_changed) {
                if (list_editable_changed) {
                    return confirm(gettext("You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action."));
                } else {
                    return confirm(gettext("You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button."));
                }
            }
        });
    };
    /* Setup plugin defaults */
    $.fn.actions.defaults = {
        actionContainer: "div.actions",
        counterContainer: "span.action-counter",
        allContainer: "div.actions span.all",
        acrossInput: "div.actions input.select-across",
        acrossQuestions: "div.actions span.question",
        acrossClears: "div.actions span.clear",
        allToggle: "#action-toggle",
        selectedClass: "selected"
    };
})(django.jQuery);
