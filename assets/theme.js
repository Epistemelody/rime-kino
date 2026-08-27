(function () {
  const THEME_KEY = "kino-theme";
  const LANG_KEY = "kino-lang";

  function systemDark() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function applyTheme(mode) {
    let next = mode;
    if (next !== "light" && next !== "dark") {
      const stored = localStorage.getItem(THEME_KEY);
      next = stored === "dark" || stored === "light"
        ? stored
        : (systemDark() ? "dark" : "light");
    } else {
      localStorage.setItem(THEME_KEY, next);
    }
    document.documentElement.dataset.theme = next;
    document.documentElement.style.colorScheme = next;
    document.querySelectorAll("[data-theme-switch]").forEach((el) => {
      el.setAttribute("aria-checked", next === "dark" ? "true" : "false");
      el.setAttribute(
        "aria-label",
        next === "dark" ? "Switch to light theme" : "Switch to dark theme"
      );
    });
  }

  function applyLang(lang) {
    const prev = localStorage.getItem(LANG_KEY) || "zh";
    const next = lang || prev || "zh";
    localStorage.setItem(LANG_KEY, next);
    document.documentElement.lang = next === "en" ? "en" : "zh-CN";
    document.documentElement.dataset.lang = next;
    document.querySelectorAll("[data-lang-option]").forEach((el) => {
      el.setAttribute(
        "aria-current",
        el.getAttribute("data-lang-option") === next ? "true" : "false"
      );
    });
    if (lang && prev !== next && /docs\.html/.test(location.pathname)) {
      remapDocsHash(next);
    }
  }

  function remapDocsHash(next) {
    const pairs = [
      ["README.en", "README"],
      ["docs/kino.en", "docs/kino"],
      ["docs/README.en", "docs/README"],
      ["docs/drafts/README.en", "docs/drafts/README"],
    ];
    let hash = (location.hash || "#/").replace(/^#\/?/, "").replace(/\.md$/, "");
    if (!hash || hash === "/") hash = next === "en" ? "README.en" : "README";
    for (const [en, zh] of pairs) {
      if (next === "en" && (hash === zh || hash === zh + ".md")) {
        location.hash = "#/" + en;
        return;
      }
      if (next === "zh" && (hash === en || hash === en + ".md")) {
        location.hash = "#/" + zh;
        return;
      }
    }
  }

  function setMenuOpen(menu, open) {
    menu.classList.toggle("open", open);
    const toggle = menu.querySelector("[data-menu-toggle]");
    toggle?.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function closeMenus() {
    document.querySelectorAll("[data-menu]").forEach((menu) => setMenuOpen(menu, false));
  }

  window.kinoApplyTheme = applyTheme;
  window.kinoApplyLang = applyLang;

  applyTheme();
  applyLang();

  document.querySelectorAll("[data-menu]").forEach((menu) => {
    const toggle = menu.querySelector("[data-menu-toggle]");
    menu.addEventListener("mouseenter", () => setMenuOpen(menu, true));
    menu.addEventListener("mouseleave", () => setMenuOpen(menu, false));
    toggle?.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      setMenuOpen(menu, !menu.classList.contains("open"));
    });
  });

  document.addEventListener("click", (ev) => {
    const sw = ev.target.closest("[data-theme-switch]");
    if (sw) {
      applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
      return;
    }
    const langOpt = ev.target.closest("[data-lang-option]");
    if (langOpt) {
      applyLang(langOpt.getAttribute("data-lang-option"));
      closeMenus();
      return;
    }
    if (!ev.target.closest("[data-menu]")) closeMenus();
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") closeMenus();
  });
})();
