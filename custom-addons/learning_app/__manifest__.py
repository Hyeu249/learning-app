{
    "name": "Learning App",
    "author": "Techno THT Gmbh",
    "website": "www.techno-tht.tech",
    "summary": "Learning App",
    "depends": ["mail", "website"],
    "data": [
        "security/ir.model.access.csv",
        "security/role.xml",
        "security/rule.xml",
        "data/sequence.xml",
        "views/menu.xml",
        "views/index.xml",
        "reports/report.xml",
    ],
    "application": True,
    "assets": {
        "web.assets_backend": [
            "learning_app/static/src/css/my_css.css",
            "learning_app/static/src/js/audio_widget.js",
        ],
    },
}
