from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_special = fields.Boolean(string="Special Order", default=False)

    def action_mark_special(self):
        for record in self:
            record.is_special = True
