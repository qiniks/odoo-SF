from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_special_transfer = fields.Boolean(string="Is Special Transfer", default=False)

    def action_mark_as_special(self):
        for record in self:
            record.is_special_transfer = True
        return True
