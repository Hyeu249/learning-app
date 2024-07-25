# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from odoo.addons.web_editor.tools import get_video_embed_code
from googletrans import Translator
from . import words
import random

translator = Translator()


class LearningApp(models.Model):
    _name = "learning.test"
    _description = "Learning test records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", required=True, tracking=True)
    description = fields.Char("Description", tracking=True)
    audio_url = fields.Char("Audio URL")
    translate_version = fields.Char("Translate version", tracking=True)
    progress = fields.Integer(string="Progress", compute="_set_progress")
    is_right = fields.Boolean(string="Is right")

    language = fields.Selection(
        CONST.LANGUAGES,
        string="Language",
        default=CONST.EN,
        required=True,
        tracking=True,
    )
    answer_number_1 = fields.Char("Answer number 1", compute="_get_answer_number_1")
    answer_number_2 = fields.Char("Answer number 2", compute="_get_answer_number_2")
    answer_number_3 = fields.Char("Answer number 3", compute="_get_answer_number_3")
    answer_number_4 = fields.Char("Answer number 4", compute="_get_answer_number_4")
    random_correct_answer = fields.Integer(
        "Random correct answer", compute="_get_random_value"
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.depends("is_right")
    def _set_progress(self):
        for record in self:
            records = self.search([])
            right_record = self.search([("is_right", "=", True)])
            total_records = len(records)
            right_len = len(right_record)

            record.progress = (right_len / total_records) * 100

    @api.depends("translate_version")
    def _get_random_value(self):
        for record in self:
            record.random_correct_answer = random.randint(1, 4)

    @api.depends("translate_version")
    def _get_answer_number_1(self):
        for record in self:
            if record.random_correct_answer == 1:
                record.answer_number_1 = record.translate_version
            else:
                record.answer_number_1 = random.choice(words.words)

    @api.depends("translate_version")
    def _get_answer_number_2(self):
        for record in self:
            if record.random_correct_answer == 2:
                record.answer_number_2 = record.translate_version
            else:
                record.answer_number_2 = random.choice(words.words)

    @api.depends("translate_version")
    def _get_answer_number_3(self):
        for record in self:
            if record.random_correct_answer == 3:
                record.answer_number_3 = record.translate_version
            else:
                record.answer_number_3 = random.choice(words.words)

    @api.depends("translate_version")
    def _get_answer_number_4(self):
        for record in self:
            if record.random_correct_answer == 4:
                record.answer_number_4 = record.translate_version
            else:
                record.answer_number_4 = random.choice(words.words)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(LearningApp, self).create(vals_list)

        for record in result:
            record.set_translate_version()

        return result

    def write(self, vals):
        self.ensure_one()
        old_name = self.name
        result = super(LearningApp, self).write(vals)
        new_name = self.name

        if old_name != new_name:
            if "name" in vals or "language" in vals:
                self.set_translate_version()

        return result

    def set_translate_version(self):
        self.ensure_one()
        translation = translator.translate(self.name, src=self.language, dest="vi")
        if translation:
            self.translate_version = translation.text

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def continue_record(self):
        self.ensure_one()
        return self.open_next_not_finished_record()

    def open_next_not_finished_record(self):
        self.ensure_one()
        ids = self.search([("is_right", "=", False)]).ids

        random_id = random.choice(ids)

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": random_id,
            "target": "current",
            "context": self.env.context,
        }

    def set_is_right(self, is_right):
        self.ensure_one()
        self.is_right = is_right

    def refresh_is_right(self):
        for record in self:
            record.is_right = False
