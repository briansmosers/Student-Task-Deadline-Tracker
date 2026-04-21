function updateCountdowns() {
    const elements = document.querySelectorAll('[data-countdown]');
    const now = new Date();

    elements.forEach(el => {
        const due = new Date(el.dataset.countdown);
        const diff = due - now;

        if (diff <= 0) {
            el.textContent = 'Overdue!';
            el.className = 'small fw-bold mb-0 text-danger';
            return;
        }

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

        if (days > 0) {
            el.textContent = `${days}d ${hours}h remaining`;
            el.className = 'small fw-bold mb-0 text-primary';
        } else if (hours > 0) {
            el.textContent = `${hours}h ${mins}m remaining`;
            el.className = 'small fw-bold mb-0 text-warning';
        } else {
            el.textContent = `${mins}m remaining`;
            el.className = 'small fw-bold mb-0 text-danger';
        }
    });
}

updateCountdowns();
setInterval(updateCountdowns, 30000);
