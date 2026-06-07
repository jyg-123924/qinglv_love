function triggerLoveEffect() {
  const overlay = document.getElementById('love-effect');
  if (!overlay) return;
  overlay.classList.remove('hidden');

  const hearts = ['💕', '❤️', '💖', '💗', '💝', '🌸'];
  for (let i = 0; i < 30; i++) {
    setTimeout(() => {
      const el = document.createElement('div');
      el.className = 'heart-particle';
      el.textContent = hearts[Math.floor(Math.random() * hearts.length)];
      el.style.left = Math.random() * 100 + 'vw';
      el.style.top = (80 + Math.random() * 20) + 'vh';
      el.style.fontSize = (1 + Math.random() * 1.5) + 'rem';
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 2000);
    }, i * 80);
  }

  setTimeout(() => overlay.classList.add('hidden'), 3500);
}

window.triggerLoveEffect = triggerLoveEffect;



document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash-success').forEach(el => {
    if (el.textContent.includes('爱的特效') || el.textContent.includes('双方都打卡')) {
      triggerLoveEffect();
    }
  });
});
