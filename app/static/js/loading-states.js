(function () {
  "use strict";

  function createSpinnerHTML(text, size = "sm") {
    const sizeClass = size === "sm" ? "spinner-border-sm" : "";
    const width = size === "sm" ? "1rem" : "1.25rem";
    return (
      '<span class="spinner-border ' +
      sizeClass +
      ' me-2" role="status" aria-hidden="true" style="width: ' +
      width +
      "; height: " +
      width +
      ';"></span>' +
      text
    );
  }

  function convertSubmitInputsToButtons() {
    document.querySelectorAll("form input[type='submit']").forEach(function (input) {
      const button = document.createElement("button");
      button.type = "submit";

      Array.from(input.attributes).forEach(function (attr) {
        if (attr.name === "type" || attr.name === "value") {
          return;
        }
        button.setAttribute(attr.name, attr.value);
      });

      button.className = input.className;
      button.innerHTML = input.value || input.getAttribute("value") || "Submit";
      button.disabled = input.disabled;
      input.replaceWith(button);
    });
  }

  function setButtonLoading(btn, loadingText) {
    if (!btn) {
      return "";
    }

    const originalHTML = btn.innerHTML;
    const originalWidth = btn.offsetWidth;
    if (originalWidth > 0) {
      btn.style.minWidth = originalWidth + "px";
    }

    btn.dataset.originalHtml = originalHTML;
    btn.innerHTML = createSpinnerHTML(loadingText);
    btn.disabled = true;
    btn.classList.add("btn-loading");
    return originalHTML;
  }

  function restoreButton(btn, originalHTML) {
    if (!btn) {
      return;
    }

    const htmlToRestore = originalHTML || btn.dataset.originalHtml || btn.innerHTML;
    btn.innerHTML = htmlToRestore;
    btn.disabled = false;
    btn.classList.remove("btn-loading", "btn-filter-loading");
    btn.style.minWidth = "";
    delete btn.dataset.originalHtml;
  }

  function findSubmitButton(form) {
    return form.querySelector("button[type='submit'], [type='submit'], button.btn-submit-trigger");
  }

  function getNavigationType() {
    const entries = window.performance && window.performance.getEntriesByType
      ? window.performance.getEntriesByType("navigation")
      : [];
    if (!entries.length) {
      return "";
    }
    return entries[0].type || "";
  }

  window.CLLoadingStates = {
    createSpinnerHTML: createSpinnerHTML,
    setButtonLoading: setButtonLoading,
    restoreButton: restoreButton
  };
  window.createSpinnerHTML = createSpinnerHTML;
  window.setButtonLoading = setButtonLoading;
  window.restoreButton = restoreButton;

  document.addEventListener("DOMContentLoaded", function () {
    convertSubmitInputsToButtons();

    const loadingTextMap = {
      loginForm: "Logging in...",
      registerForm: "Creating account...",
      demoBookingForm: "Booking your demo...",
      demoModalForm: "Booking your demo...",
      contactForm: "Sending message...",
      scholarshipRegisterForm: "Registering...",
      scholarshipTestForm: "Submitting test... Please wait",
      profileUpdateForm: "Saving changes...",
      courseEditForm: "Saving course...",
      blogEditForm: "Saving post...",
      blogNewForm: "Creating post...",
      emailCaptureForm: "Getting your resources...",
      leadsFilterForm: "Filtering...",
      studentsFilterForm: "Filtering...",
      blogFilterForm: "Filtering...",
      default: "Processing..."
    };

    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        const submitBtn = findSubmitButton(form);
        if (!submitBtn) {
          return;
        }

        if (submitBtn.disabled || submitBtn.classList.contains("btn-loading")) {
          event.preventDefault();
          return;
        }

        let loadingText = loadingTextMap.default;
        if (submitBtn.dataset.loadingText) {
          loadingText = submitBtn.dataset.loadingText;
        } else if (form.id && loadingTextMap[form.id]) {
          loadingText = loadingTextMap[form.id];
        }

        if (form.id === "scholarshipTestForm") {
          loadingText = "Submitting your answers... Do not close this page";
        }

        setButtonLoading(submitBtn, loadingText);

        if (form.id === "leadsFilterForm" || form.id === "studentsFilterForm" || form.id === "blogFilterForm") {
          submitBtn.classList.add("btn-filter-loading");
        }
      });
    });

    let demoModalOriginalHTML = "";

    document.addEventListener("demoFormStart", function () {
      const modalSubmitBtn = document.querySelector("#demoModal .modal-footer button[type='submit'], #demoModal button.btn-cl-primary");
      if (!modalSubmitBtn || modalSubmitBtn.classList.contains("btn-loading")) {
        return;
      }
      demoModalOriginalHTML = setButtonLoading(modalSubmitBtn, "Booking your demo...");
    });

    document.addEventListener("demoFormEnd", function () {
      const modalSubmitBtn = document.querySelector("#demoModal .modal-footer button[type='submit'], #demoModal button.btn-cl-primary");
      if (!modalSubmitBtn || !modalSubmitBtn.classList.contains("btn-loading")) {
        return;
      }
      restoreButton(modalSubmitBtn, demoModalOriginalHTML || modalSubmitBtn.dataset.originalHtml);
      demoModalOriginalHTML = "";
    });

    document.querySelectorAll("a[data-loading-text]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        if (link.classList.contains("resource-direct-download")) {
          return;
        }

        if (link.classList.contains("btn-loading")) {
          event.preventDefault();
          return;
        }

        const loadingText = link.dataset.loadingText || "Processing...";
        const originalHTML = link.innerHTML;
        const originalHref = link.getAttribute("href");

        if (!originalHref || originalHref === "#") {
          return;
        }

        event.preventDefault();

        link.innerHTML = createSpinnerHTML(loadingText);
        link.classList.add("btn-loading");
        link.style.pointerEvents = "none";

        const navigateDelay = Number(link.dataset.loadingDelay || 400);
        const restoreDelay = Number(link.dataset.restoreDelay || (link.id === "exportCsvBtn" ? 3000 : 6000));

        setTimeout(function () {
          window.location.href = originalHref;
        }, navigateDelay);

        setTimeout(function () {
          if (!document.body.contains(link)) {
            return;
          }
          link.innerHTML = originalHTML;
          link.classList.remove("btn-loading");
          link.style.pointerEvents = "";
        }, restoreDelay);
      });
    });

    document.querySelectorAll(".resource-direct-download[data-loading-text]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        if (link.classList.contains("btn-loading")) {
          event.preventDefault();
          return;
        }

        const originalHref = link.getAttribute("href");
        if (!originalHref || originalHref === "#") {
          return;
        }

        event.preventDefault();

        const originalHTML = link.innerHTML;
        link.innerHTML = createSpinnerHTML(link.dataset.loadingText || "Loading...");
        link.classList.add("btn-loading");
        link.style.pointerEvents = "none";

        const downloadFrame = document.getElementById("resourceDownloadFrame");

        setTimeout(function () {
          if (downloadFrame) {
            downloadFrame.src = originalHref;
          } else {
            window.location.href = originalHref;
          }
        }, 400);

        setTimeout(function () {
          if (!document.body.contains(link)) {
            return;
          }

          link.innerHTML = originalHTML;
          link.classList.remove("btn-loading");
          link.style.pointerEvents = "";
        }, 3000);
      });
    });

    document.querySelectorAll(".resource-download-btn").forEach(function (button) {
      button.addEventListener("click", function (event) {
        if (button.disabled || button.classList.contains("btn-loading")) {
          event.preventDefault();
          return;
        }

        event.preventDefault();

        const originalHTML = setButtonLoading(button, button.dataset.loadingText || "Loading...");
        const modalTarget = button.dataset.modalTarget;

        setTimeout(function () {
          restoreButton(button, originalHTML);

          if (!modalTarget) {
            return;
          }

          const modalElement = document.querySelector(modalTarget);
          if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) {
            return;
          }

          const modalInstance = window.bootstrap.Modal.getOrCreateInstance(modalElement);
          modalInstance.show();
        }, 300);
      });
    });

    const scholarshipForm = document.getElementById("scholarshipTestForm");
    if (scholarshipForm) {
      let alreadySubmitted = false;

      scholarshipForm.addEventListener("submit", function (event) {
        if (alreadySubmitted) {
          event.preventDefault();
          return false;
        }

        const questionCards = document.querySelectorAll(".question-card, .scholarship-question-card");
        const totalQuestions = questionCards.length;
        const answeredQuestions = scholarshipForm.querySelectorAll('input[type="radio"]:checked').length;
        const autoSubmittedField = scholarshipForm.querySelector('input[name="auto_submitted"]');
        const isAutoSubmitted = (autoSubmittedField && autoSubmittedField.value || "").toLowerCase() === "true";

        if (!isAutoSubmitted && answeredQuestions < totalQuestions) {
          const confirmed = window.confirm(
            "You have only answered " +
              answeredQuestions +
              " out of " +
              totalQuestions +
              " questions. Unanswered questions will be marked as wrong. Are you sure you want to submit?"
          );

          if (!confirmed) {
            event.preventDefault();
            const submitBtn = findSubmitButton(scholarshipForm);
            if (submitBtn && submitBtn.classList.contains("btn-loading")) {
              restoreButton(submitBtn, submitBtn.dataset.originalHtml);
            }
            return false;
          }
        }

        alreadySubmitted = true;

        const submitBtn = findSubmitButton(scholarshipForm);
        if (submitBtn) {
          if (!submitBtn.classList.contains("btn-loading")) {
            setButtonLoading(submitBtn, "Submitting your answers... Please do not close this page");
          } else {
            submitBtn.innerHTML = createSpinnerHTML("Submitting your answers... Please do not close this page", "sm");
            submitBtn.disabled = true;
          }
        }

        window.testTimerPaused = true;

        if (!document.getElementById("submissionOverlay")) {
          const overlay = document.createElement("div");
          overlay.id = "submissionOverlay";
          overlay.style.cssText =
            "position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(26, 26, 46, 0.85); z-index: 99999; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white;";
          overlay.innerHTML =
            '<div class="spinner-border mb-3" style="width: 3rem; height: 3rem;" role="status"></div>' +
            "<h4>Submitting Your Scholarship Test</h4>" +
            '<p class="text-white-50 mt-2">Please wait. Do not press back or refresh this page.</p>';
          document.body.appendChild(overlay);
        }
      });
    }

    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
      loginForm.addEventListener("submit", function () {
        const submitBtn = findSubmitButton(loginForm);
        if (!submitBtn) {
          return;
        }

        let originalHTML = submitBtn.dataset.originalHtml || submitBtn.innerHTML;
        if (!submitBtn.classList.contains("btn-loading")) {
          originalHTML = setButtonLoading(submitBtn, "Logging in...");
        }

        setTimeout(function () {
          if (document.body.contains(submitBtn) && submitBtn.classList.contains("btn-loading")) {
            restoreButton(submitBtn, originalHTML);
          }
        }, 8000);
      });
    }

    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
      registerForm.addEventListener("submit", function () {
        const submitBtn = findSubmitButton(registerForm);
        if (!submitBtn) {
          return;
        }

        let originalHTML = submitBtn.dataset.originalHtml || submitBtn.innerHTML;
        if (!submitBtn.classList.contains("btn-loading")) {
          originalHTML = setButtonLoading(submitBtn, "Creating account...");
        }

        setTimeout(function () {
          if (document.body.contains(submitBtn) && submitBtn.classList.contains("btn-loading")) {
            restoreButton(submitBtn, originalHTML);
          }
        }, 10000);
      });
    }
  });

  window.addEventListener("pageshow", function (event) {
    if (!event.persisted && getNavigationType() !== "back_forward") {
      return;
    }

    document.querySelectorAll(".btn-loading").forEach(function (btn) {
      restoreButton(btn, btn.dataset.originalHtml);
    });
  });
})();
