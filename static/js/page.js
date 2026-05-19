document.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector(".nav");
  const navLinks = document.querySelector("#navLinks");

  if (nav && navLinks) {
    let navToggle =
      document.querySelector("#navToggle") ||
      document.querySelector(".nav-toggle");

    // Si el botón hamburguesa no existe en el HTML, lo crea automáticamente
    if (!navToggle) {
      navToggle = document.createElement("button");
      navToggle.id = "navToggle";
      navToggle.className = "nav-toggle";
      navToggle.type = "button";
      navToggle.setAttribute("aria-label", "Abrir menú");
      navToggle.setAttribute("aria-controls", "navLinks");
      navToggle.setAttribute("aria-expanded", "false");

      navToggle.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
      `;

      nav.insertBefore(navToggle, navLinks);
    }

    const openMenu = () => {
      navLinks.classList.add("is-open");
      navToggle.classList.add("is-active");
      navToggle.setAttribute("aria-expanded", "true");
      navToggle.setAttribute("aria-label", "Cerrar menú");
      document.body.classList.add("menu-open");
    };

    const closeMenu = () => {
      navLinks.classList.remove("is-open");
      navToggle.classList.remove("is-active");
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "Abrir menú");
      document.body.classList.remove("menu-open");
    };

    const toggleMenu = () => {
      const isOpen = navLinks.classList.contains("is-open");

      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    };

    navToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleMenu();
    });

    navLinks.querySelectorAll("a, button").forEach((item) => {
      item.addEventListener("click", () => {
        closeMenu();
      });
    });

    document.addEventListener("click", (event) => {
      const clickedInsideNav = nav.contains(event.target);

      if (!clickedInsideNav) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeMenu();
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 760) {
        closeMenu();
      }
    });
  }

  const revealElements = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.14,
      }
    );

    revealElements.forEach((element) => {
      observer.observe(element);
    });
  } else {
    revealElements.forEach((element) => {
      element.classList.add("is-visible");
    });
  }
});