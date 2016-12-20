function LabelConstructor(config){
  $.extend(this.options = {}, config || {});

  this.elem = $(this.options.elem);
  this.background_image = $(this.options.image);

  this.create_container();
  this.container.append(this.create_view());
  this.container.append(this.create_toolbar());
}

LabelConstructor.prototype.make_classes = function(def, field){
  if(!(def instanceof Array))
    def = def.split(' ');

  if(field in this.options){
    var t = this.otptions[field];

    if(!(t instanceof Array))
      t = t.split(' ');

    def.concat(t);
  }

  return $.unique(def).join(' ');
};

LabelConstructor.prototype.create_container = function(){
  return this.container = $('<div/>').
    addClass(this.make_classes('lc-container', 'containerClasses'));
};

LabelConstructor.prototype.create_view = function(){
  var self = this;

  $('<img/>').load(function(){
    self.real_width = this.width;
    self.real_height = this.height;
  });

  return this.view = $('<img/>').
    addClass(this.make_classes('lc-view', 'viewClasses')).
    attr('src', this.options.image);
};

LabelConstructor.prototype.create_toolbar = function(){
  this.toolbar = $('<div/>').
    addClass(this.make_classes('lc-toolbar', 'toolbarClasses'));

  this.labelList = $('<div/>').
    addClass(this.make_classes('lc-label-list', 'labelListClasses'));

  this.toolbar.append(this.labelList);
  
  var self = this;
  var addBtn = $('<div/>').
    addClass(this.make_classes('lc-add-btn', 'addBtnClasses')).
    click(function(){
      self.addEmptyLabel();
      return false;
    });

  this.toolbar.append(addBtn);

  return this.toolbar;
};


