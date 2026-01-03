from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Suggestion(models.Model):
    _name = 'gestion.suggestion'
    _description = 'Suggestion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_creation desc'

    # Champs de base
    name = fields.Char(
        string='Titre',
        required=True,
        tracking=True,
        help="Titre court de la suggestion"
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        tracking=True,
        help="Description détaillée de la suggestion"
    )
    
    # Champs relationnels
    auteur_id = fields.Many2one(
        'res.users',
        string='Auteur',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        readonly=True
    )
    
    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        help="Personne responsable de traiter la suggestion"
    )
    
    # Champs de dates
    date_creation = fields.Date(
        string='Date de création',
        default=fields.Date.today,
        required=True,
        readonly=True
    )
    
    date_traitement = fields.Date(
        string='Date de traitement',
        tracking=True,
        help="Date à laquelle la suggestion a été traitée"
    )
    
    # Champs de statut
    state = fields.Selection([
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('en_cours', 'En cours d\'analyse'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
        ('realise', 'Réalisé')
    ], string='État', default='brouillon', required=True, tracking=True)
    
    priorite = fields.Selection([
        ('faible', 'Faible'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente')
    ], string='Priorité', default='moyenne', tracking=True)
    
    categorie = fields.Selection([
        ('amelioration', 'Amélioration'),
        ('innovation', 'Innovation'),
        ('probleme', 'Résolution de problème'),
        ('economie', 'Économie'),
        ('qualite', 'Qualité'),
        ('securite', 'Sécurité'),
        ('autre', 'Autre')
    ], string='Catégorie', required=True, tracking=True)
    
    # Champs additionnels
    commentaire = fields.Text(
        string='Commentaire de traitement',
        tracking=True,
        help="Commentaires sur la décision prise"
    )
    
    benefice_estime = fields.Text(
        string='Bénéfice estimé',
        help="Estimation des bénéfices potentiels"
    )
    
    cout_estime = fields.Float(
        string='Coût estimé',
        help="Coût estimé de mise en œuvre"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Champs calculés
    duree_traitement = fields.Integer(
        string='Durée de traitement (jours)',
        compute='_compute_duree_traitement',
        store=True
    )
    
    @api.depends('date_creation', 'date_traitement')
    def _compute_duree_traitement(self):
        """Calcule la durée entre la création et le traitement"""
        for record in self:
            if record.date_traitement and record.date_creation:
                delta = record.date_traitement - record.date_creation
                record.duree_traitement = delta.days
            else:
                record.duree_traitement = 0
    
    # Contraintes
    @api.constrains('cout_estime')
    def _check_cout_estime(self):
        """Vérifie que le coût estimé n'est pas négatif"""
        for record in self:
            if record.cout_estime < 0:
                raise ValidationError("Le coût estimé ne peut pas être négatif.")
    
    @api.constrains('date_traitement', 'date_creation')
    def _check_dates(self):
        """Vérifie que la date de traitement est après la date de création"""
        for record in self:
            if record.date_traitement and record.date_creation:
                if record.date_traitement < record.date_creation:
                    raise ValidationError(
                        "La date de traitement ne peut pas être antérieure à la date de création."
                    )
    
    # Méthodes d'action
    def action_soumettre(self):
        """Soumet la suggestion pour analyse"""
        for record in self:
            if not record.description:
                raise ValidationError("Veuillez remplir la description avant de soumettre.")
            record.write({'state': 'soumis'})
        return True
    
    def action_analyser(self):
        """Met la suggestion en cours d'analyse"""
        self.write({'state': 'en_cours'})
        return True
    
    def action_accepter(self):
        """Accepte la suggestion"""
        for record in self:
            if not record.responsable_id:
                raise ValidationError("Veuillez assigner un responsable avant d'accepter.")
            record.write({
                'state': 'accepte',
                'date_traitement': fields.Date.today()
            })
        return True
    
    def action_refuser(self):
        """Refuse la suggestion"""
        for record in self:
            if not record.commentaire:
                raise ValidationError("Veuillez indiquer la raison du refus dans les commentaires.")
            record.write({
                'state': 'refuse',
                'date_traitement': fields.Date.today()
            })
        return True
    
    def action_realiser(self):
        """Marque la suggestion comme réalisée"""
        self.write({'state': 'realise'})
        return True
    
    def action_retour_brouillon(self):
        """Remet la suggestion en brouillon"""
        self.write({
            'state': 'brouillon',
            'date_traitement': False
        })
        return True
    
    # Méthodes de notification
    @api.model
    def create(self, vals):
        """Surcharge la création pour envoyer une notification"""
        record = super(Suggestion, self).create(vals)
        # Notification lors de la création
        record.message_post(
            body=f"Nouvelle suggestion créée par {record.auteur_id.name}",
            subject="Nouvelle suggestion"
        )
        return record
    
    def write(self, vals):
        """Surcharge l'écriture pour suivre les changements d'état"""
        # Notification en cas de changement de responsable
        if 'responsable_id' in vals and vals['responsable_id']:
            responsable = self.env['res.users'].browse(vals['responsable_id'])
            for record in self:
                record.message_post(
                    body=f"Assigné à {responsable.name}",
                    subject="Nouvelle assignation",
                    partner_ids=[responsable.partner_id.id]
                )
        
        # Notification en cas d'acceptation
        if 'state' in vals and vals['state'] == 'accepte':
            for record in self:
                record.message_post(
                    body=f"Suggestion acceptée",
                    subject="Suggestion acceptée",
                    partner_ids=[record.auteur_id.partner_id.id]
                )
        
        # Notification en cas de refus
        if 'state' in vals and vals['state'] == 'refuse':
            for record in self:
                record.message_post(
                    body=f"Suggestion refusée",
                    subject="Suggestion refusée",
                    partner_ids=[record.auteur_id.partner_id.id]
                )
        
        return super(Suggestion, self).write(vals)
    
    # Méthode pour formater le nom complet
    def name_get(self):
        """Affiche le nom avec l'état"""
        result = []
        for record in self:
            name = f"[{record.state.upper()}] {record.name}"
            result.append((record.id, name))
        return result
    
    # Recherche personnalisée
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par titre ou auteur"""
        args = args or []
        if name:
            args = ['|', ('name', operator, name), ('auteur_id.name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    
    # Méthodes statistiques
    def action_view_statistics(self):
        """Ouvre une vue avec les statistiques des suggestions"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Statistiques des Suggestions',
            'res_model': 'gestion.suggestion',
            'view_mode': 'graph,pivot',
            'domain': [('id', 'in', self.ids)],
            'context': {'group_by': ['state', 'categorie']}
        }