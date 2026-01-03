from odoo import models, fields

class TpProjet(models.Model):
    _name = "tp.projet"
    _description = "Projet TP"

    name = fields.Char(string="Nom du projet", required=True)
    responsable = fields.Char(string="Responsable")
    date_debut = fields.Date(string="Date de début")
    statut = fields.Selection([
        ("brouillon", "Brouillon"),
        ("en cours", "En cours"),
        ("termine", "Terminé"),
    ], string="Statut", default="brouillon")
    description = fields.Text(string="Description")