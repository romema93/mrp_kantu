'use strict';
let mrpProductionModule = require('./components/mrp_production/mrp_production.module');
let serviceModule = require('./services/service.module');
let stockMoveModule = require('./components/stock_move/stock_move.module');
let productionModalModule = require('./components/production_modal/production_modal.module');

angular.module('laboratorio', [
    'ui.bootstrap',
    mrpProductionModule.name,
    serviceModule.name,
    stockMoveModule.name,
    productionModalModule.name,

]).controller('laboratorioCtl', function ($scope) {
    $scope.production = +$('#production').text();
    $scope.context = JSON.parse($('#context').text());
});