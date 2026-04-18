document.addEventListener("DOMContentLoaded", function () {
  const statsSection = document.getElementById("stats-section");
  if (!statsSection) {
    return;
  }

  const counters = statsSection.querySelectorAll("[data-target]");
  if (!counters.length) {
    return;
  }

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const parseTarget = function (rawTarget) {
    const target = String(rawTarget || "0").trim();
    const hasPlus = target.endsWith("+");
    const numericPart = hasPlus ? target.slice(0, -1) : target;
    const numericValue = parseFloat(numericPart);
    const isDecimal = numericPart.includes(".");
    return {
      raw: target,
      hasPlus: hasPlus,
      numericValue: Number.isNaN(numericValue) ? 0 : numericValue,
      isDecimal: isDecimal
    };
  };

  const formatValue = function (value, targetMeta, forceFinal) {
    let output;
    if (targetMeta.isDecimal) {
      output = (forceFinal ? targetMeta.numericValue : value).toFixed(1);
    } else {
      output = String(Math.floor(forceFinal ? targetMeta.numericValue : value));
    }

    if (targetMeta.hasPlus) {
      output += "+";
    }
    return output;
  };

  const animateCounter = function (counter, duration) {
    const targetMeta = parseTarget(counter.getAttribute("data-target"));
    if (prefersReducedMotion) {
      counter.textContent = targetMeta.raw;
      return;
    }

    const startTime = performance.now();

    const step = function (currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentValue = targetMeta.numericValue * progress;
      counter.textContent = formatValue(currentValue, targetMeta, progress >= 1);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };

    requestAnimationFrame(step);
  };

  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) {
          return;
        }

        counters.forEach(function (counter) {
          animateCounter(counter, 2000);
        });

        observer.disconnect();
      });
    },
    { threshold: 0.3 }
  );

  observer.observe(statsSection);
});
