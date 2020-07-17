app.controller('indexCtl', function ($scope, $http, $stateParams, peticion,mrpProductionService) {
    var production = $('#production').text();
    var contexto = $('#context').text();
    $scope.location_dest = {};
    $scope.location_src = {};

    function ReadProduction() {
        $scope.dataLoaded = false;
        peticion.ejecutar([[parseInt(production)], []], {context: JSON.parse(contexto)}, 'read', 'mrp.production', function (res) {
            $scope.mrp_production = res[0];
            $scope.main.titulo = $scope.mrp_production.name;
            peticion.ejecutar([$scope.mrp_production.move_raw_ids, []], {context: JSON.parse(contexto)}, 'read', 'stock.move', function (res) {
                var move_raw_ids = res.map(function(x){return x.id});
                //Obtener las operaciones de fabricacación ó transferancias para cada item de la lista de materiales
                peticion.search_read({context:JSON.parse(contexto)},
                [['move_dest_id','in',move_raw_ids]],
                ['name','product_id','product_uom_qty','product_uom','production_id'],false,'stock.move',0,'',function (res) {
                    console.log(res);
                    $scope.ops = res.records;
                });
                //--------------------------------------------------------------------------------------------------
                $scope.move_raw_ids = res;
                $scope.move_raw_ids.forEach(function (move) {
                    if (move.state === 'assigned')
                        move.class = 'list-group-item-success';
                });
                $scope.dataLoaded = true;
            });
            let domain = [
                ['origin','=',$scope.mrp_production.name+':'+$scope.mrp_production.name],
                ['state','!=','cancel']
            ];
            /*mrpProductionService.GetBomProduction(JSON.parse(contexto),domain)
                .then(function (res) {
                    $scope.ops = res.records;
                })
                .catch(function (err) {
                    alert(err.toString());
                });*/
        });
    }
    ReadProduction();

    $scope.ModalProducir = function (data) {
        let context = JSON.parse(contexto);
        $scope.moveProduce = data;
        context.default_product_id = data.product_id[0];
        context.default_product_qty = data.product_uom_qty;
        let kwargs = {
            args: ['&', '|', ['product_id', '=', data.product_id[0]], ["product_tmpl_id.product_variant_ids", "=", data.product_id[0]], ['type', '=', 'normal']],
            context: context,
            limit: 0,
            name: '',
            operator: 'ilike'
        };
        let kwargsPicking = {
            args: [],
            context: context,
            limit: 0,
            name: '',
            operator: 'ilike'
        };
        //Obtenemos los campos del formulario
        mrpProductionService.FieldsViewGet(JSON.parse(contexto),'form')
            .then(function (res) {
                //Obtenemos los valores por defecto del mrp.production
                mrpProductionService.DefaultGet(context,res.fields)
                    .then(function (res) {
                        $scope.production = res;
                        $scope.production.product_uom_id = data.product_uom;
                        mrpProductionService.GetBom(kwargs)
                            .then(function (res) {
                                $scope.production.bom_id = res[0];
                                $scope.bom_ids = res;
                            });
                        mrpProductionService.ListPickingType(kwargsPicking)
                            .then(function (res) {
                                $scope.production.picking_type_id = res.find(function (p_i) {
                                    return p_i[0] == $scope.production.picking_type_id[0];
                                });
                                $scope.picking_type_ids = res;
                            })
                    })
                    .catch(function (err) {
                        alert(err.toString());
                    })
            })
            .catch(function (err) {
                alert(err.toString());
            });
        /*$scope.production = {};
        $scope.production.move_raws = [];
        $scope.production.name = 'Nuevo';
        $scope.production.product_id = data.product_id;
        $scope.production.product_uom_id = data.product_uom;
        $scope.production.product_qty = data.product_uom_qty;
        $scope.bom_ids = [];
        $scope.production.bom_id = [];
        $scope.stock_move = data;
        var kwargs = {
            args: ['&', '|', ['product_id', '=', $scope.stock_move.product_id[0]], ["product_tmpl_id.product_variant_ids", "=", $scope.stock_move.product_id[0]], ['type', '=', 'normal']],
            context: JSON.parse(contexto),
            limit: 0,
            name: '',
            operator: 'ilike'
        };
        //Obtenemos los valores por defecto del mrp.production
        peticion.ejecutar([], {context: JSON.parse(contexto)}, 'fields_get', 'mrp.production', function (res) {
            attributes = [];
            for (var prop in res) {
                attributes.push(prop);
            }
            peticion.ejecutar([attributes], {context: JSON.parse(contexto)}, 'default_get', 'mrp.production', function (res) {
                for (i in res) {
                    if ($scope.production[i] === undefined)
                        $scope.production[i] = res[i];
                }
            });
        });
        peticion.ejecutar([], kwargs, 'name_search', 'mrp.bom', function (res) {
            $scope.production.bom_id = res[0];
            $scope.bom_ids = res;
            $scope.bom_ids.push([$scope.bom_ids.length, 'PERSONALIZADO']);
        });*/
    };

    function generar_valores(funcion) {
        var values;
        peticion.ejecutar([], {context: JSON.parse(contexto)}, 'fields_get', 'mrp.production', function (res) {
            attributes = [];
            for (var prop in res) {
                attributes.push(prop);
            }
            peticion.ejecutar([attributes], {context: JSON.parse(contexto)}, 'default_get', 'mrp.production', function (res) {
                values = res;
                peticion.ejecutar([[$scope.stock_move.product_id[0]], []], {context: JSON.parse(contexto)}, 'read', 'product.product', function (res) {
                    $scope.stock_move.producto = res[0];
                    values.bom_id = $scope.stock_move.producto.bom_ids[0];
                    peticion.ejecutar([[values.picking_type_id], []], {context: JSON.parse(contexto)}, 'read', 'stock.picking.type', function (res) {
                        $scope.stock_move.stock_picking_type = res[0];
                        values.location_src_id = $scope.stock_move.stock_picking_type.default_location_src_id[0];
                        values.location_dest_id = $scope.stock_move.stock_picking_type.default_location_dest_id[0];
                        values.product_id = $scope.stock_move.product_id[0];
                        values.product_qty = $scope.stock_move.product_uom_qty;
                        values.product_uom_id = $scope.stock_move.product_uom[0];
                        values.origin = $scope.mrp_production.name;
                        funcion(values);
                    });
                });
            });
        });
    }

    $scope.CrearProduccion = function () {
        $scope.dataLoaded = false;
        $scope.production.origin = $scope.mrp_production.name+':'+$scope.mrp_production.name;
        let values = GetIds($scope.production);
        let move = GetIds($scope.moveProduce);
        mrpProductionService.CreateMrpFromMove([[$scope.moveProduce.id],values],contexto)
            .then(res => {
                let idProduction = res;
                mrpProductionService.ActionAssign(res,contexto)
                    .then(res => {
                        mrpProductionService.GetMrpProduction(idProduction,JSON.parse(contexto))
                            .then(res => {
                                $scope.production = res;
                                $scope.ops.push(res);
                                //$scope.moveProduce.product_uom_qty = ($scope.moveProduce.product_uom_qty+$scope.production.product_qty).toFixed(2);
                                mrpProductionService.GetMoveRaws($scope.production.move_raw_ids,contexto)
                                    .then(res => {
                                        $scope.production.move_raws = res;
                                        $scope.dataLoaded = true;
                                    })
                            })
                    })
            })
            .catch(function (err) {
                $scope.dataLoaded = true;
                alert(err.toString());
            });
    };
    $scope.MarcarHecho = function () {
        /*$scope.dataLoaded = false;
        peticion.call_button([[$scope.production.id], JSON.parse(contexto)], 1, '', 'button_mark_done', 'mrp.production', function (res) {
            peticion.call_button([[parseInt(production)], JSON.parse(contexto)], 1, '', 'action_assign', 'mrp.production', function (res) {
                ReadProduction();
            });
        });*/
        $scope.dataLoaded = false;
        mrpProductionService.MarkDone($scope.production.id,contexto)
            .then(function (res) {
                $scope.production.state = 'done';
                ReadProduction();
                $scope.dataLoaded = true;
            })
            .catch(function (err) {
                alert(err.toString());
            });
    };
    $scope.ModalTransferir = function (data) {
        $scope.stock_move = data;
        $scope.mrp_transferencia = {};
        $scope.mrp_transferencia.product_id = data.product_id;
        $scope.mrp_transferencia.product_uom_qty = data.product_uom_qty;
        $scope.mrp_transferencia.product_uom = data.product_uom;
        $scope.mrp_transferencia.origin = $scope.mrp_production.name;
        $scope.mrp_transferencia.motivo = 'abastecimiento';
        $scope.DropDown(function () {
            $scope.ChangeMotivo();
        });
    };
    $scope.DropDown = function (ejecutar) {
        kwargs = {};
        kwargs.name = "";
        kwargs.operator = 'ilike';
        kwargs.limit = 0;
        kwargs.args = [];
        kwargs.context = JSON.parse(contexto);
        peticion.ejecutar([], kwargs, 'name_search', 'stock.location', function (data) {
            locations = [];
            data.forEach(function (res) {
                locations.push({id: res[0], name: res[1]});
            });
            $scope.locations = locations;
            ejecutar();
        })
    };
    $scope.ChangeMotivo = function () {
        if ($scope.mrp_transferencia.motivo === 'abastecimiento' || $scope.mrp_transferencia.motivo === 'adicionar') {
            $scope.mrp_transferencia.location_dest_id = {
                id: $scope.stock_move.location_id[0],
                name: $scope.stock_move.location_id[1]
            };
            $scope.mrp_transferencia.location_id = undefined;
        } else {
            $scope.mrp_transferencia.location_id = {
                id: $scope.stock_move.location_id[0],
                name: $scope.stock_move.location_id[1]
            };
            $scope.mrp_transferencia.location_dest_id = undefined;
        }
    };
    $scope.RealizarTransferencia = function () {
        let values = GetIds($scope.mrp_transferencia);
        values.name = values.origin;
        mrpProductionService.TransferQuantity([[$scope.stock_move.id],values],contexto)
            .then((res)=>{
                ReadProduction();
            })
            .catch((err)=>{
                alert(err.toString());
            })
    };
    $scope.AgregarMaterial = function () {
        var kwargs = {
            args: [["type", "in", ["product", "consu"]]],
            context: JSON.parse(contexto),
            limit: 0,
            name: '',
            operator: 'ilike'
        };
        peticion.ejecutar([], kwargs, 'name_search', 'product.product', function (res) {
            $scope.product_ids = peticion.toListObject(res);
            $scope.move_raw = {};
        });
        kwargs.args = [];
        peticion.ejecutar([], kwargs, 'name_search', 'product.uom', function (res) {
            $scope.product_uom_ids = peticion.toListObject(res);
        });
        $scope.agregar_material = true;
    };

    function GetSubtotal(list) {
        var sum = 0;
        for (var i = 0; i < list.length; i++) {
            list[i].subtotal = sum + parseFloat(list[i].product_uom_qty);
            sum = list[i].subtotal;
        }
        return list
    }

    $scope.AddMoveRaw = function () {
        $scope.production.move_raws.push($scope.move_raw);
        $scope.move_raw = {};
        $scope.agregar_material = true;
        GetSubtotal($scope.production.move_raws);
    };
    $scope.CancelMoveRaw = function () {
        $scope.agregar_material = false;
        $scope.move_raw = {};
    };
    $scope.DeleteMoveRaw = function (move) {
        var i = $scope.production.move_raws.indexOf(move);
        $scope.production.move_raws.splice(i, 1);
        GetSubtotal($scope.production.move_raws);
    };

    //Obtener los ids de un array o de un objeto para enviarlos al metodo create de python
    function GetIds(p_obj) {
        var values = {};
        //recorremos por las propiedades del objeto
        for (var i in p_obj) {
            if (Array.isArray(p_obj[i])) {
                for (j in p_obj[i]) {
                    if (typeof p_obj[i][j] !== 'object') {
                        values[i] = p_obj[i][0];
                    }
                    else {
                        if (values[i] === undefined) {
                            values[i] = [];
                            values[i].push(GetIds(p_obj[i][j]));
                        }
                        else values[i].push(GetIds(p_obj[i][j]));
                    }
                }
            }
            else if (typeof p_obj[i] === 'object') {
                values[i] = p_obj[i].id;
            }
            else {
                values[i] = p_obj[i];
            }
        }
        return values;
    }

    $scope.DoneCustomProduction = function () {
        var values = GetIds($scope.production);
        values.bom_id = $scope.production.bom_id[1];
        peticion.ejecutar([values], {context: JSON.parse(contexto)}, 'create', 'mrp.production', function (res) {
            console.log(res);
        });
        console.log($scope.production);
    };
    
    //FUNCION QUE RETORNA UNA OP SELECCIONADA
    $scope.GetOp = function (op) {
        if (op.production_id){
            $('#myModal').modal('show');
        $scope.production = op;
        peticion.ejecutar([[op.production_id[0]],[]],{context:JSON.parse(contexto)},'read','mrp.production',function (res) {
            $scope.production = res[0]
            mrpProductionService.GetMoveRaws($scope.production.move_raw_ids,contexto)
            .then(function (res) {
                $scope.production.move_raws = res;
            })
            .catch(function (err) {
                alert(err.toString());
            })
        });}
    };

    $scope.ChangePicking = function () {
        mrpProductionService.GetPickingType([[$scope.production.picking_type_id[0]],['default_location_src_id','default_location_dest_id']],contexto)
            .then(function (res) {
                $scope.production.location_src_id = res.default_location_src_id;
                $scope.production.location_dest_id = res.default_location_dest_id;
            })
            .catch(function (err) {
                alert(err.toString());
            })
    };
    $scope.ActionAssign = () => {
        mrpProductionService.ActionAssign($scope.production.id,contexto)
            .then(res => {
                $scope.ReloadModalProduction();
            })
            .catch(err => {
                alert(err.toString());
            })
    };
    $scope.ReloadModalProduction = () => {
        $scope.dataLoaded = false;
        mrpProductionService.GetMrpProduction($scope.production.id,JSON.parse(contexto))
            .then(res => {
                $scope.production = res;
                mrpProductionService.GetMoveRaws($scope.production.move_raw_ids,contexto)
                    .then(res => {
                        console.log(res);
                        $scope.production.move_raws = res;
                        $scope.dataLoaded = true;
                    })
            })
            .catch(err => {
                alert(err.toString());
            })
    };
});
