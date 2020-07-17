from odoo import api, fields, models
from odoo.exceptions import UserError

class PedidoLine(models.TransientModel):
    _name = "pedido.line.wizard"
    _description = "Lanza una ventana para agregar detalles de pedido"

    pedido_id = fields.Many2one('mrp.pedido.produccion', 'Pedido de Produccion', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product',string='Producto',required=True)
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    product_uom_id = fields.Many2one('product.uom')
    product_uom_qty = fields.Integer('Cantidad',required=True)

    @api.multi
    def add_detail(self):
        self.ensure_one()
        if not self.product_id.bom_ids:
            raise UserError('No se configuro una lista de materiales para este producto')
        bom = self.product_id.bom_ids[0]
        bom_line = bom.bom_line_ids.filtered(lambda x: x.product_id.bases_x_carro and x.product_id.max_carros)
        if bom_line:
            base = bom_line.mapped('product_id')
            bases_x_carro = base.bases_x_carro
            max_carros = base.max_carros
            pz_x_base = bom.product_qty / bom_line.product_qty
            if bases_x_carro and max_carros:
                num_pzs,carros = self._get_num_pzs(bases_x_carro,pz_x_base,self.product_uom_qty)
                self._create_pedido_line(max_carros,carros,num_pzs)
        else:
            self.env['mrp.pedido.line'].create(self._prepare_datos(self.product_uom_qty))
        return True

    def _get_num_pzs(self,p_bases_x_carro,p_pz_x_base,p_product_qty):
        bases = p_product_qty / float(p_pz_x_base)
        a = bases - int(bases)
        bases = int(bases)
        if a >= 0.33:
            bases += 1
        carros = bases / float(p_bases_x_carro)
        b = carros - int(carros)
        carros = int(carros)
        if b >= 0.33:
            carros += 1
        num_piezas = carros * p_bases_x_carro * p_pz_x_base
        return num_piezas,carros

    def _create_pedido_line(self, p_max_carros,p_carros,p_num_pzs):
        pedido_line = self.env['mrp.pedido.line']
        min = p_max_carros
        max = (min - 1)*2
        carros = p_carros
        piezas = p_num_pzs
        piezas_x_carro = piezas / carros
        if carros <= min:
            pedido_line.create(self._prepare_datos(piezas))
        else:
            while carros>=min:
                if carros>min and carros<=max:
                    temp = int(carros/2)
                    pzs = temp * piezas_x_carro
                    pedido_line.create(self._prepare_datos(pzs))
                    temp += carros%2
                    pzs = temp * piezas_x_carro
                    pedido_line.create(self._prepare_datos(pzs))
                    carros = 0
                else:
                    carros = carros - min
                    pzs = min * piezas_x_carro
                    pedido_line.create(self._prepare_datos(pzs))
            if carros > 0 and carros <= min:
                pzs = carros * piezas_x_carro
                pedido_line.create(self._prepare_datos(pzs))

    def _prepare_datos(self,p_num_pzs):
        return {
            'location_dest_id': self.location_dest_id.id or '',
            'num_piezas': p_num_pzs,
            'product_id': self.product_id.id,
            'pedido_id': self.pedido_id.id
        }