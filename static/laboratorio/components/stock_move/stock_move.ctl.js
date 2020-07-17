module.exports = function () {
    let vm = this;
    this.$onInit = function() {

    };
    vm.SelectMove = function () {
        vm.moveselected = vm.move;
    }
};