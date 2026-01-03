{
    "name": "TP - Gestion des Suggestions",
    "version": "1.0",
    "summary": "Module pour gérer les suggestions",
    "category": "Tools",
    "author": "EMSI",
    "depends": ["base", "mail"],  # ← Ajoutez "mail" ici
    "data": [
        "security/ir.model.access.csv",
        "views/suggestion_views.xml",
        "views/menu_views.xml",  # ← Ajoutez aussi cette ligne si vous avez ce fichier
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",  # ← Ajoutez cette ligne pour éviter le warning
}