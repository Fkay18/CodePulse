(() => {
    const toggle = document.querySelector('[data-theme-toggle]');
    const choices = document.querySelectorAll('[data-theme-choice]');
    const root = document.documentElement;

    const applyTheme = (theme) => {
        root.dataset.theme = theme;
        root.dataset.bsTheme = theme;
        localStorage.setItem('codepulse-theme', theme);

        const nextTheme = theme === 'dark' ? 'light' : 'dark';
        if (toggle) {
            toggle.setAttribute('aria-label', `Switch to ${nextTheme} mode`);
            toggle.title = `Switch to ${nextTheme} mode`;
            const sunIcon = toggle.querySelector('[data-theme-icon="sun"]');
            const moonIcon = toggle.querySelector('[data-theme-icon="moon"]');
            if (sunIcon) sunIcon.hidden = theme !== 'dark';
            if (moonIcon) moonIcon.hidden = theme !== 'light';
        }

        choices.forEach((choice) => {
            const selected = choice.dataset.themeChoice === theme;
            choice.setAttribute('aria-pressed', String(selected));
            choice.classList.toggle('is-selected', selected);
        });
    };

    applyTheme(root.dataset.theme === 'dark' ? 'dark' : 'light');

    if (toggle) {
        toggle.addEventListener('click', () => {
            applyTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
        });
    }

    choices.forEach((choice) => {
        choice.addEventListener('click', () => applyTheme(choice.dataset.themeChoice));
    });
})();