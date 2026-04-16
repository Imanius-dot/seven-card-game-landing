const scrollTopBtn = document.getElementById("scrollTopBtn");
const subscribeForm = document.getElementById("subscribeForm");
const successMessage = document.getElementById("successMessage");
const tiltCards = document.querySelectorAll(".card-tilt");
const revealSections = document.querySelectorAll(".reveal");

if (scrollTopBtn) {
  scrollTopBtn.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });
}

if (subscribeForm && successMessage) {
  subscribeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(subscribeForm);
    const email = String(formData.get("email") || "").trim();

    if (!email) {
      successMessage.textContent = "Please enter a valid email address.";
      return;
    }

    try {
      const subscribeUrl = window.SUBSCRIBE_URL || "/subscribe";
      const response = await fetch(subscribeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        successMessage.textContent = data.error || "Could not subscribe right now. Try again.";
        return;
      }
    } catch (error) {
      successMessage.textContent = "Connection error. Please try again in a moment.";
      return;
    }

    successMessage.textContent = "🎉 You’re in! Get ready — the game begins soon.";
    subscribeForm.reset();
  });
}

tiltCards.forEach((card) => {
  card.addEventListener("mousemove", (event) => {
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const rotateX = -((y / rect.height) - 0.5) * 8;
    const rotateY = ((x / rect.width) - 0.5) * 10;
    card.style.transform = `perspective(700px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg)`;
  });

  card.addEventListener("mouseleave", () => {
    card.style.transform = "perspective(700px) rotateX(0deg) rotateY(0deg)";
  });
});

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  revealSections.forEach((section) => observer.observe(section));
} else {
  revealSections.forEach((section) => section.classList.add("visible"));
}
