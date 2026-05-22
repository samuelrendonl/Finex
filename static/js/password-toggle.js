document.addEventListener("DOMContentLoaded", () => {
  const passwordInputs = document.querySelectorAll(
    'input[type="password"], input[data-secure-password]',
  );

  passwordInputs.forEach((input) => {
    input.type = "password";
    input.removeAttribute("data-secure-password");

    if (input.parentElement.classList.contains("password-field")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "password-field";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "password-toggle";
    button.setAttribute("aria-label", "Mostrar contraseña");

    button.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M2.25 12s3.75-6.75 9.75-6.75S21.75 12 21.75 12 18 18.75 12 18.75 2.25 12 2.25 12Z"></path>
        <circle cx="12" cy="12" r="3"></circle>
        <path class="eye-slash" d="M4 4l16 16"></path>
      </svg>
    `;

    wrapper.appendChild(button);

    button.addEventListener("mousedown", (e) => {
      e.preventDefault();
    });

    button.addEventListener("click", () => {
      const start = input.selectionStart;
      const end = input.selectionEnd;
      const isHidden = input.type === "password";

      input.type = isHidden ? "text" : "password";

      button.classList.toggle("is-visible", isHidden);
      button.setAttribute(
        "aria-label",
        isHidden ? "Ocultar contraseña" : "Mostrar contraseña",
      );

      input.focus();

      if (start !== null && end !== null) {
        input.setSelectionRange(start, end);
      }
    });
  });
});
