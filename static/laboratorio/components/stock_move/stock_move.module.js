let mrpProductionCtl = require('./stock_move.ctl');

module.exports = angular.module('stockMove', [])
    .controller('stockMoveCtl', mrpProductionCtl)
    .component('stockMove', {
        templateUrl: '/mrp_kantu/static/laboratorio/components/stock_move/stock_move.html',
        controller: 'stockMoveCtl',
        bindings:{
            move: "=",
            moveselected:'=',
        }
    });