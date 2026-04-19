const DEFAULT_EXAM_SECURITY_CONFIG = {
  MAX_VIOLATIONS: 3,
  FULLSCREEN_REQUIRED: true,
  WARNING_MODAL_ID: "examWarningModal",
  VIOLATION_ENDPOINT: "/scholarship/report-violation",
  FORM_ID: "scholarshipTestForm",
  QUESTIONS_CONTAINER_ID: "questionsContainer",
  CSRF_TOKEN: document.querySelector('meta[name="csrf-token"]')?.content || "",
  TIMER_EXPIRED_MESSAGE: "Your exam time limit has ended.",
  LEAVE_CONFIRMATION_TEXT: "You are in the middle of your exam. If you leave, your current answers may be lost. Are you sure?",
  VIOLATION_MESSAGES: {
    tab_switch: "You switched to another tab or window.",
    fullscreen_exit: "You exited full screen mode.",
    copy_attempt: "You attempted to copy content.",
    right_click: "Right-click is not allowed during the exam.",
    keyboard_shortcut: "That keyboard shortcut is not allowed during the exam.",
    devtools_open: "Developer tools are not allowed during the exam.",
    focus_loss: "The exam window lost focus.",
    drag_attempt: "Dragging content is not allowed during the exam.",
    print_attempt: "Printing is not allowed during the exam."
  }
};

const EXAM_SECURITY_CONFIG = Object.assign(
  {},
  DEFAULT_EXAM_SECURITY_CONFIG,
  window.examSecurityConfig || {}
);

EXAM_SECURITY_CONFIG.VIOLATION_MESSAGES = Object.assign(
  {},
  DEFAULT_EXAM_SECURITY_CONFIG.VIOLATION_MESSAGES,
  (window.examSecurityConfig && window.examSecurityConfig.VIOLATION_MESSAGES) || {}
);

let violationCount = 0;
let examSubmitted = false;
let fullscreenActive = false;
let warningModalInstance = null;
let devtoolsOpen = false;
let timeRemaining = Number(window.serverTimeRemaining || 1200);

const violationDebounceMs = 1200;
const violationTimestamps = {};

function shouldSkipViolation(violationType) {
  const now = Date.now();
  const previous = violationTimestamps[violationType] || 0;
  if (now - previous < violationDebounceMs) {
    return true;
  }
  violationTimestamps[violationType] = now;
  return false;
}

function getViolationMessage(violationType) {
  return EXAM_SECURITY_CONFIG.VIOLATION_MESSAGES[violationType] || "A violation was detected.";
}

function blockAndStop(event) {
  event.preventDefault();
  event.stopPropagation();
  return false;
}

async function reportViolation(violationType) {
  if (examSubmitted || shouldSkipViolation(violationType)) {
    return;
  }

  violationCount += 1;

  try {
    const response = await fetch(EXAM_SECURITY_CONFIG.VIOLATION_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": EXAM_SECURITY_CONFIG.CSRF_TOKEN
      },
      body: JSON.stringify({ violation_type: violationType })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || "Violation endpoint failed.");
    }

    violationCount = Number(data.violation_count || violationCount);

    if (data.auto_submit) {
      triggerAutoSubmit("Maximum integrity violations reached. Test auto-submitted.");
      return;
    }

    showViolationWarning(
      violationType,
      Number(data.violation_count || violationCount),
      Number(data.remaining_warnings || 0)
    );
  } catch (error) {
    const remaining = EXAM_SECURITY_CONFIG.MAX_VIOLATIONS - violationCount;

    if (violationCount >= EXAM_SECURITY_CONFIG.MAX_VIOLATIONS) {
      triggerAutoSubmit("Maximum integrity violations reached. Test auto-submitted.");
      return;
    }

    showViolationWarning(violationType, violationCount, Math.max(0, remaining));
  }
}

function showViolationWarning(violationType, count, remaining) {
  let modal = document.getElementById(EXAM_SECURITY_CONFIG.WARNING_MODAL_ID);
  if (!modal) {
    modal = document.createElement("div");
    modal.id = EXAM_SECURITY_CONFIG.WARNING_MODAL_ID;
    modal.className = "modal fade";
    modal.setAttribute("data-bs-backdrop", "static");
    modal.setAttribute("data-bs-keyboard", "false");
    modal.setAttribute("tabindex", "-1");
    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content" style="border: 3px solid #C0392B;">
          <div class="modal-header" style="background: #C0392B; color: white;">
            <h5 class="modal-title fw-bold">⚠️ Exam Integrity Warning</h5>
          </div>
          <div class="modal-body" id="warningModalBody"></div>
          <div class="modal-footer justify-content-center">
            <button type="button" class="btn btn-danger px-4" id="warningDismissBtn">
              I Understand, Continue Exam
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  const body = document.getElementById("warningModalBody");
  const violationMsg = getViolationMessage(violationType);
  const remainingText = remaining > 0
    ? `You have <strong style="color:#C0392B;">${remaining} warning(s)</strong> left. If you receive ${EXAM_SECURITY_CONFIG.MAX_VIOLATIONS} warnings, your test will be auto-submitted with your current answers.`
    : `<strong style="color:#C0392B;">This is your final warning.</strong> Your next violation will automatically submit your test.`;

  body.innerHTML = `
    <p><strong>${violationMsg}</strong></p>
    <p>This is warning <strong style="color:#C0392B;">${count} of ${EXAM_SECURITY_CONFIG.MAX_VIOLATIONS}</strong>.</p>
    <p>${remainingText}</p>
    <div class="alert alert-warning py-2 px-3" style="font-size: 14px;">
      <i class="fas fa-exclamation-triangle me-2"></i>
      Please focus on the exam. Ensure you are in full screen mode and do not switch windows.
    </div>
  `;

  const modalInstance = new bootstrap.Modal(modal, {
    backdrop: "static",
    keyboard: false
  });

  warningModalInstance = modalInstance;
  modalInstance.show();

  const dismissBtn = document.getElementById("warningDismissBtn");
  dismissBtn.onclick = function () {
    modalInstance.hide();
    if (EXAM_SECURITY_CONFIG.FULLSCREEN_REQUIRED) {
      requestFullScreen();
    }
  };
}

function triggerAutoSubmit(reason) {
  if (examSubmitted) {
    return;
  }

  examSubmitted = true;
  window.testTimerPaused = true;
  window.onbeforeunload = null;

  const overlay = document.createElement("div");
  overlay.style.cssText = `
    position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    background: rgba(26, 26, 46, 0.95);
    z-index: 999999;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: white; font-family: 'Poppins', sans-serif;
  `;
  overlay.innerHTML = `
    <div class="spinner-border mb-4" style="width: 3rem; height: 3rem; color: #C0392B;" role="status"></div>
    <h3 style="color: #C0392B; font-weight: 700;">Exam Auto-Submitted</h3>
    <p style="color: rgba(255,255,255,0.8); margin-top: 8px; text-align: center; max-width: 420px;">
      ${reason}<br>Your answers have been submitted automatically.
    </p>
    <p style="color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 16px;">
      Please do not close this page...
    </p>
  `;
  document.body.appendChild(overlay);

  const form = document.getElementById(EXAM_SECURITY_CONFIG.FORM_ID);
  if (form) {
    let autoField = form.querySelector('input[name="auto_submitted"]');
    if (!autoField) {
      autoField = document.createElement("input");
      autoField.type = "hidden";
      autoField.name = "auto_submitted";
      autoField.value = "true";
      form.appendChild(autoField);
    }

    form.submit();
  }
}

function requestFullScreen() {
  const elem = document.documentElement;
  if (elem.requestFullscreen) {
    elem.requestFullscreen()
      .then(function () {
        fullscreenActive = true;
      })
      .catch(function () {
        showFullScreenInstructions();
      });
  } else if (elem.webkitRequestFullscreen) {
    elem.webkitRequestFullscreen();
    fullscreenActive = true;
  } else if (elem.mozRequestFullScreen) {
    elem.mozRequestFullScreen();
    fullscreenActive = true;
  } else if (elem.msRequestFullscreen) {
    elem.msRequestFullscreen();
    fullscreenActive = true;
  } else {
    showFullScreenInstructions();
  }
}

function exitFullScreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.webkitExitFullscreen) {
    document.webkitExitFullscreen();
  }
}

function isInFullScreen() {
  return !!(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  );
}

function showFullScreenInstructions() {
  const banner = document.getElementById("fullscreenBanner");
  if (banner) {
    banner.classList.remove("d-none");
  }
}

function handleFullScreenChange() {
  if (!isInFullScreen() && fullscreenActive && !examSubmitted) {
    fullscreenActive = false;
    showFullScreenInstructions();
    reportViolation("fullscreen_exit");
  } else if (isInFullScreen()) {
    fullscreenActive = true;
    const banner = document.getElementById("fullscreenBanner");
    if (banner) {
      banner.classList.add("d-none");
    }
  }
}

document.addEventListener("fullscreenchange", handleFullScreenChange);
document.addEventListener("webkitfullscreenchange", handleFullScreenChange);
document.addEventListener("mozfullscreenchange", handleFullScreenChange);
document.addEventListener("MSFullscreenChange", handleFullScreenChange);

document.addEventListener("visibilitychange", function () {
  if (document.hidden && !examSubmitted) {
    reportViolation("tab_switch");
  }
});

window.addEventListener("blur", function () {
  if (!examSubmitted) {
    setTimeout(function () {
      if (!document.hasFocus() && !examSubmitted) {
        reportViolation("focus_loss");
      }
    }, 500);
  }
});

document.addEventListener("keydown", function (e) {
  if (examSubmitted) {
    return;
  }

  const key = e.key ? e.key.toLowerCase() : "";
  const ctrl = e.ctrlKey || e.metaKey;
  const shift = e.shiftKey;

  if (ctrl && key === "c") {
    blockAndStop(e);
    reportViolation("copy_attempt");
    return false;
  }

  if (ctrl && key === "v") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "x") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "a") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "u") {
    blockAndStop(e);
    reportViolation("keyboard_shortcut");
    return false;
  }

  if (ctrl && shift && key === "i") {
    blockAndStop(e);
    reportViolation("devtools_open");
    return false;
  }

  if (ctrl && shift && key === "j") {
    blockAndStop(e);
    reportViolation("devtools_open");
    return false;
  }

  if (ctrl && shift && key === "c") {
    blockAndStop(e);
    reportViolation("devtools_open");
    return false;
  }

  if (e.key === "F12") {
    blockAndStop(e);
    reportViolation("devtools_open");
    return false;
  }

  if (ctrl && key === "p") {
    blockAndStop(e);
    reportViolation("print_attempt");
    return false;
  }

  if (ctrl && key === "s") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "f") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "g") {
    blockAndStop(e);
    return false;
  }

  if (e.altKey && e.key === "F4") {
    blockAndStop(e);
    return false;
  }

  if (e.key === "F5") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "r") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "w") {
    blockAndStop(e);
    return false;
  }

  if (ctrl && key === "t") {
    blockAndStop(e);
    reportViolation("tab_switch");
    return false;
  }

  if (ctrl && key === "n") {
    blockAndStop(e);
    reportViolation("tab_switch");
    return false;
  }

  if (e.altKey && e.key === "Tab") {
    blockAndStop(e);
    return false;
  }

  if (e.key === "Meta" || e.key === "OS") {
    blockAndStop(e);
    return false;
  }
});

document.addEventListener("contextmenu", function (e) {
  if (examSubmitted) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  reportViolation("right_click");
  return false;
});

document.addEventListener("copy", function (e) {
  if (examSubmitted) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  if (e.clipboardData) {
    e.clipboardData.setData("text/plain", "");
  }
  reportViolation("copy_attempt");
});

document.addEventListener("cut", function (e) {
  if (examSubmitted) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
});

const originalGetSelection = window.getSelection;
window.getSelection = function () {
  const selection = originalGetSelection.call(window);
  if (selection && selection.anchorNode) {
    const questionArea = document.getElementById(EXAM_SECURITY_CONFIG.QUESTIONS_CONTAINER_ID);
    if (questionArea && questionArea.contains(selection.anchorNode)) {
      selection.removeAllRanges();
    }
  }
  return selection;
};

document.addEventListener("dragstart", function (e) {
  if (examSubmitted) {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  reportViolation("drag_attempt");
  return false;
});

document.addEventListener("drop", function (e) {
  e.preventDefault();
  e.stopPropagation();
  return false;
});

const devtoolsThreshold = 160;

function detectDevTools() {
  if (examSubmitted) {
    return;
  }

  const widthThreshold = window.outerWidth - window.innerWidth > devtoolsThreshold;
  const heightThreshold = window.outerHeight - window.innerHeight > devtoolsThreshold;

  if ((widthThreshold || heightThreshold) && !devtoolsOpen) {
    devtoolsOpen = true;
    reportViolation("devtools_open");
  } else if (!widthThreshold && !heightThreshold) {
    devtoolsOpen = false;
  }
}

setInterval(detectDevTools, 2000);

(function () {
  const element = new Image();
  Object.defineProperty(element, "id", {
    get: function () {
      if (!examSubmitted) {
        devtoolsOpen = true;
        reportViolation("devtools_open");
      }
      return "detected";
    }
  });

  requestAnimationFrame(function check() {
    console.log("%c", element);
    if (!examSubmitted) {
      requestAnimationFrame(check);
    }
  });
})();

window.print = function () {
  reportViolation("print_attempt");
  return false;
};

window.addEventListener("beforeprint", function (e) {
  reportViolation("print_attempt");
  if (e.preventDefault) {
    e.preventDefault();
  }
});

if (window.BroadcastChannel && window.currentUserId) {
  const examChannel = new BroadcastChannel("cl_exam_channel_" + window.currentUserId);

  examChannel.postMessage({ type: "exam_open", timestamp: Date.now() });

  examChannel.addEventListener("message", function (event) {
    if (examSubmitted || !event || !event.data) {
      return;
    }

    if (event.data.type === "exam_open") {
      reportViolation("tab_switch");
      alert(
        "This exam is already open in another tab or window. Please close all other tabs and continue here. This incident has been recorded."
      );
    }
  });

  window.addEventListener("beforeunload", function () {
    examChannel.close();
  });
}

history.pushState(null, null, window.location.href);

window.addEventListener("popstate", function () {
  history.pushState(null, null, window.location.href);
  if (!examSubmitted) {
    reportViolation("tab_switch");
  }
});

window.addEventListener("beforeunload", function (e) {
  if (examSubmitted) {
    return;
  }

  e.preventDefault();
  e.returnValue = EXAM_SECURITY_CONFIG.LEAVE_CONFIRMATION_TEXT;
  return e.returnValue;
});

const timerDisplay = document.getElementById("examTimer");
const stickyTimer = document.getElementById("stickyTimer");
const timerInterval = setInterval(function () {
  if (window.testTimerPaused || examSubmitted) {
    return;
  }

  timeRemaining -= 1;

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const display = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  if (timerDisplay) {
    timerDisplay.textContent = `Time Remaining: ${display}`;
    if (timeRemaining <= 300) {
      timerDisplay.style.color = "#C0392B";
      timerDisplay.style.fontWeight = "700";
    }
    if (timeRemaining <= 60) {
      timerDisplay.classList.toggle("opacity-50");
    }
  }

  if (stickyTimer) {
    stickyTimer.textContent = display;
    if (timeRemaining <= 300) {
      stickyTimer.style.color = "#C0392B";
      stickyTimer.style.fontWeight = "700";
    }
    if (timeRemaining <= 60) {
      stickyTimer.classList.toggle("opacity-50");
    }
  }

  if (timeRemaining <= 0) {
    clearInterval(timerInterval);
    triggerAutoSubmit(EXAM_SECURITY_CONFIG.TIMER_EXPIRED_MESSAGE);
  }
}, 1000);

function updateAnsweredCount() {
  const form = document.getElementById(EXAM_SECURITY_CONFIG.FORM_ID);
  const answeredCountEl = document.getElementById("answeredCount");

  if (!form || !answeredCountEl) {
    return;
  }

  const totalQuestions = document.querySelectorAll(".scholarship-question-card, .question-card").length;
  const answered = form.querySelectorAll('input[type="radio"]:checked').length;
  answeredCountEl.textContent = `${answered} of ${totalQuestions} answered`;
}

function updateScrollProgress() {
  const progress = document.getElementById("questionProgress");
  const questionCards = Array.from(document.querySelectorAll(".scholarship-question-card, .question-card"));

  if (!progress || !questionCards.length) {
    return;
  }

  const marker = window.scrollY + window.innerHeight * 0.35;
  let activeQuestion = 1;

  questionCards.forEach(function (card, index) {
    if (card.offsetTop <= marker) {
      activeQuestion = index + 1;
    }
  });

  progress.textContent = `Question ${activeQuestion} of ${questionCards.length}`;
}

function showFullScreenStartModal() {
  let startModal = document.getElementById("examStartModal");
  if (!startModal) {
    startModal = document.createElement("div");
    startModal.id = "examStartModal";
    startModal.className = "modal fade";
    startModal.setAttribute("data-bs-backdrop", "static");
    startModal.setAttribute("data-bs-keyboard", "false");
    startModal.setAttribute("tabindex", "-1");
    startModal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header" style="background: #1A1A2E; color: white;">
            <h4 class="modal-title fw-bold">
              <i class="fas fa-shield-alt me-2" style="color: #C0392B;"></i>
              Before You Begin, Exam Rules
            </h4>
          </div>
          <div class="modal-body p-4">
            <div class="alert alert-warning">
              <strong>⚠️ This exam is monitored for integrity violations.</strong>
              Any suspicious behaviour will be recorded and may result in automatic test submission.
            </div>
            <h6 class="fw-bold mb-3">During the exam, the following are strictly prohibited:</h6>
            <div class="row">
              <div class="col-md-6">
                <ul class="list-unstyled">
                  <li class="mb-2">🚫 Switching to another tab or window</li>
                  <li class="mb-2">🚫 Copying or sharing question content</li>
                  <li class="mb-2">🚫 Using browser developer tools</li>
                  <li class="mb-2">🚫 Right-clicking on the exam page</li>
                </ul>
              </div>
              <div class="col-md-6">
                <ul class="list-unstyled">
                  <li class="mb-2">🚫 Printing the exam questions</li>
                  <li class="mb-2">🚫 Exiting full screen mode</li>
                  <li class="mb-2">🚫 Refreshing or navigating away</li>
                  <li class="mb-2">🚫 Opening the exam in multiple tabs</li>
                </ul>
              </div>
            </div>
            <div class="alert alert-info mt-3 mb-0">
              <strong>ℹ️ You will receive up to 3 warnings.</strong>
              After 3 violations, your test will be auto-submitted with your current answers.
            </div>
            <div class="mt-3 p-3 rounded" style="background: #f8f9fa; border: 1px solid #dee2e6;">
              <p class="mb-1 fw-bold">✅ The exam will now open in <strong>Full Screen mode</strong>.</p>
              <p class="mb-0 text-muted small">
                You must stay in full screen for the entire duration. Exiting full screen counts as a violation.
                Press <kbd>F11</kbd> or use the button below to enter full screen mode.
              </p>
            </div>
          </div>
          <div class="modal-footer justify-content-center">
            <button type="button" id="startExamBtn" class="btn btn-danger btn-lg px-5">
              <i class="fas fa-expand me-2"></i>I Understand, Enter Full Screen and Begin
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(startModal);
  }

  const modalInstance = new bootstrap.Modal(startModal, {
    backdrop: "static",
    keyboard: false
  });
  modalInstance.show();

  const startBtn = document.getElementById("startExamBtn");
  startBtn.onclick = function () {
    modalInstance.hide();
    requestFullScreen();
  };
}

document.addEventListener("DOMContentLoaded", function () {
  const examForm = document.getElementById(EXAM_SECURITY_CONFIG.FORM_ID);
  if (examForm) {
    examForm.addEventListener("submit", function (event) {
      if (event.defaultPrevented) {
        return;
      }

      examSubmitted = true;
      window.testTimerPaused = true;
    });
  }

  if (EXAM_SECURITY_CONFIG.FULLSCREEN_REQUIRED) {
    showFullScreenStartModal();
  }

  updateAnsweredCount();
  updateScrollProgress();

  document.querySelectorAll('input[type="radio"]').forEach(function (radio) {
    radio.addEventListener("change", updateAnsweredCount);
  });

  window.addEventListener("scroll", updateScrollProgress, { passive: true });
});
