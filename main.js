// Auto-dismiss flash messages
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .4s ease';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

// Animate bar widths on page load
window.addEventListener('load', () => {
  document.querySelectorAll('[style*="width:"]').forEach(el => {
    const w = el.style.width;
    el.style.width = '0';
    requestAnimationFrame(() => {
      el.style.transition = 'width .6s cubic-bezier(.4,0,.2,1)';
      el.style.width = w;
    });
  });
});

// Confirm dialogs are already inline; nothing else needed.
