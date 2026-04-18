window.addEventListener("scroll", function () {
  const navbar = document.getElementById("mainNavbar");
  if (!navbar) {
    return;
  }
  if (window.scrollY > 80) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const backToTop = document.createElement("button");
  backToTop.type = "button";
  backToTop.className = "back-to-top";
  backToTop.setAttribute("aria-label", "Back to top");
  backToTop.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
  document.body.appendChild(backToTop);

  window.addEventListener("scroll", function () {
    if (window.scrollY > 300) {
      backToTop.classList.add("show");
    } else {
      backToTop.classList.remove("show");
    }
  });

  backToTop.addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  const ticker = document.querySelector(".ticker-content");
  if (ticker && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    ticker.style.animationPlayState = "paused";
  }

  document.querySelectorAll("img").forEach(function (img) {
    if (!img.hasAttribute("loading")) {
      img.setAttribute("loading", "lazy");
    }
  });

  const currentPath = (window.location.pathname.replace(/\/+$/, "") || "/").toLowerCase();
  document.querySelectorAll("#mainNavbar a.nav-link, #mainNavbar .dropdown-item").forEach(function (link) {
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("javascript:")) {
      return;
    }

    const linkPath = (new URL(href, window.location.origin).pathname.replace(/\/+$/, "") || "/").toLowerCase();
    if (linkPath === currentPath) {
      link.classList.add("active");
      const dropdown = link.closest(".dropdown");
      if (dropdown) {
        const toggle = dropdown.querySelector(".dropdown-toggle");
        if (toggle) {
          toggle.classList.add("active");
        }
      }
    }
  });

  const demoForm = document.getElementById("demoBookingForm");
  if (!demoForm) {
    return;
  }

  const clearDemoErrors = function () {
    demoForm.querySelectorAll(".is-invalid").forEach(function (field) {
      field.classList.remove("is-invalid");
    });

    demoForm.querySelectorAll(".dynamic-field-error").forEach(function (node) {
      node.remove();
    });
  };

  const showFieldError = function (fieldName, message) {
    const field = demoForm.querySelector('[name="' + fieldName + '"]');
    if (!field) {
      return;
    }

    field.classList.add("is-invalid");
    const errorNode = document.createElement("div");
    errorNode.className = "invalid-feedback d-block dynamic-field-error";
    errorNode.textContent = message;
    const parent = field.parentElement;
    if (parent) {
      parent.appendChild(errorNode);
    }
  };

  demoForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearDemoErrors();

    const formData = new FormData(demoForm);
    const csrfToken = formData.get("csrf_token") || "";

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

      const data = await response.json();
      if (response.ok && (data.status === "ok" || data.status === "success")) {
        window.location.href = data.redirect || data.redirect_url || "/demo/success";
        return;
      }

      if (data.errors) {
        Object.keys(data.errors).forEach(function (key) {
          const fieldErrors = data.errors[key];
          const firstError = Array.isArray(fieldErrors) ? fieldErrors[0] : fieldErrors;
          showFieldError(key, firstError);
        });
      }
    } catch (error) {
      showFieldError("first_name", "We could not submit your request right now. Please try again.");
    }
  });
});
