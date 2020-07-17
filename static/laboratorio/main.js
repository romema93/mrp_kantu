(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';
var mrpProductionModule = require('./components/mrp_production/mrp_production.module');
var serviceModule = require('./services/service.module');
var stockMoveModule = require('./components/stock_move/stock_move.module');
var productionModalModule = require('./components/production_modal/production_modal.module');

angular.module('laboratorio', [
    mrpProductionModule.name,
    serviceModule.name,
    stockMoveModule.name,
    productionModalModule.name,

]).controller('laboratorioCtl', function ($scope) {
    $scope.production = +$('#production').text();
    $scope.context = JSON.parse($('#context').text());
});
},{"./components/mrp_production/mrp_production.module":3,"./components/production_modal/production_modal.module":5,"./components/stock_move/stock_move.module":7,"./services/service.module":10}],2:[function(require,module,exports){
module.exports = function (mrpProductionService) {
    let vm = this;
    vm.moveselected = {};

    /*
    Panel toolbox
     */
    $(document).ready(function() {
        $('.collapse-link').on('click', function() {
            var $BOX_PANEL = $(this).closest('.x_panel'),
                $ICON = $(this).find('i'),
                $BOX_CONTENT = $BOX_PANEL.find('.x_content');

            // fix for some div with hardcoded fix class
            if ($BOX_PANEL.attr('style')) {
                $BOX_CONTENT.slideToggle(200, function(){
                    $BOX_PANEL.removeAttr('style');
                });
            } else {
                $BOX_CONTENT.slideToggle(200);
                $BOX_PANEL.css('height', 'auto');
            }

            $ICON.toggleClass('fa-chevron-up fa-chevron-down');
        });

        $('.close-link').click(function () {
            var $BOX_PANEL = $(this).closest('.x_panel');

            $BOX_PANEL.remove();
        });
    });

    this.$onInit = function() {
        mrpProductionService.GetMrpProduction(vm.production,vm.context)
            .then(function (res) {
                vm.mrpProduction = res;
                mrpProductionService.GetMoveRaws(vm.mrpProduction.move_raw_ids,vm.context)
                    .then(function (res) {
                        vm.move_raws = res;
                    })
                    .catch(function (err) {
                        console.log(err);
                    });
                let domain = [
                    ['origin','=',vm.mrpProduction.name+':'+vm.mrpProduction.name]
                ];
                mrpProductionService.GetBomProduction(vm.context,domain)
                    .then(function (res) {
                        console.log(res);
                    })
                    .catch(function (err) {
                        console.log(err);
                    })
            }).catch(function (err) {
                console.log(err);
        });
    };
};
},{}],3:[function(require,module,exports){
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
},{"./mrp_production.ctl":2}],4:[function(require,module,exports){
module.exports = function (mrpProductionService) {
    let vm = this;
    vm.mrpProduction = {};
    //variable para almacenar el array de los atributos del mrpProduction
    vm.attributesMrpProduction = [];
    vm.$onInit = function () {

    };
    //Funcion que se ejecuta al cambiar el parametro pasado al componente
    vm.$onChanges = function(changesObj){
        //Verificamos que existe el Product_id
        if(changesObj.moveselected.currentValue.product_id != undefined){
            vm.mrpProductionSelected = Object.assign({},changesObj.moveselected.currentValue);
            vm.mrpProduction.product_id = vm.mrpProductionSelected.product_id;
            vm.mrpProduction.product_qty = vm.mrpProductionSelected.product_qty;
            vm.mrpProduction.product_uom = vm.mrpProductionSelected.product_uom;
        }
        //Obtenemos los atributos del MrpProduction
        vm.attributesMrpProduction = [];
        for(var prop in vm.mrpProductionSelected){
            if(prop != '$$hashKey'){
                vm.attributesMrpProduction.push(prop);
            }
        }
        //Obtenemos los valores por defecto para crear un mrpProduction
        mrpProductionService.GetDefaultValues(vm.context,vm.attributesMrpProduction)
            .then(function (res) {
                console.log(res);
            })
            .catch(function (err) {
                console.log(err);
            })
    };
};
},{}],5:[function(require,module,exports){
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
},{"./production_modal.ctl":4}],6:[function(require,module,exports){
module.exports = function () {
    let vm = this;
    this.$onInit = function() {

    };
    vm.SelectMove = function () {
        vm.moveselected = vm.move;
    }
};
},{}],7:[function(require,module,exports){
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
},{"./stock_move.ctl":6}],8:[function(require,module,exports){
module.exports = function ($http, $q) {
    return {
        //Operaciones CRUD para los modelos
        call_kw: function (p_args, p_kwargs, p_method, p_model) {
            let defered = $q.defer();
            let promise = defered.promise;
            $http.post('/web/dataset/call_kw', {
                method: "call",
                params: {
                    args: p_args,
                    kwargs: p_kwargs,
                    method: p_method,
                    model: p_model
                }
            }).then(function (res) {
                if(res.data.error){
                    defered.reject(res.data.error);
                }
                else {
                    defered.resolve(res.data.result);
                }
            }).catch(function (err) {
                defered.reject(err);
            });
            return promise;
        },
        //llamada a la accion de un boton
        call_button: function (p_args, p_context_id, p_domain_id, p_method, p_model, p_funcion) {
            let defered = $q.defer();
            let promise = defered.promise;
            $http.post('/web/dataset/call_button', {
                method: "call",
                params: {
                    args: p_args,
                    context_id: p_context_id,
                    domain_id: p_domain_id,
                    method: p_method,
                    model: p_model
                }
            }).then(function (res) {
                p_funcion(res.data.result);
            });
        },
        //Busqueda de un objeto mediante domain's
        search_read: function (p_context, p_domain, p_fields, p_limit, p_model, p_offset, p_sort) {
            let defered = $q.defer();
            let promise = defered.promise;
            $http.post('/web/dataset/search_read', {
                method: "call",
                params: {
                    context: p_context,
                    domain: p_domain,
                    fields: p_fields,
                    limit: p_limit,
                    model: p_model,
                    offset: p_offset,
                    sort: p_sort
                }
            }).then(function (res) {
                if(res.data.error){
                    defered.reject(res.data.error);
                }
                else {
                    defered.resolve(res.data.result);
                }
            }).catch(function (err) {
                defered.reject(err);
            });
            return promise;
        },
        //convertir el array del name_search a una lista de objetos
        toListObject: function (p_list) {
            var list = [];
            for (var i = 0; i < p_list.length; i++) {
                list.push({
                    id: p_list[i][0],
                    name: p_list[i][1]
                });
            }
            return list;
        }
    }
};
},{}],9:[function(require,module,exports){
module.exports = function ($q, apiServerService) {
    return {
        //Devuelve el objeto mrpProduction
        GetMrpProduction: function (pid, pcontext) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([[pid], []], {context: pcontext}, 'read', 'mrp.production')
                .then(function (res) {
                    defered.resolve(res[0]);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Devuelve ordenes de produccion creadas para la lista de materiales
        GetBomProduction: function (pcontext, pdomain) {
            let defered = $q.defer();
            let promise = defered.promise;
            let fields = [
                "message_needaction",
                "name",
                "date_planned_start",
                "product_id",
                "product_qty",
                "product_uom_id",
                "availability",
                "routing_id",
                "origin",
                "state"
            ];
            apiServerService.search_read(pcontext,pdomain,fields,80,'mrp.production',0,'')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Devolver la lista de materiales a consumir en el mrpProduction
        GetMoveRaws: function (praw_ids, pcontext) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([praw_ids, []], {context: pcontext}, 'read', 'stock.move')
                .then(function (res) {
                    console.log(res);
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Devolver valores por defecto para la creacion de un mrpProduction
        GetDefaultValues: function (pcontext,pattributes) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([pattributes], {context: pcontext}, 'default_get', 'mrp.production')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        }
    }
};

},{}],10:[function(require,module,exports){
var apiServerService = require('./api_server.service');
var mrpProductionService = require('./mrp_production.service');

module.exports = angular.module('Services',[])
    .factory('apiServerService', apiServerService)
    .factory('mrpProductionService', mrpProductionService);
},{"./api_server.service":8,"./mrp_production.service":9}]},{},[1]);
