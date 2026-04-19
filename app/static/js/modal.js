document.addEventListener("DOMContentLoaded", function () {
  const modalElement = document.getElementById("demoModal");
  const form = document.getElementById("demoModalForm");
  const formFields = document.getElementById("demoModalFormFields");
  const footer = document.getElementById("demoModalFooter");
  const feedback = document.getElementById("demoModalFeedback");
  const submitButton = document.getElementById("demoModalSubmitBtn");

  if (!modalElement || !form || !feedback || !submitButton) {
    return;
  }

  const defaultButtonMarkup = submitButton.innerHTML;

  function clearFieldErrors() {
    form.querySelectorAll(".is-invalid").forEach(function (input) {
      input.classList.remove("is-invalid");
    });

    form.querySelectorAll(".dynamic-invalid-feedback").forEach(function (node) {
      node.remove();
    });

    form.querySelectorAll(".invalid-feedback").forEach(function (node) {
      if (node.classList.contains("dynamic-invalid-feedback")) {
        return;
      }
      node.textContent = "";
    });
  }

  function setLoading(isLoading) {
    submitButton.disabled = isLoading;
    if (isLoading) {
      submitButton.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Booking...';
      return;
    }
    submitButton.innerHTML = defaultButtonMarkup;
  }

  function setFieldError(fieldName, message) {
    const field = form.querySelector('[name="' + fieldName + '"]');
    if (!field) {
      return;
    }

    field.classList.add("is-invalid");

    let feedbackNode = field.parentElement.querySelector(".invalid-feedback");
    if (!feedbackNode) {
      feedbackNode = document.createElement("div");
      feedbackNode.className = "invalid-feedback dynamic-invalid-feedback";
      field.parentElement.appendChild(feedbackNode);
    }

    feedbackNode.textContent = message;
    feedbackNode.classList.add("d-block");
  }

  function showFeedback(messageHtml, typeClass) {
    feedback.classList.remove("d-none", "alert-success", "alert-danger", "alert-warning");
    feedback.classList.add("alert", typeClass);
    feedback.innerHTML = messageHtml;
  }

  function resetModalState() {
    clearFieldErrors();
    form.reset();

    if (formFields) {
      formFields.classList.remove("d-none");
    }

    if (footer) {
      footer.classList.remove("d-none");
    }

    feedback.classList.add("d-none");
    feedback.classList.remove("alert", "alert-success", "alert-danger", "alert-warning");
    feedback.innerHTML = "";
    setLoading(false);
  }

  modalElement.addEventListener("shown.bs.modal", function () {
    resetModalState();
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const modalSubmitBtn = document.querySelector(
      "#demoModal .modal-footer button[type='submit'], #demoModal button.btn-cl-primary"
    );
    if (modalSubmitBtn && modalSubmitBtn.classList.contains("btn-loading")) {
      return;
    }

    clearFieldErrors();
    feedback.classList.add("d-none");

    const formData = new FormData(form);
    const csrfToken = formData.get("csrf_token") || "";

    document.dispatchEvent(new CustomEvent("demoFormStart"));
    setLoading(true);

    try {
      const response = await fetch("/demo", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken,
          "X-CSRF-Token": csrfToken
        },
        body: formData
      });

      const payload = await response.json().catch(function () {
        return { status: "error" };
      });

      if (payload.status === "success") {
        if (formFields) {
          formFields.classList.add("d-none");
        }

        if (footer) {
          footer.classList.add("d-none");
        }

        showFeedback(
          '<div class="text-center py-2">' +
            '<i class="fa-solid fa-circle-check mb-3" style="font-size: 54px; color: var(--cl-success);"></i>' +
            '<h5 class="mb-2" style="color: var(--cl-navy);">Booking confirmed! We\'ll call you within minutes.</h5>' +
            '<p class="text-muted mb-3">Your demo has been booked! We\'ll call you shortly.</p>' +
            '<button type="button" class="btn btn-cl-primary" id="closeExploreProgramsBtn">Close & Explore Programs</button>' +
          '</div>',
          "alert-success"
        );

        const closeExploreButton = document.getElementById("closeExploreProgramsBtn");
        if (closeExploreButton) {
          closeExploreButton.addEventListener("click", function () {
            const modalInstance = window.bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
              modalInstance.hide();
            }
            window.location.href = "/courses";
          });
        }

        return;
      }

      if (payload.status === "error" && payload.errors) {
        Object.keys(payload.errors).forEach(function (fieldName) {
          const fieldErrors = payload.errors[fieldName];
          if (Array.isArray(fieldErrors) && fieldErrors.length) {
            setFieldError(fieldName, fieldErrors[0]);
          }
        });

        showFeedback("Please correct the highlighted fields and submit again.", "alert-warning");
        return;
      }

      showFeedback(
        'Something went wrong. Please try again or <a href="https://wa.me/919978559986?text=Hi%2C%20I%20want%20to%20book%20a%20free%20demo%20class" target="_blank" rel="noopener">WhatsApp us directly</a>.',
        "alert-danger"
      );
    } catch (error) {
      showFeedback(
        'Something went wrong. Please try again or <a href="https://wa.me/919978559986?text=Hi%2C%20I%20want%20to%20book%20a%20free%20demo%20class" target="_blank" rel="noopener">WhatsApp us directly</a>.',
        "alert-danger"
      );
    } finally {
      setLoading(false);
      document.dispatchEvent(new CustomEvent("demoFormEnd"));
    }
  });
});
