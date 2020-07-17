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