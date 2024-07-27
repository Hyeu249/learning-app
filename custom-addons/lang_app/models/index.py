# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from odoo.addons.web_editor.tools import get_video_embed_code
from googletrans import Translator
from gtts import gTTS
from . import words
import random
import os
import subprocess

translator = Translator()


class LearningApp(models.Model):
    _name = "lang.app.learning"
    _description = "Language app learning records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", required=True, tracking=True)
    description = fields.Char("Description", tracking=True)
    continue_button = fields.Char("Continue", default="Continue", tracking=True)

    # related
    vocabulary_name = fields.Char("Vocabulary name", related="vocabulary_id.name")
    audio_url = fields.Char("Audio URL", related="vocabulary_id.audio_url")
    translate_version = fields.Char(
        "Translate version", related="vocabulary_id.translate_version"
    )

    # compute
    progress = fields.Integer(string="Progress", compute="_set_progress")

    answer_number_1 = fields.Char(
        "Answer number 1", compute="_get_answer_number_1", store=True
    )
    answer_number_2 = fields.Char(
        "Answer number 2", compute="_get_answer_number_2", store=True
    )
    answer_number_3 = fields.Char(
        "Answer number 3", compute="_get_answer_number_3", store=True
    )
    answer_number_4 = fields.Char(
        "Answer number 4", compute="_get_answer_number_4", store=True
    )
    random_correct_answer = fields.Integer(
        "Random correct answer", compute="_get_random_value", store=True
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    topic_id = fields.Many2one("lang.app.topic", string="Topic")
    vocabulary_id = fields.Many2one("lang.app.vocabulary", string="Vocabulary")
    vocabulary_ids = fields.Many2many("lang.app.vocabulary", string="Vocabulary")

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.depends("vocabulary_ids")
    def _set_progress(self):
        for record in self:
            records = self.vocabulary_ids
            right_record = self.vocabulary_ids.filtered(lambda e: e.is_completed)
            total_records = len(records)
            right_len = len(right_record)

            if total_records:
                record.progress = (right_len / total_records) * 100
            else:
                record.progress = 0

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
                record.answer_number_1 = self.get_random_answer()

    @api.depends("translate_version")
    def _get_answer_number_2(self):
        for record in self:
            if record.random_correct_answer == 2:
                record.answer_number_2 = record.translate_version
            else:
                record.answer_number_2 = self.get_random_answer()

    @api.depends("translate_version")
    def _get_answer_number_3(self):
        for record in self:
            if record.random_correct_answer == 3:
                record.answer_number_3 = record.translate_version
            else:
                record.answer_number_3 = self.get_random_answer()

    @api.depends("translate_version")
    def _get_answer_number_4(self):
        for record in self:
            if record.random_correct_answer == 4:
                record.answer_number_4 = record.translate_version
            else:
                record.answer_number_4 = self.get_random_answer()

    @api.model_create_multi
    def create(self, vals_list):
        result = super(LearningApp, self).create(vals_list)
        return result

    def write(self, vals):
        self.ensure_one()
        result = super(LearningApp, self).write(vals)

        if "vocabulary_ids" in vals and not self.vocabulary_id:
            self.set_default_vocabulary_id()

        return result

    def set_default_vocabulary_id(self):
        self.ensure_one()
        self.vocabulary_id = self.vocabulary_ids[0]

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def continue_vocabulary(self):
        self.ensure_one()
        return self.open_next_not_finished_vocabulary()

    def open_next_not_finished_vocabulary(self):
        self.ensure_one()
        records = self.vocabulary_ids.filtered(
            lambda e: not e.is_completed and e.id != self.vocabulary_id.id
        )

        if records:
            random_id = random.choice(records)
            self.vocabulary_id = random_id
        else:
            raise ValidationError("Bạn đã xem qua hết các từ vựng cần học")

    def set_is_completed(self, is_completed):
        self.ensure_one()
        self.vocabulary_id.set_is_completed(is_completed)

    def refresh_is_completed(self):
        for record in self:
            for record_id in record.vocabulary_ids:
                record_id.set_is_completed(False)

    def get_random_answer(self):
        self.ensure_one()
        old_answers = self.get_old_answers()
        new_answers = [item for item in words.words if item not in old_answers]
        new_answer = random.choice(new_answers)

        return new_answer

    def get_old_answers(self):
        self.ensure_one()
        return [
            self.answer_number_1,
            self.answer_number_2,
            self.answer_number_3,
            self.answer_number_4,
        ]


class Topic(models.Model):
    _name = "lang.app.topic"
    _description = "Lang app topic records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    learning_ids = fields.One2many("lang.app.learning", "topic_id", string="Learning")

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        result = super(Topic, self).create(vals_list)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(Topic, self).write(vals)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result


class Vocabulary(models.Model):
    _name = "lang.app.vocabulary"
    _description = "Lang app vocabulary records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", required=True, tracking=True)
    description = fields.Char("Description", tracking=True)
    audio_url = fields.Char("Audio URL", tracking=True)
    translate_version = fields.Char("Translate version", tracking=True)

    language = fields.Selection(
        CONST.LANGUAGES,
        string="Language",
        default=CONST.EN,
        required=True,
        tracking=True,
    )

    # compute
    is_completed = fields.Boolean(
        "Is completed", compute="get_is_completed", tracking=True
    )

    @api.depends("complete_ids")
    def get_is_completed(self):
        for record in self:
            complete_id = record.complete_ids.filtered(
                lambda e: e.user_id == self.env.user and e.vocabulary_id == record
            )

            record.is_completed = complete_id.is_completed

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    learning_ids = fields.Many2many("lang.app.learning", string="Genre")
    complete_ids = fields.One2many(
        "lang.app.completed.vocabulary", "vocabulary_id", string="Genre"
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        result = super(Vocabulary, self).create(vals_list)

        for record in result:
            record.set_translate_version()

        return result

    def write(self, vals):
        self.ensure_one()
        old_name = self.name
        result = super(Vocabulary, self).write(vals)
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

    def save_audio_url(self):
        for record in self:
            if record.name and not record.audio_url:
                tts = gTTS(text=record.name, lang=record.language)
                destiny_path, module_path = record.get_paths()
                file_name = record.name + ".mp3"

                file_path = os.path.join(destiny_path, file_name)
                audio_url = os.path.join(module_path, file_name)

                tts.save(file_path)
                record.audio_url = audio_url

    def speak(self):
        self.ensure_one()
        path = "/base/static"
        raise ValidationError(f"{os.path.exists(path)}")

    def get_paths(self):
        self.ensure_one()
        app_path = "/mnt/extra-addons/"
        module_path = "lang_app/static/src/audio"
        destiny_path = app_path + module_path

        return destiny_path, module_path

    def check_save(self):
        self.ensure_one()
        app_path = "/mnt/extra-addons/"
        module_path = "lang_app/static/src/audio"
        path = app_path + module_path

        command = ["ls", path]
        can_read = os.access(path, os.R_OK)
        can_write = os.access(path, os.W_OK)
        can_execute = os.access(path, os.X_OK)
        result = subprocess.run(command, capture_output=True, text=True)

        raise ValidationError(
            f"{can_read}-{can_write}-{can_execute}-{result}-{os.path.exists(path)}"
        )

    def set_is_completed(self, is_completed):
        self.ensure_one()
        complete_id = self.find_or_create_completed_vocabulary()
        complete_id.is_completed = is_completed

    def find_or_create_completed_vocabulary(self):
        self.ensure_one()
        complete_id = self.complete_ids.search(
            [
                ("vocabulary_id", "=", self.id),
                ("user_id", "=", self.env.user.id),
            ]
        )

        if complete_id:
            return complete_id
        else:
            return self.complete_ids.create(
                {
                    "vocabulary_id": self.id,
                    "user_id": self.env.user.id,
                }
            )


class CompletedVocabulary(models.Model):
    _name = "lang.app.completed.vocabulary"
    _description = "Lang app completed vocabulary records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    is_completed = fields.Boolean("Is completed", tracking=True)

    # related
    name = fields.Char("Name", related="vocabulary_id.name", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    user_id = fields.Many2one("res.users", string="User")
    vocabulary_id = fields.Many2one("lang.app.vocabulary", string="Vocabulary")

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.constrains("user_id", "vocabulary_id")
    def _unique_user(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("user_id", "=", record.user_id.id),
                    ("vocabulary_id", "=", record.vocabulary_id.id),
                ]
            )
            message = "Trùng người dùng ở hoàn thành từ vựng!"
            if duplicate:
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(CompletedVocabulary, self).create(vals_list)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(CompletedVocabulary, self).write(vals)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
