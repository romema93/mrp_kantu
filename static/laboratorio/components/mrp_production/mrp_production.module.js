var mrpProductionCtl = require('./mrp_production.ctl');

module.exports = angular.module('mrpProduction', [])
    .controller('mrpProductionCtl', mrpProductionCtl)
    .component('mrpProduction', {
        templateUrl: '/mrp_kantu/static/laboratorio/components/mrp_production/mrp_production.html',
        controller: 'mrpProductionCtl',
        bindings:{
            production: "=",
            context: "="
        }
    });