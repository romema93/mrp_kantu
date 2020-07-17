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
