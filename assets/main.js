// 主题切换（记忆到 localStorage）
(function () {
  var root = document.documentElement;
  var saved = localStorage.getItem('theme');
  if (saved) root.setAttribute('data-theme', saved);
  var btn = document.getElementById('themeToggle');
  if (btn) {
    btn.addEventListener('click', function () {
      var cur = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', cur);
      localStorage.setItem('theme', cur);
    });
  }
})();

// 复制链接
function copyLink() {
  navigator.clipboard.writeText(window.location.href).then(function() {
    var btn = document.querySelector('.share-btn');
    var orig = btn.textContent;
    btn.textContent = '已复制!';
    btn.style.background = '#4CAF50';
    setTimeout(function() { btn.textContent = orig; btn.style.background = ''; }, 2000);
  });
}
