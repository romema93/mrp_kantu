odoo.define('mrp_kantu.production_view', function (require) {
"use strict";
var Widget = require('web.Widget');
var core = require('web.core');
var Model = require('web.Model');
var QWeb = core.qweb;

var HomePage = Widget.extend({
     className:'oe_laboratorio',
     init: function (parent, action) {
        this._super.apply(this, arguments);
        this.materials = action.materials;
     },
     start: function(){
         var self = this;
         //self.$el.append(QWeb.render('MrpMaterialesView',{widget: self}));
         self.$el.append(QWeb.render('MrpMaterialesView',{widget: self}));
         this.$el.find('.oe-producir').click(_.bind(this.clickAppendNewProduction, this));
     },
     clickAppendNewProduction: function(event) {
        console.log(event);
        //var newChar;
        //newChar = event.currentTarget.innerText || event.currentTarget.textContent;
        //return this.state.appendNewChar(newChar);
    },
});

    core.action_registry.add('mrp_kantu.production_view', HomePage);

return HomePage;
});