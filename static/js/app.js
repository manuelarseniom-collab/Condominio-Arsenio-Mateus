document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("mainMenuDropdown")) {
        return;
    }
    const dropdowns = Array.from(document.querySelectorAll("[data-pub-menu]"));
    if (!dropdowns.length) return;

    const closeDropdown = (menuRoot) => {
        const toggle = menuRoot.querySelector(".pub-menu-toggle");
        const panel = menuRoot.querySelector(".pub-menu-panel");
        if (!toggle || !panel) return;
        menuRoot.classList.remove("open");
        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
    };

    const openDropdown = (menuRoot) => {
        const toggle = menuRoot.querySelector(".pub-menu-toggle");
        const panel = menuRoot.querySelector(".pub-menu-panel");
        if (!toggle || !panel) return;
        menuRoot.classList.add("open");
        panel.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
    };

    dropdowns.forEach((menuRoot) => {
        const toggle = menuRoot.querySelector(".pub-menu-toggle");
        const panel = menuRoot.querySelector(".pub-menu-panel");
        if (!toggle || !panel) return;

        panel.hidden = true;
        toggle.setAttribute("aria-expanded", "false");

        toggle.addEventListener("click", (event) => {
            event.stopPropagation();
            const isOpen = menuRoot.classList.contains("open");
            dropdowns.forEach(closeDropdown);
            if (!isOpen) openDropdown(menuRoot);
        });
    });

    document.addEventListener("click", (event) => {
        dropdowns.forEach((menuRoot) => {
            if (!menuRoot.contains(event.target)) closeDropdown(menuRoot);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") dropdowns.forEach(closeDropdown);
    });
});
