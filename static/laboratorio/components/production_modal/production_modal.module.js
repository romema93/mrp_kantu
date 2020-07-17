let productionModalCtl = require('./production_modal.ctl');

module.exports = angular.module('productionModal', [])
    .controller('productionModalCtl', productionModalCtl)
    .component('productionModal', {
        templateUrl: '/mrp_kantu/static/laboratorio/components/production_modal/production_modal.html',
        controller: 'productionModalCtl',
        bindings:{
            moveselected:'<',
            context:'='
        }
    });