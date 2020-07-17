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