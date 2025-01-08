document.addEventListener("DOMContentLoaded", function() {
    new EmojiPicker({
        trigger: [
            {
                selector: '#emoji_label_emoji_picker_button',
                insertInto: '#id_emoji_label'
            },
        ],
        closeButton: true,
        specialButtons: '#00175C' // $brand-primary
    });
})
