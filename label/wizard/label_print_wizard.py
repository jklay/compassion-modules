# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Serpent Consulting Services Pvt. Ltd.
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import math

from openerp import fields, models, api, _


class label_print_wizard(models.TransientModel):

    _name = 'label.print.wizard'

    name = fields.Many2one(
        'label.config', _('Label Type'), required=True,
        default=lambda s: s.env.ref('label.label_4455')
    )
    number_of_labels = fields.Integer(_('Number of Labels (per item)'),
                                      required=True,
                                      default=33)
    labels_per_page = fields.Integer(_('Number of Labels per Pages'),
                                     compute="_compute_labels_per_page")
    brand_id = fields.Many2one(
        'label.brand', _('Brand Name'), required=True,
        default=lambda s: s.env.ref('label.herma4')
    )

    @api.model
    def default_get(self, fields):
        if self._context is None:
            self._context = {}
        result = super(label_print_wizard, self).default_get(fields)
        if self._context.get('label_print'):
            label_print_obj = self.env['label.print']
            label_print_data = label_print_obj.browse(
                self._context.get('label_print'))
            for field in label_print_data.sudo().field_ids:
                if field.type == 'barcode':
                    result['is_barcode'] = True
        return result

    @api.onchange('name')
    def _compute_labels_per_page(self):
        """
        Compute the number of labels per pages
        """
        for labels in self:
            if labels.name:
                rows = int((297-self.name.left_margin -
                            self.name.right_margin) /
                           (self.name.height or 1))
                columns = (float(210) / float(self.name.width or 1))
                self.labels_per_page = columns * rows

    @api.multi
    def get_report_data(self):
        if self._context is None or (not self._context.get('label_print') or
                                     not self._context.get('active_ids') or
                                     not self.name):
            return False

        column = (float(210) / float(self.name.width or 1))
        no_row_per_page = int((297-self.name.left_margin -
                               self.name.right_margin) /
                              (self.name.height or 1))

        label_print_obj = self.env['label.print']
        label_print_data = label_print_obj.browse(
            self._context.get('label_print'))

        ids = self.env.context['active_ids']
        rows_usable = int(math.ceil(float(math.ceil(
            self.number_of_labels*len(ids)) / int(column))))
        datas = {
            'rows': int(no_row_per_page),
            'columns': int(column),
            'rows_usable': rows_usable,
            'model': self._context.get('active_model'),
            'ids': ids,
            'padding_top': label_print_data.padding_top,
            'padding_bottom': label_print_data.padding_bottom,
            'padding_left': label_print_data.padding_left,
            'padding_right': label_print_data.padding_right,
            'barcode_width': label_print_data.barcode_width,
            'barcode_height': label_print_data.barcode_height,
            'dpi': self.env.ref('label.paperformat_label').dpi,
        }
        data = {
            'ids': self.ids,
            'model': 'label.config',
            'form': datas,
        }
        return data

    @api.multi
    def print_report(self):
        data = self.get_report_data()
        report_obj = self.env['report'].with_context(data['form'])
        return report_obj.get_action(self, 'label.report_label', data=data)
