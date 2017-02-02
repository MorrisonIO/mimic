function buildmenu(){
    $.ajax({
        url: 'get_menu_data',
        success: function(response){
            // console.log("response", response)
            drawMenu(JSON.parse(response))
        },
        error: function(err){
            console.log('err',err)
        }
    })

    function toOneWord(text){
        return text.split(' ').join('-');
    }

    function drawMenu(data){
        // return
        var html= '<ul>';
        var index = 0;
        for(category in data){
            var li_tag = '<li><h3><span class="icon-dashboard"></span>'+ data[category]['title'] +'</h3><ul class="filters-category">'
            for (row in data[category]){
                if (row.toLowerCase() == 'title') continue;
                index++;
                if(category.toLowerCase() == 'num_of_images'){
                    li_tag += '<li> <input class="filter" data-filter=".'+ toOneWord(row) +'" type="checkbox" id="checkbox'+index+'">'+
                          '<label class="checkbox-label" for="checkbox' + index + '">' + row + '</label></li>';
                } else if(category.toLowerCase() == 'feature_prop'){
                    li_tag += '<li> <input class="filter" data-filter=".feature-' + toOneWord(row) + '" type="checkbox" id="checkbox'+index+'">'+
                          '<label class="checkbox-label" for="checkbox' + index + '">' + row  + '</label></li>';
                } else {
                    li_tag += '<li> <input class="filter" data-filter=".'+ '' +'" type="checkbox" id="checkbox'+index+'">'+
                            '<label class="checkbox-label" for="checkbox' + index + '">' + row + '</label></li>';                }

            }
            li_tag += '</ul></li>'
            html += li_tag
        }
        html += '</ul>'
        $('#accordian').html(html)
        $('#accordian > ul > li').first().addClass('active')

        $("#accordian h3").click(function(){
            // slide up/down all the link lists
            // slide down the link list below the h3 clicked - only if its closed
            if(!$(this).next().is(":visible")) {
                $(this).next().slideDown();
            } else {
                $(this).next().slideUp();
            }
        })
        buttonFilter.init();
    }
}
    
var buttonFilter = {
  	// Declare any variables we will need as properties of the object
  	$filters: null,
  	groups: [],
  	outputArray: [],
  	outputString: '',
  
  	// The "init" method will run on document ready and cache any jQuery objects we will need.
  	init: function(){
    	var self = this; // As a best practice, in each method we will asign "this" to the variable "self" so that it remains scope-agnostic. We will use it to refer to the parent "buttonFilter" object so that we can share methods and properties between all parts of the object.
    
    	self.$filters = $('.sidebar ');
    	self.$container = $('.content ');
    
	    self.$filters.find('.filters-category').each(function(){
	      	var $this = $(this);
	      
		    self.groups.push({
		        $inputs: $this.find('.filter'),
		        active: '',
		        tracker: false
		    });
	    });
	    
	    self.bindHandlers();
  	},
  
  	// The "bindHandlers" method will listen for whenever a button is clicked. 
  	bindHandlers: function(){
    	var self = this;

    	self.$filters.on('click', 'a', function(e){
	      	self.parseFilters();
    	});
	    self.$filters.on('change', function(){
	      self.parseFilters();           
	    });
  	},
  
  	parseFilters: function(){
	    var self = this;
	    // loop through each filter group and grap the active filter from each one.
	    for(var i = 0, group; group = self.groups[i]; i++){
	    	group.active = [];
	    	group.$inputs.each(function(){
	    		var $this = $(this);
	    		if($this.is('input[type="radio"]') || $this.is('input[type="checkbox"]')) {
	    			if($this.is(':checked') ) {
	    				group.active.push($this.attr('data-filter'));
	    			}
	    		} else if( $this.find('.selected').length > 0 ) {
	    			group.active.push($this.attr('data-filter'));
	    		}
	    	});
	    }
	    self.concatenate();
  	},
  
  	concatenate: function(){
    	var self = this;
    
    	self.outputString = ''; // Reset output string
    
	    for(var i = 0, group; group = self.groups[i]; i++){
	      	self.outputString += group.active;
	    }
	    // If the output string is empty, show all rather than none:    
	    !self.outputString.length && (self.outputString = 'all'); 
        
    	// Hide unselected items
        if(self.outputString == "all"){
            $('.filterable').show(200)
        } else {
            $('.filterable:not('+ self.outputString +')').hide(200)
            $('.filterable'+ self.outputString).show(200)
        }
  	}
};