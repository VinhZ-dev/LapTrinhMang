// app.js - Logic chung cho toàn bộ frontend bệnh viện

// Kiểm tra token và phân quyền, chuyển hướng nếu chưa đăng nhập
function checkAuth(requiredRole) {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');
  if (!token) window.location.href = 'login.html';
  if (requiredRole && role !== requiredRole) window.location.href = 'index.html';
}

// Gọi API có token
async function apiFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  options.headers = options.headers || {};
  options.headers['Authorization'] = 'Bearer ' + token;
  return fetch(url, options);
}

// Đăng xuất
function logout() {
  localStorage.clear();
  window.location.href = 'login.html';
}

// Hiển thị thông báo
function notify(msg, type = 'info') {
  let n = document.getElementById('notification');
  if (!n) {
    n = document.createElement('div');
    n.id = 'notification';
    n.className = 'notification';
    document.body.appendChild(n);
  }
  n.innerText = msg;
  n.classList.add('active');
  setTimeout(() => n.classList.remove('active'), 2500);
}

// Hiển thị loading
function showLoading(show) {
  let l = document.getElementById('loading-overlay');
  if (!l) {
    l = document.createElement('div');
    l.id = 'loading-overlay';
    l.className = 'loading-overlay';
    l.innerHTML = '<div class="loading-spinner"><span>Đang tải...</span></div>';
    document.body.appendChild(l);
  }
  l.style.display = show ? 'flex' : 'none';
} 