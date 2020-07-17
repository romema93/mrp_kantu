app.factory('mrpProductionService', function ($q, apiServerService) {
    return {
        //Obtiene los campos de una vista determinada
        FieldsViewGet: function (p_context, p_viewType) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([],{context:p_context,toolbar:false,view_type:p_viewType},'fields_view_get','mrp.production')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Obtiene valores por defecto
        DefaultGet: function (p_context,p_fields) {
            let defered = $q.defer();
            let promise = defered.promise;
            let attributes = [];
            let fields = p_fields;
            for (let prop in p_fields) {
                attributes.push(prop);
            }
            apiServerService.call_kw([p_fields],{context:p_context},'default_get','mrp.production')
                .then(function (res) {
                    let data = res;
                    for (let prop in res){
                        if(fields[prop].type == 'many2one'){
                            apiServerService.call_kw([[res[prop]]],{context:p_context},'name_get',fields[prop].relation)
                                .then(function (res) {
                                    data[prop] = res[0];
                                })
                                .catch(function (err) {
                                    alert(err);
                                })
                        }
                    }
                    defered.resolve(data);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
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
                "state",
                'move_raw_ids',
                "bom_id"
            ];
            apiServerService.search_read(pcontext, pdomain, fields, 80, 'mrp.production', 0, '')
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
        GetDefaultValues: function (pcontext, pattributes) {
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
        },
        //Obtener los stock.move de una op
        GetMoveRaws: function (p_move_raw_ids, p_context) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([p_move_raw_ids, []], {context: JSON.parse(p_context)}, 'read', 'stock.move')
                .then(function (res) {
                    let sum = 0;
                    for (var i = 0; i < res.length; i++) {
                        res[i].subtotal = (sum + res[i].product_uom_qty).toFixed(2);
                        sum = parseFloat(res[i].subtotal);
                    }
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Marcar como hecho una OP
        MarkDone: function (p_id,p_context) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_button([[p_id], JSON.parse(p_context)], 1, '', 'button_mark_done', 'mrp.production')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Obtener la bom de un producto
        GetBom:function (p_kwargs) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([], p_kwargs, 'name_search', 'mrp.bom')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        //Obtener los stock.picking.typr
        ListPickingType:function (p_kwargs) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw([], p_kwargs, 'name_search', 'stock.picking.type')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        GetPickingType:function (p_args, p_context) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw(p_args, {context:JSON.parse(p_context)}, 'read', 'stock.picking.type')
                .then(function (res) {
                    defered.resolve(res[0]);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        },
        CreateMrpFromMove: function (p_args, p_context) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw(p_args,{context:JSON.parse(p_context)},'CreateMrpFromMove','stock.move')
                .then(function (res) {
                    defered.resolve(res)
                })
                .catch(function (err) {
                    defered.reject(err)
                });
            return promise;
        },
        TransferQuantity: function (p_args, p_context) {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_kw(p_args,{context:JSON.parse(p_context)},'TransferQuantity','stock.move')
                .then(function (res) {
                    defered.resolve(res)
                })
                .catch(function (err) {
                    defered.reject(err)
                });
            return promise;
        },
        /*
        Comprueba la disponibilidad de la lista de materiales
         */
        ActionAssign: (p_id,p_context) => {
            let defered = $q.defer();
            let promise = defered.promise;
            apiServerService.call_button([[p_id], JSON.parse(p_context)], 1, '', 'action_assign', 'mrp.production')
                .then(function (res) {
                    defered.resolve(res);
                })
                .catch(function (err) {
                    defered.reject(err);
                });
            return promise;
        }
    }
});