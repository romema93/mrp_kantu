var apiServerService = require('./api_server.service');
var mrpProductionService = require('./mrp_production.service');

module.exports = angular.module('Services',[])
    .factory('apiServerService', apiServerService)
    .factory('mrpProductionService', mrpProductionService);