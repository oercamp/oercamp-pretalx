document.addEventListener('DOMContentLoaded', () => {

    function tm_getSponsorCardContent(
        logoUrl,
        title,
        text
    ) {
        return '<div class="sponsor-card">' +
        '<img class="sponsor-card__image" src="'+ logoUrl + '" data-mce-src="'+ logoUrl + '" alt="Logo image" />' +
        '<div>' +
        '<h3>'+ title + '</h3>' +
        '<p>'+ text + '</p>' +
        '</div>' +
        '</div>'
    }

    tinymce.PluginManager.add('pretalx-sponsor-plugin', (editor) => {

        editor.ui.registry.addMenuItem('sponsor-remove', {
            text: 'Entferne diesen Sponsor',
            onAction: () => {
                const sponsorElement = tinymce.activeEditor.selection.getNode().closest('.sponsor-card');
                if (sponsorElement) {
                    tinyMCE.activeEditor.dom.remove(sponsorElement);
                }
            }
        });

        editor.ui.registry.addContextMenu('sponsor-remove', {
            update: (element) => !element.closest('.sponsor-card')  ? '' : 'sponsor-remove'
        });
    });

    tinymce.init({
        license_key: 'gpl',
        selector: '#id_text_1',
        toolbar: 'undo redo | customInsertSponsorButton | code',
        contextmenu: 'image sponsor-remove',
        plugins: 'image code pretalx-sponsor-plugin',
        content_style: '' +
            "@import url('https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&family=Unbounded:wght@200..900&display=swap'); " +
            '.sponsor-card { margin: 1rem; display: flex; flex-direction: row; gap: 0.25rem; border: 1px solid rgba(0, 0, 0, 0.125); border-radius:0.25rem; } ' +
            '.sponsor-card img { margin: 1rem } ',
        font_family_formats:
            "Unbounded=Unbounded; Open Sans=Open Sans; Andale Mono=andale mono,times; Arial=arial,helvetica,sans-serif; Arial Black=arial black,avant garde; Book Antiqua=book antiqua,palatino; Comic Sans MS=comic sans ms,sans-serif; Courier New=courier new,courier; Georgia=georgia,palatino; Helvetica=helvetica; Impact=impact,chicago; Symbol=symbol; Tahoma=tahoma,arial,helvetica,sans-serif; Terminal=terminal,monaco; Times New Roman=times new roman,times; Trebuchet MS=trebuchet ms,geneva; Verdana=verdana,geneva; Webdings=webdings; Wingdings=wingdings,zapf dingbats",
        setup: (editor) => {

            editor.ui.registry.addButton('customInsertSponsorButton', {
                text: '+Sponsor',
                onAction: (_) => {
                    const inputFields = [
                        {
                            type: 'input',
                            name: 'sponsor_logo_url',
                            label: 'Logo URL',
                            flex: true
                        },
                        {
                            type: 'input',
                            name: 'sponsor_title',
                            label: 'Titel / Sponsorname',
                            flex: true
                        },
                        {
                            type: 'textarea',
                            name: 'sponsor_text',
                            label: 'Text Inhalt',
                            flex: true
                        },
                    ];

                    const sponsorElement = tinymce.activeEditor.selection.getNode().closest('.sponsor-card');
                    if (sponsorElement) {
                        inputFields.push(
                            {
                                type: 'checkbox',
                                name: 'sponsor_before',
                                label: 'Vor dem gewählten Sponsor einfügen',
                                flex: true
                            }
                        )

                    }

                    tinyMCE.activeEditor.windowManager.open({
                        title: 'Bitte Sponsor Daten eingeben (ist später änderbar)',
                        body: {
                            type: 'panel',
                            items: inputFields
                        },
                        onSubmit: function (api) {
                            if (sponsorElement) {
                                tinymce.activeEditor.selection.select(sponsorElement);
                                let content = tinymce.activeEditor.selection.getContent();

                                if (api.getData().sponsor_before === true) {
                                    content = tm_getSponsorCardContent(
                                        api.getData().sponsor_logo_url,
                                        api.getData().sponsor_title,
                                        api.getData().sponsor_text
                                    ) + content
                                } else {
                                    content += tm_getSponsorCardContent(
                                        api.getData().sponsor_logo_url,
                                        api.getData().sponsor_title,
                                        api.getData().sponsor_text
                                    )
                                }

                                tinymce.activeEditor.selection.setContent(content);
                            } else {
                                tinyMCE.activeEditor.insertContent(
                                    tm_getSponsorCardContent(
                                        api.getData().sponsor_logo_url,
                                        api.getData().sponsor_title,
                                        api.getData().sponsor_text
                                    )
                                )
                            }
                            api.close();
                        },
                        buttons: [
                            {
                                text: 'Einfügen',
                                type: 'submit',
                                primary: true,
                            }
                        ]
                    });
                }
            });
        },
    });
})
