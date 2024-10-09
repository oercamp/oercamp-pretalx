const updateVisibility = () => {
  if (["accepted", "confirmed"].includes(document.querySelector("#id_state").value)) {
    document.querySelector("#show-if-state").classList.remove("d-none")
  } else {
    document.querySelector("#show-if-state").classList.add("d-none")
  }
}

if (document.querySelector("#id_state")) {
  document.querySelector("#id_state").addEventListener("change", updateVisibility)
  updateVisibility()
}

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
