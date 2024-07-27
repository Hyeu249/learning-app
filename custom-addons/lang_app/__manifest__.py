{
    "name": "Language App",
    "author": "Techno THT Gmbh",
    "website": "www.techno-tht.tech",
    "summary": "Language App",
    "depends": ["mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/role.xml",
        "security/rule.xml",
        "data/sequence.xml",
        "views/menu.xml",
        "views/index.xml",
        "views/vocabulary.xml",
        "views/completed_vocabulary.xml",
        "views/topic.xml",
        "reports/report.xml",
    ],
    "application": True,
    "assets": {
        "web.assets_backend": [
            "lang_app/static/src/css/my_css.css",
            "lang_app/static/src/js/audio_widget.js",
            "lang_app/static/src/js/home.js",
            "lang_app/static/src/js/components.js",
            "lang_app/static/src/xml/home.xml",
        ],
    },
}
