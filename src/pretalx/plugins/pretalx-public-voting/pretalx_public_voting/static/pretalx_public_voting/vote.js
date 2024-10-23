document.addEventListener('DOMContentLoaded', () => {
  const saveIndicator = document.querySelector("#js-save")
  if (saveIndicator !== null) {
      const saving = saveIndicator.querySelector(".badge-primary")
      const saved = saveIndicator.querySelector(".badge-success")
      const savingSpinner = document.querySelector(".fa-spin")
      const form = document.querySelector("form")

      function saveForm() {
          savingSpinner.classList.remove("d-none")
          saved.classList.add("d-none")
          saving.classList.remove("d-none")
          window.setTimeout(() => {
              fetch(form.action, {
                  method: 'POST',
                  body: new FormData(form),
              }).then((res) => {
                  savingSpinner.classList.add("d-none")
                  saved.classList.remove("d-none")
                  saving.classList.add("d-none")
              })
          }, 5)
      }

      document.querySelectorAll('input[type="radio"]').forEach((input) => {
          input.addEventListener('change', (event) => {
              saveForm();
          })
      })

      document.querySelectorAll('.btn-save-comment').forEach((input) => {
          input.addEventListener('click', (event) => {
              saveForm();
          })
      })
  }

    document.querySelectorAll('.form-delete-comment').forEach((deleteCommentForm) => {
        deleteCommentForm.addEventListener('submit', e => {
            return (window.confirm('Sind Sie sicher, dass Sie den Kommentar löschen wollen?')) ? true : e.preventDefault()
        })
    })
})
