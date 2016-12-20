$(document).ready(function(){
  $.error = function(){ console.log(arguments); };

  var jqCronInit = false;

  var switcher = $('#id_scheduled');
  var schedule = $('#id_schedule');

  var parent = schedule.closest('div');

  schedule.hide();
  var scheduler = $('<div/>');
  parent.append(scheduler)

  switcher.change(function(){
    if($(this).is(':checked')){
      parent.show();

      if(!jqCronInit){
        scheduler.cron({
          initial: schedule.val() || '* * * * *',

          onChange: function(){
            schedule.val($(this).cron('value'));
          }
        });

        jqCronInit = true;
      }
    }else
      parent.hide();
  }).change();
});
