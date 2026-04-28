document.addEventListener("DOMContentLoaded", () => {
    const menuRoot = document.querySelector("[data-pub-menu]");
    if (!menuRoot) {
        return;
    }

    const toggle = menuRoot.querySelector(".pub-menu-toggle");
    if (!toggle) {
        return;
    }

    const closeMenu = () => {
        menuRoot.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
    };

    toggle.addEventListener("click", () => {
        const open = menuRoot.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    document.addEventListener("click", (event) => {
        if (!menuRoot.contains(event.target)) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
        }
    });
});
