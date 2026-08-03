document.addEventListener("DOMContentLoaded", () => {
  const progressBar = document.querySelector(".loader-bar");
  const card = document.querySelector(".welcome-card");

  let progress = 0;

  const duration = 5000;
  const intervalTime = 40;

  const step = 100 / (duration / intervalTime);

  const interval = setInterval(() => {
    progress += step;

    progressBar.style.width = `${progress}%`;

    if (progress >= 100) {
      clearInterval(interval);

      card.classList.add("fade-out");

      setTimeout(() => {
        window.location.href = "/login";
      }, 600);
    }
  }, intervalTime);
});
