EMAIL_ANALYSIS_TOOL = {
    "name": "analyze_email",
    "description": "Analyse un email et retourne une évaluation complète avec catégorie, priorité, résumé et brouillon de réponse.",
    "input_schema": {
        "type": "object",
        "properties": {
            "email_id": {
                "type": "string",
                "description": "L'identifiant unique de l'email",
            },
            "category": {
                "type": "string",
                "enum": ["urgent", "important", "normal", "newsletter", "spam"],
                "description": "Catégorie de l'email",
            },
            "priority": {
                "type": "integer",
                "enum": [1, 2, 3, 4, 5],
                "description": "Niveau de priorité de 1 (négligeable) à 5 (critique)",
            },
            "sentiment": {
                "type": "string",
                "enum": ["positif", "neutre", "négatif", "urgent", "réclamation"],
                "description": "Sentiment général de l'email",
            },
            "summary": {
                "type": "string",
                "description": "Résumé en 1-2 phrases de ce dont parle l'email",
            },
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Points clés à retenir (max 3)",
            },
            "action_required": {
                "type": "boolean",
                "description": "Une action est-elle requise de la part du destinataire ?",
            },
            "action_description": {
                "type": "string",
                "description": "Description de l'action à effectuer si action_required est true",
            },
            "deadline": {
                "type": "string",
                "description": "Date limite si mentionnée ou implicite (format: YYYY-MM-DD ou description)",
            },
            "draft_reply": {
                "type": "string",
                "description": "Brouillon de réponse professionnel et adapté au contexte. Laisser null pour newsletters et spam.",
            },
        },
        "required": ["email_id", "category", "priority", "sentiment", "summary", "key_points", "action_required"],
    },
}

BRIEFING_TOOL = {
    "name": "generate_briefing",
    "description": "Génère le briefing exécutif quotidien de la boîte mail.",
    "input_schema": {
        "type": "object",
        "properties": {
            "executive_summary": {
                "type": "string",
                "description": "Résumé exécutif de la situation email du jour (3-5 phrases percutantes)",
            },
            "priority_list": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Liste ordonnée des actions prioritaires à mener aujourd'hui",
            },
            "alerts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Alertes ou points d'attention particuliers",
            },
        },
        "required": ["executive_summary", "priority_list", "alerts"],
    },
}
