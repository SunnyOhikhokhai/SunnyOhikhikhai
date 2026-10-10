/*
 * FINPLAN – small progressive enhancements (vanilla JavaScript).
 * Every page still works without JavaScript; this file only makes it nicer:
 *   - mobile menu toggle
 *   - dismissible messages
 *   - step-by-step form navigation
 *   - show/hide steps that depend on another answer
 *   - add/remove custom line-item rows
 *   - live currency symbol next to money inputs
 *   - print button
 */
(function () {
  "use strict";

  /* ---- Mobile navigation ---------------------------------------------- */
  function initMenu() {
    var toggle = document.querySelector("[data-menu-toggle]");
    var sidebar = document.getElementById("sidebar");
    var backdrop = document.querySelector("[data-menu-close]");
    if (!toggle || !sidebar) return;

    function setOpen(open) {
      sidebar.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (backdrop) backdrop.hidden = !open;
      if (open) {
        var first = sidebar.querySelector("a, button");
        if (first) first.focus();
      }
    }
    toggle.addEventListener("click", function () {
      setOpen(!sidebar.classList.contains("is-open"));
    });
    if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && sidebar.classList.contains("is-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  /* ---- Dismissible messages -------------------------------------------- */
  function initDismiss() {
    document.querySelectorAll("[data-dismiss]").forEach(function (button) {
      button.addEventListener("click", function () {
        var alert = button.closest(".alert");
        if (alert) alert.remove();
      });
    });
  }

  /* ---- Print button --------------------------------------------------- */
  function initPrint() {
    document.querySelectorAll("[data-print]").forEach(function (button) {
      button.addEventListener("click", function () { window.print(); });
    });
  }

  /* ---- Currency symbol ------------------------------------------------ */
  function initCurrency(form) {
    var dataNode = document.getElementById("currency-symbols");
    var select = form.querySelector("select[name='currency']");
    if (!dataNode || !select) return;
    var symbols = JSON.parse(dataNode.textContent);
    function update() {
      var symbol = symbols[select.value] || "";
      form.querySelectorAll("[data-currency-symbol]").forEach(function (node) {
        node.textContent = symbol;
      });
    }
    select.addEventListener("change", update);
    form._updateCurrency = update;
    update();
  }

  /* ---- Custom line items --------------------------------------------- */
  function initLineItems(form) {
    form.querySelectorAll("[data-line-items]").forEach(function (group) {
      var rows = group.querySelector("[data-rows]");
      var template = group.querySelector("template[data-row-template]");
      var add = group.querySelector("[data-add-row]");
      if (!rows || !template || !add) return;
      add.addEventListener("click", function () {
        var fragment = template.content.cloneNode(true);
        rows.appendChild(fragment);
        var inputs = rows.querySelectorAll("[data-row]");
        var last = inputs[inputs.length - 1];
        if (form._updateCurrency) form._updateCurrency();
        if (last) {
          var first = last.querySelector("input");
          if (first) first.focus();
        }
      });
      group.addEventListener("click", function (event) {
        var remove = event.target.closest("[data-remove-row]");
        if (!remove) return;
        var row = remove.closest("[data-row]");
        if (row) row.remove();
        add.focus();
      });
    });
  }

  /* ---- Conditional steps ---------------------------------------------- */
  function conditionMet(form, node) {
    var name = node.getAttribute("data-show-if");
    if (!name) return true;
    var field = form.querySelector("[name='" + name + "']");
    if (!field) return true;
    var allowed = (node.getAttribute("data-show-values") || "").split(",");
    return allowed.indexOf(field.value) !== -1;
  }

  /* ---- Stepper -------------------------------------------------------- */
  function initStepper(form) {
    var steps = Array.prototype.slice.call(form.querySelectorAll("[data-step]"));
    var tabs = Array.prototype.slice.call(form.querySelectorAll("[data-step-tab]"));
    var stepper = form.querySelector(".stepper");
    if (!steps.length || !stepper) return;
    form.classList.add("is-enhanced-steps");
    stepper.classList.add("is-enhanced");

    function visibleSteps() {
      return steps.filter(function (step) { return conditionMet(form, step); });
    }

    var current = null;

    function refresh() {
      var visible = visibleSteps();
      if (visible.indexOf(current) === -1) current = visible[0];
      var currentIndex = visible.indexOf(current);
      steps.forEach(function (step) {
        var shown = visible.indexOf(step) !== -1;
        step.hidden = step !== current;
        step.classList.toggle("step-hidden", !shown);
        var count = step.querySelector("[data-step-count]");
        if (count && shown) count.textContent = "Step " + (visible.indexOf(step) + 1) + " of " + visible.length;
        var prev = step.querySelector("[data-prev]");
        var next = step.querySelector("[data-next]");
        var idx = visible.indexOf(step);
        if (prev) prev.style.visibility = idx <= 0 ? "hidden" : "visible";
        if (next) next.style.display = idx === visible.length - 1 ? "none" : "";
      });
      tabs.forEach(function (tab) {
        var number = tab.getAttribute("data-step-tab");
        var step = form.querySelector("[data-step='" + number + "']");
        var idx = visible.indexOf(step);
        tab.hidden = idx === -1;
        tab.classList.toggle("is-current", step === current);
        tab.classList.toggle("is-done", idx !== -1 && idx < currentIndex);
        var button = tab.querySelector("button");
        if (button) {
          if (step === current) button.setAttribute("aria-current", "step");
          else button.removeAttribute("aria-current");
          var num = button.querySelector(".stepper-num");
          if (num && idx !== -1) num.textContent = idx + 1;
        }
      });
    }

    function go(step, focus) {
      current = step;
      refresh();
      if (focus) {
        var heading = step.querySelector(".step-title");
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          heading.focus();
        }
        step.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    form.addEventListener("click", function (event) {
      var visible = visibleSteps();
      var index = visible.indexOf(current);
      if (event.target.closest("[data-next]") && index < visible.length - 1) {
        go(visible[index + 1], true);
      } else if (event.target.closest("[data-prev]") && index > 0) {
        go(visible[index - 1], true);
      } else {
        var goto = event.target.closest("[data-goto]");
        if (goto) go(form.querySelector("[data-step='" + goto.getAttribute("data-goto") + "']"), true);
      }
    });
    form.addEventListener("change", function (event) {
      if (event.target.tagName === "SELECT") refresh();
    });

    // Start on the first step with a validation error, otherwise the first step.
    var errored = steps.filter(function (step) {
      return conditionMet(form, step) && step.querySelector(".field-error");
    })[0];
    current = errored || visibleSteps()[0];
    refresh();
    if (errored) go(errored, true);

    // Hidden steps that do not apply should not block submission or save stale data.
    form.addEventListener("submit", function () {
      steps.forEach(function (step) {
        if (!conditionMet(form, step)) {
          step.querySelectorAll("input, select, textarea").forEach(function (input) { input.disabled = true; });
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMenu();
    initDismiss();
    initPrint();
    document.querySelectorAll("form[data-stepper]").forEach(function (form) {
      initCurrency(form);
      initLineItems(form);
      initStepper(form);
    });
  });
})();
