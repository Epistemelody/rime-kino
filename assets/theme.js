(function () {
  const THEME_KEY = "kino-theme";
  const LANG_KEY = "kino-lang";

  function systemDark() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function resolvedTheme(mode) {
    if (mode === "dark") return "dark";
    if (mode === "light") return "light";
    return systemDark() ? "dark" : "light";
  }

  function applyTheme(mode) {
    const next = mode || localStorage.getItem(THEME_KEY) || "system";
    localStorage.setItem(THEME_KEY, next);
    document.documentElement.dataset.theme = resolvedTheme(next);
    document.documentElement.dataset.themeMode = next;
    document.querySelectorAll("[data-theme-option]").forEach((el) => {
      el.setAttribute("aria-current", el.getAttribute("data-theme-option") === next ? "true" : "false");
    });
  }

  function applyLang(lang) {
    const next = lang || localStorage.getItem(LANG_KEY) || "zh";
    localStorage.setItem(LANG_KEY, next);
    document.documentElement.lang = next === "en" ? "en" : "zh-CN";
    document.documentElement.dataset.lang = next;
    document.querySelectorAll("[data-lang-option]").forEach((el) => {
      el.setAttribute("aria-current", el.getAttribute("data-lang-option") === next ? "true" : "false");
    });
    document.querySelectorAll("[data-lang-label]").forEach((el) => {
      el.textContent = next === "en" ? "English" : "简体中文";
    });
  }

  window.kinoApplyTheme = applyTheme;
  window.kinoApplyLang = applyLang;

  applyTheme();
  applyLang();

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem(THEME_KEY) || "system") === "system") applyTheme("system");
  });

  document.addEventListener("click", (ev) => {
    const themeOpt = ev.target.closest("[data-theme-option]");
    if (themeOpt) {
      applyTheme(themeOpt.getAttribute("data-theme-option"));
      themeOpt.closest("[data-menu]")?.classList.remove("open");
      return;
    }
    const langOpt = ev.target.closest("[data-lang-option]");
    if (langOpt) {
      applyLang(langOpt.getAttribute("data-lang-option"));
      langOpt.closest("[data-menu]")?.classList.remove("open");
      return;
    }
    const toggle = ev.target.closest("[data-menu-toggle]");
    document.querySelectorAll("[data-menu]").forEach((menu) => {
      if (toggle && menu.contains(toggle)) {
        menu.classList.toggle("open");
      } else {
        menu.classList.remove("open");
      }
    });
  });
})();
