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

// Sửa lại notify để toast luôn ở góc trên bên phải, không che nội dung chính
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
  // Đặt vị trí toast lên góc trên bên phải, margin lớn hơn
  n.style.position = 'fixed';
  n.style.top = '32px';
  n.style.right = '32px';
  n.style.left = 'auto';
  n.style.bottom = 'auto';
  n.style.zIndex = 3000;
  n.style.maxWidth = '350px';
  n.style.width = 'auto';
  n.style.borderRadius = '12px';
  n.style.boxShadow = '0 4px 24px rgba(37,99,235,0.18)';
  n.style.background = type === 'success' ? 'linear-gradient(135deg, #10b981, #059669)' : type === 'error' ? 'linear-gradient(135deg, #ef4444, #dc2626)' : 'linear-gradient(135deg, #2563eb, #3b82f6)';
  n.style.color = '#fff';
  n.style.padding = '1rem 1.5rem';
  n.style.fontWeight = '500';
  n.style.fontSize = '1rem';
  n.style.opacity = 1;
  n.style.pointerEvents = 'auto';
  n.style.transition = 'opacity 0.3s';
  setTimeout(() => {
    n.style.opacity = 0;
    n.style.pointerEvents = 'none';
    n.classList.remove('active');
  }, 2500);
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

// === Chatbot Hugging Face cho bệnh viện ===
(function() {
  // const HF_API_TOKEN = 'REMOVED'; // ĐÃ XÓA TOKEN
  const HF_MODEL = 'bigscience/bloom';
  const HF_ENDPOINT = `https://api-inference.huggingface.co/models/${HF_MODEL}`;
// Giữ lại toàn bộ phần code chatbot như trước!


  if (!localStorage.getItem('token')) return;
  if (document.getElementById('hospital-chatbot-btn')) return;

  const btn = document.createElement('div');
  btn.id = 'hospital-chatbot-btn';
  btn.style.position = 'fixed';
  btn.style.right = '32px';
  btn.style.bottom = '32px';
  btn.style.zIndex = '9999';
  btn.style.width = '64px';
  btn.style.height = '64px';
  btn.style.borderRadius = '50%';
  btn.style.background = '#fff';
  btn.style.boxShadow = '0 4px 24px rgba(37,99,235,0.18)';
  btn.style.display = 'flex';
  btn.style.alignItems = 'center';
  btn.style.justifyContent = 'center';
  btn.style.cursor = 'pointer';
  btn.style.transition = 'box-shadow 0.2s';
  btn.innerHTML = `<img src="../image/logo.jpg" alt="Chatbot" style="width:48px;height:48px;border-radius:50%;object-fit:cover;">`;
  document.body.appendChild(btn);

  const chatbox = document.createElement('div');
  chatbox.id = 'hospital-chatbot-box';
  chatbox.style.position = 'fixed';
  chatbox.style.right = '32px';
  chatbox.style.bottom = '110px';
  chatbox.style.width = '350px';
  chatbox.style.maxWidth = '95vw';
  chatbox.style.height = '480px';
  chatbox.style.background = '#fff';
  chatbox.style.borderRadius = '18px';
  chatbox.style.boxShadow = '0 8px 32px rgba(37,99,235,0.18)';
  chatbox.style.display = 'none';
  chatbox.style.flexDirection = 'column';
  chatbox.style.overflow = 'hidden';
  chatbox.style.zIndex = '10000';
  chatbox.innerHTML = `
    <div style="background:#2563eb;color:#fff;padding:16px 20px;font-weight:600;font-size:1.1rem;display:flex;align-items:center;justify-content:space-between;">
      <span><img src="../image/logo.jpg" style="width:28px;height:28px;border-radius:50%;vertical-align:middle;margin-right:8px;"> Chatbot Bệnh viện</span>
      <button id="close-chatbot-btn" style="background:none;border:none;color:#fff;font-size:1.3rem;cursor:pointer;">&times;</button>
    </div>
    <div id="chatbot-messages" style="flex:1;padding:16px;overflow-y:auto;background:#f6f8fa;"></div>
    <form id="chatbot-form" style="display:flex;padding:12px 16px;border-top:1px solid #e0e7ef;background:#fff;gap:8px;">
      <input id="chatbot-input" type="text" placeholder="Nhập câu hỏi..." autocomplete="off" style="flex:1;padding:8px 12px;border-radius:8px;border:1px solid #cbd5e1;font-size:1rem;outline:none;">
      <button type="submit" style="background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-weight:600;cursor:pointer;">Gửi</button>
    </form>
  `;
  document.body.appendChild(chatbox);

  btn.onclick = () => {
    chatbox.style.display = 'flex';
    if (!chatbox.dataset.greeted) {
      setTimeout(() => {
        addMsg('Xin chào! Tôi là Chatbot Bệnh viện. Bạn cần hỗ trợ gì? Hãy đặt câu hỏi cho tôi nhé!', 'bot');
        chatbox.dataset.greeted = '1';
      }, 400);
    }
  };
  chatbox.querySelector('#close-chatbot-btn').onclick = () => { chatbox.style.display = 'none'; };

  const form = chatbox.querySelector('#chatbot-form');
  const input = chatbox.querySelector('#chatbot-input');
  const messages = chatbox.querySelector('#chatbot-messages');

  function addMsg(msg, from) {
    const div = document.createElement('div');
    div.style.margin = '8px 0';
    div.style.textAlign = from === 'user' ? 'right' : 'left';
    div.innerHTML = `<span style="display:inline-block;max-width:80%;padding:8px 12px;border-radius:12px;background:${from==='user'?'#2563eb':'#e0f2fe'};color:${from==='user'?'#fff':'#222'};font-size:1rem;">${msg}</span>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  form.onsubmit = async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    addMsg(q, 'user');
    input.value = '';
    addMsg('<i>Đang trả lời...</i>', 'bot');
    try {
      const OPENROUTER_API_KEY = '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';
      const OPENROUTER_ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions';
      const res = await fetch(OPENROUTER_ENDPOINT, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + OPENROUTER_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'openai/gpt-3.5-turbo',
          messages: [
            { role: 'system', content: 'Bạn là một chatbot AI thông minh, thân thiện, ưu tiên trả lời các câu hỏi về bệnh viện/y tế. Nếu người dùng hỏi ngoài chủ đề bệnh viện, hãy trả lời ngắn gọn, lịch sự, thân thiện và hữu ích. Luôn trả lời tự nhiên, dễ hiểu, không từ chối trừ khi nội dung không phù hợp.' },
            { role: 'user', content: q }
          ]
        })
      });
      const data = await res.json();
      messages.lastChild.remove();
      if (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) {
        addMsg(data.choices[0].message.content, 'bot');
      } else if (data.error && data.error.message) {
        addMsg('Lỗi từ OpenRouter: ' + data.error.message, 'bot');
      } else {
        addMsg('Xin lỗi, tôi không thể trả lời câu hỏi này.', 'bot');
      }
    } catch (err) {
      messages.lastChild.remove();
      addMsg('Có lỗi khi kết nối OpenRouter: ' + (err.message || err), 'bot');
    }
  };
})();

// === Quản lý người dùng: Lọc vai trò, đếm số lượng, xác thực đổi quyền ===

// Lưu danh sách người dùng toàn cục để filter
window.allUsers = [];
window.filteredUsers = [];
window.selectedRoleFilter = 'all';
window.pendingRoleChange = null;

// Làm đẹp mục số lượng vai trò
function showRoleFilter(users) {
  const filterContainer = document.getElementById('role-filter-container');
  if (!filterContainer) return;
  filterContainer.style.display = 'block';
  // Đếm số lượng từng vai trò
  const counts = {admin: 0, doctor: 0, receptionist: 0, patient: 0};
  users.forEach(u => { if (counts[u.Role] !== undefined) counts[u.Role]++; });
  document.getElementById('role-counts').innerHTML = `
    <span style="display:inline-block;margin-right:8px;font-weight:600;">Số lượng:</span>
    <span class='badge badge-admin'>Admin: ${counts.admin}</span>
    <span class='badge badge-doctor'>Bác sĩ: ${counts.doctor}</span>
    <span class='badge badge-receptionist'>Lễ tân: ${counts.receptionist}</span>
    <span class='badge badge-patient'>Bệnh nhân: ${counts.patient}</span>
  `;
}

// Lọc danh sách theo vai trò
function filterUsersByRole(role) {
  window.selectedRoleFilter = role;
  if (role === 'all') {
    window.filteredUsers = [...window.allUsers];
  } else {
    window.filteredUsers = window.allUsers.filter(u => (u.Role || u.role) === role);
  }
  renderAdminUserTableFiltered();
  showRoleFilter(window.allUsers);
  // Đặt lại giá trị select filter đúng với filter hiện tại
  const filter = document.getElementById('role-filter');
  if (filter) filter.value = role;
}

// Render lại bảng người dùng theo filter
window.renderAdminUserTableFiltered = function() {
  document.getElementById('admin-user-table').style.display = 'block';
  // Ẩn loading khi đã render bảng
  const sectionHeader = document.getElementById('section-title');
  if (sectionHeader) sectionHeader.style.display = 'none';
  const users = window.filteredUsers;
  const getInitials = name => name ? name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2) : '?';
  const formatDate = d => d ? new Date(d).toLocaleDateString('vi-VN') : '-';
  let tableHtml = `
    <div class="user-management-container">
      <div class="table-header">
        <div class="table-title"><i class="fas fa-users-cog"></i> Quản lý người dùng</div>
        <div class="table-stats"><i class="fas fa-users"></i> Tổng cộng: ${users.length} người dùng</div>
      </div>
      <div class="user-table-wrap">
        <table class="user-table">
          <thead>
            <tr>
              <th><i class="fas fa-user"></i> Người dùng</th>
              <th><i class="fas fa-envelope"></i> Email</th>
              <th><i class="fas fa-phone"></i> Điện thoại</th>
              <th><i class="fas fa-calendar"></i> Ngày sinh</th>
              <th><i class="fas fa-venus-mars"></i> Giới tính</th>
              <th><i class="fas fa-map-marker-alt"></i> Địa chỉ</th>
              <th><i class="fas fa-user-tag"></i> Vai trò</th>
              <th><i class="fas fa-building"></i> Khoa phụ trách</th>
              <th><i class="fas fa-cogs"></i> Thao tác</th>
            </tr>
          </thead>
          <tbody>
  `;
  users.forEach(user => {
    const userId = user.UserId || user.id;
    const userRole = user.Role || user.role;
    tableHtml += `
      <tr>
        <td><div class="user-avatar-cell"><div class="user-avatar">${getInitials(user.FullName)}</div><div><div class="user-name">${user.FullName||'Chưa cập nhật'}</div><div class="user-username">@${user.Username}</div></div></div></td>
        <td>${user.Email||'-'}</td>
        <td>${user.Phone||'-'}</td>
        <td>${formatDate(user.DateOfBirth)}</td>
        <td>${user.Gender||'-'}</td>
        <td>${user.Address||'-'}</td>
        <td>
          <select class="role-select" data-uid="${userId}" data-oldrole="${userRole}">
            <option value="admin" ${userRole==='admin'?'selected':''}>Admin</option>
            <option value="doctor" ${userRole==='doctor'?'selected':''}>Bác sĩ</option>
            <option value="receptionist" ${userRole==='receptionist'?'selected':''}>Lễ tân</option>
            <option value="patient" ${userRole==='patient'?'selected':''}>Bệnh nhân</option>
          </select>
        </td>
        <td>${userRole==='doctor'?(user.DepartmentName||'-'):'-'}</td>
        <td><div class="user-actions"><button class="btn btn-danger btn-sm" onclick="deleteUser(${userId}, '${user.FullName||user.Username}')" title="Xóa người dùng"><i class="fas fa-trash"></i></button></div></td>
      </tr>
    `;
  });
  tableHtml += '</tbody></table></div></div>';
  document.getElementById('admin-user-table').innerHTML = tableHtml;

  // Đảm bảo modal nhập mật khẩu admin luôn có trong DOM
  if (!document.getElementById('admin-password-modal')) {
    const modalHtml = `
    <div id="admin-password-modal" class="modal">
      <div class="modal-content">
        <div class="modal-icon">
          <i class="fas fa-lock"></i>
        </div>
        <h3 class="modal-title">Xác thực Admin</h3>
        <p class="modal-message">Nhập mật khẩu admin để xác nhận thay đổi quyền người dùng.</p>
        <input type="password" id="admin-password-input" class="form-input" placeholder="Nhập mật khẩu admin" style="margin-bottom:1.5rem;width:100%;">
        <div class="modal-actions">
          <button class="btn btn-secondary" onclick="closeAdminPasswordModal()">
            <i class="fas fa-times"></i> Hủy
          </button>
          <button class="btn btn-primary" id="admin-password-confirm-btn">
            <i class="fas fa-check"></i> Xác nhận
          </button>
        </div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  }
  bindAdminPasswordConfirmBtn();

  // Gắn lại sự kiện onchange cho tất cả select role
  document.querySelectorAll('.role-select').forEach(select => {
    select.onchange = function(e) {
      const userId = this.getAttribute('data-uid');
      const oldRole = this.getAttribute('data-oldrole');
      const newRole = this.value;
      if (!userId || !newRole) return;
      if (newRole !== oldRole) {
        window.pendingRoleChange = {userId, newRole, oldRole};
        document.getElementById('admin-password-input').value = '';
        document.getElementById('admin-password-modal').classList.add('active');
        setTimeout(() => document.getElementById('admin-password-input').focus(), 100);
      }
    };
  });
}

// Sửa hàm renderAdminUserTable để lưu users và gọi filter
window.renderAdminUserTable = async function() {
  document.getElementById('admin-user-table').style.display = 'block';
  try {
    const response = await fetch('http://localhost:8000/users', {
      headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
    });
    if (!response.ok) throw new Error('HTTP error!');
    const users = await response.json();
    window.allUsers = users;
    window.filteredUsers = users;
    showRoleFilter(users);
    renderAdminUserTableFiltered();
    // Gắn sự kiện filter
    const filter = document.getElementById('role-filter');
    if (filter) {
      filter.onchange = e => filterUsersByRole(e.target.value);
      // Đặt lại giá trị filter đúng với filter hiện tại
      filter.value = window.selectedRoleFilter || 'all';
    }
  } catch (e) {
    document.getElementById('admin-user-table').innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i>Lỗi khi tải danh sách người dùng!</div>';
  }
}

// Khi chọn đổi quyền, hiện modal nhập mật khẩu admin
window.onRoleSelectChange = function(userId, newRole, oldRole) {
  if (newRole === oldRole) return;
  window.pendingRoleChange = {userId, newRole, oldRole};
  document.getElementById('admin-password-input').value = '';
  document.getElementById('admin-password-modal').classList.add('active');
  document.getElementById('admin-password-input').focus();
}

// Đóng modal mật khẩu admin
window.closeAdminPasswordModal = function() {
  const modal = document.getElementById('admin-password-modal');
  if (modal) modal.classList.remove('active');
  window.pendingRoleChange = null;
  // Reset lại dropdown về giá trị cũ nếu đang đổi quyền
  const {userId, oldRole} = window.pendingRoleChange || {};
  if (userId && oldRole) {
    const select = document.querySelector(`select[data-uid="${userId}"]`);
    if (select) {
      select.value = oldRole;
      select.setAttribute('data-oldrole', oldRole);
    }
  }
};

// Đảm bảo chỉ gắn 1 sự kiện xác nhận cho nút Xác nhận
function bindAdminPasswordConfirmBtn() {
  const btn = document.getElementById('admin-password-confirm-btn');
  if (!btn) return;
  // Xóa sự kiện cũ nếu có
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.onclick = async function() {
    const pwd = document.getElementById('admin-password-input').value;
    const {userId, newRole, oldRole} = window.pendingRoleChange || {};
    if (!userId || !newRole || !pwd) {
      notify('Vui lòng nhập đầy đủ thông tin!', 'error');
      return;
    }
    try {
      const body = JSON.stringify({ role: newRole, admin_password: pwd });
      const res = await fetch(`http://localhost:8000/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('token')
        },
        body
      });
      if (res.ok) {
        notify('Đổi quyền thành công!', 'success');
        closeAdminPasswordModal();
        await window.renderAdminUserTable();
      } else {
        notify('Mật khẩu admin không đúng hoặc lỗi đổi quyền!', 'error');
        // Reset lại select về giá trị cũ
        const select = document.querySelector(`select[data-uid="${userId}"]`);
        if (select) {
          select.value = oldRole;
          select.setAttribute('data-oldrole', oldRole);
        }
        closeAdminPasswordModal();
      }
    } catch (e) {
      notify('Lỗi kết nối máy chủ!', 'error');
      closeAdminPasswordModal();
    }
  };
}

// Thêm CSS badge đẹp cho số lượng vai trò
(function addRoleBadgeCSS() {
  const style = document.createElement('style');
  style.innerHTML = `
    .badge { display:inline-block; padding:4px 12px; border-radius:16px; font-size:0.95em; margin-right:8px; font-weight:600; }
    .badge-admin { background:#fee2e2; color:#b91c1c; }
    .badge-doctor { background:#d1fae5; color:#047857; }
    .badge-receptionist { background:#fef9c3; color:#b45309; }
    .badge-patient { background:#dbeafe; color:#1d4ed8; }
  `;
  document.head.appendChild(style);
})();

// === Hiển thị thông tin cá nhân cho patient/doctor ===
async function renderCurrentUserProfile() {
  const sectionHeader = document.getElementById('section-title');
  const profileInfo = document.getElementById('profile-info');
  try {
    if (sectionHeader) {
      sectionHeader.querySelector('h2').innerText = 'Đang tải...';
      sectionHeader.querySelector('p').innerText = 'Vui lòng đợi trong giây lát';
    }
    if (profileInfo) profileInfo.style.display = 'none';

    const res = await apiFetch('http://localhost:8000/users/me');
    if (!res.ok) throw new Error('Lỗi khi lấy thông tin cá nhân');
    const user = await res.json();

    // Tạo bảng Khoa phụ trách nếu là bác sĩ
    let departmentTable = '';
    if (user.Role === 'doctor' && user.DepartmentName) {
      departmentTable = `
        <div class="profile-view-card" style="min-width:260px;max-width:320px;padding:1.5rem 1rem 1.5rem 1rem;align-self:flex-start;background:#fff;box-shadow:var(--shadow-md);border-radius:18px;">
          <div class="profile-role" style="margin-bottom:1rem;">KHOA PHỤ TRÁCH</div>
          <div style="background:#f8fafc;padding:18px 14px;border-radius:12px;box-shadow:var(--shadow-sm);margin-bottom:1rem;">
            <div style="font-weight:600;">Tên khoa</div>
            <div style="margin-top:4px;">${user.DepartmentName}</div>
          </div>
          <button class="btn btn-secondary" id="edit-department-btn" style="width:100%;"><i class="fas fa-edit"></i> Chỉnh sửa khoa</button>
        </div>
      `;
    }

    // Render thông tin cá nhân và bảng khoa phụ trách (nếu có)
    if (profileInfo) {
      profileInfo.innerHTML = `
        <div class="profile-view-card" style="flex:2;min-width:320px;">
          <div class="profile-avatar">${user.FullName ? user.FullName[0] : '?'}</div>
          <div class="profile-name">${user.FullName || 'Chưa cập nhật'}</div>
          <div class="profile-role">${user.Role === 'doctor' ? 'Bác sĩ' : user.Role === 'patient' ? 'Bệnh nhân' : user.Role}</div>
          <div class="profile-info-grid">
            <div class="profile-row"><div class="profile-row-icon"><i class="fas fa-envelope"></i></div><div class="profile-row-content"><div class="profile-row-label">Email</div><div class="profile-row-value">${user.Email || '-'}</div></div></div>
            <div class="profile-row"><div class="profile-row-icon"><i class="fas fa-phone"></i></div><div class="profile-row-content"><div class="profile-row-label">Điện thoại</div><div class="profile-row-value">${user.Phone || '-'}</div></div></div>
            <div class="profile-row"><div class="profile-row-icon"><i class="fas fa-calendar"></i></div><div class="profile-row-content"><div class="profile-row-label">Ngày sinh</div><div class="profile-row-value">${formatDateVN(user.DateOfBirth)}</div></div></div>
            <div class="profile-row"><div class="profile-row-icon"><i class="fas fa-venus-mars"></i></div><div class="profile-row-content"><div class="profile-row-label">Giới tính</div><div class="profile-row-value">${user.Gender || '-'}</div></div></div>
            <div class="profile-row"><div class="profile-row-icon"><i class="fas fa-map-marker-alt"></i></div><div class="profile-row-content"><div class="profile-row-label">Địa chỉ</div><div class="profile-row-value">${user.Address || '-'}</div></div></div>
          </div>
          <div class="form-actions" style="justify-content:flex-end;margin-top:2rem;">
            <button class="btn btn-primary" id="edit-profile-btn"><i class="fas fa-edit"></i> Chỉnh sửa thông tin</button>
          </div>
        </div>
        ${departmentTable}
      `;
      profileInfo.style.display = 'flex';
      profileInfo.style.gap = '2rem';
      if (sectionHeader) sectionHeader.style.display = 'none';
    }

    // Gắn sự kiện cho nút chỉnh sửa thông tin cá nhân
    const editBtnEl = document.getElementById('edit-profile-btn');
    if (editBtnEl) {
      editBtnEl.onclick = function() {
        renderEditProfileForm(user);
      };
    }
    // Gắn sự kiện cho nút chỉnh sửa khoa phụ trách
    const editDeptBtn = document.getElementById('edit-department-btn');
    if (editDeptBtn) {
      editDeptBtn.onclick = function() {
        renderEditDepartmentForm(user);
      };
    }
  } catch (e) {
    if (sectionHeader) {
      sectionHeader.querySelector('h2').innerText = 'Lỗi!';
      sectionHeader.querySelector('p').innerText = 'Không thể tải thông tin cá nhân.';
    }
    if (profileInfo) profileInfo.style.display = 'none';
  }
}

// Hàm render form chỉnh sửa thông tin cá nhân
function renderEditProfileForm(user) {
  const profileInfo = document.getElementById('profile-info');
  if (!profileInfo) return;
  profileInfo.innerHTML = `
    <form class="edit-profile-form" id="edit-profile-form">
      <div class="edit-form-title"><i class="fas fa-user-edit"></i> Chỉnh sửa thông tin cá nhân</div>
      <div class="form-grid">
        <div class="form-group">
          <label class="form-label">Họ tên</label>
          <input class="form-input" name="FullName" value="${user.FullName||''}" required />
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input class="form-input" name="Email" value="${user.Email||''}" type="email" required />
        </div>
        <div class="form-group">
          <label class="form-label">Điện thoại</label>
          <input class="form-input" name="Phone" value="${user.Phone||''}" />
        </div>
        <div class="form-group">
          <label class="form-label">Ngày sinh</label>
          <input class="form-input" name="DateOfBirth" value="${user.DateOfBirth ? user.DateOfBirth.split('T')[0] : ''}" type="date" />
        </div>
        <div class="form-group">
          <label class="form-label">Giới tính</label>
          <select class="form-select" name="Gender">
            <option value="">-- Chọn --</option>
            <option value="Nam" ${user.Gender==='Nam'?'selected':''}>Nam</option>
            <option value="Nữ" ${user.Gender==='Nữ'?'selected':''}>Nữ</option>
            <option value="Khác" ${user.Gender==='Khác'?'selected':''}>Khác</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Địa chỉ</label>
          <input class="form-input" name="Address" value="${user.Address||''}" />
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-success"><i class="fas fa-save"></i> Lưu thay đổi</button>
        <button type="button" class="btn btn-secondary" id="cancel-edit-profile"><i class="fas fa-times"></i> Hủy</button>
      </div>
    </form>
  `;
  // Gắn sự kiện submit
  document.getElementById('edit-profile-form').onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
      FullName: form.FullName.value,
      Email: form.Email.value,
      Phone: form.Phone.value,
      DateOfBirth: form.DateOfBirth.value,
      Gender: form.Gender.value,
      Address: form.Address.value
    };
    try {
      const res = await apiFetch('http://localhost:8000/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error('Lỗi khi cập nhật thông tin');
      notify('Cập nhật thành công!', 'success');
      renderCurrentUserProfile();
    } catch (err) {
      notify('Cập nhật thất bại!', 'error');
    }
  };
  // Gắn sự kiện hủy
  document.getElementById('cancel-edit-profile').onclick = function() {
    renderCurrentUserProfile();
  };
}

// Hàm render form chỉnh sửa khoa phụ trách cho bác sĩ
async function renderEditDepartmentForm(user) {
  const profileInfo = document.getElementById('profile-info');
  if (!profileInfo) return;
  // Lấy danh sách khoa
  let departments = [];
  try {
    const res = await apiFetch('http://localhost:8000/departments');
    if (res.ok) departments = await res.json();
  } catch {}
  profileInfo.innerHTML = `
    <form class="edit-profile-form" id="edit-department-form" style="max-width:400px;margin:auto;">
      <div class="edit-form-title"><i class="fas fa-building"></i> Chỉnh sửa khoa phụ trách</div>
      <div class="form-group">
        <label class="form-label">Chọn khoa</label>
        <select class="form-select" name="DepartmentId" required>
          <option value="">-- Chọn khoa --</option>
          ${departments.map(d => `<option value="${d.DepartmentId}" ${user.DepartmentName===d.Name?'selected':''}>${d.Name}</option>`).join('')}
        </select>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-success"><i class="fas fa-save"></i> Lưu thay đổi</button>
        <button type="button" class="btn btn-secondary" id="cancel-edit-department"><i class="fas fa-times"></i> Hủy</button>
      </div>
    </form>
  `;
  document.getElementById('edit-department-form').onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const departmentId = form.DepartmentId.value;
    if (!departmentId) return notify('Vui lòng chọn khoa!', 'error');
    try {
      // Gọi API cập nhật khoa phụ trách cho bác sĩ (giả sử backend có endpoint này)
      const res = await apiFetch('http://localhost:8000/doctor_departments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ DoctorId: user.UserId, DepartmentId: Number(departmentId), IsPrimary: true })
      });
      if (!res.ok) throw new Error('Lỗi khi cập nhật khoa');
      notify('Cập nhật khoa thành công!', 'success');
      renderCurrentUserProfile();
    } catch (err) {
      notify('Cập nhật khoa thất bại!', 'error');
    }
  };
  document.getElementById('cancel-edit-department').onclick = function() {
    renderCurrentUserProfile();
  };
}

// Hàm format ngày về dd/mm/yyyy
function formatDateVN(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString('vi-VN');
}

// === Tab navigation: Tổng quan & Thông báo ===
document.addEventListener('DOMContentLoaded', function() {
  const navOverview = document.getElementById('nav-overview');
  const navNotifications = document.getElementById('nav-notifications');
  const sectionOverview = document.getElementById('section-overview');
  const sectionNotifications = document.getElementById('section-notifications');
  if (navOverview && navNotifications && sectionOverview && sectionNotifications) {
    navOverview.addEventListener('click', function(e) {
      e.preventDefault();
      navOverview.classList.add('active');
      navNotifications.classList.remove('active');
      sectionOverview.style.display = '';
      sectionNotifications.style.display = 'none';
    });
    navNotifications.addEventListener('click', async function(e) {
      e.preventDefault();
      navOverview.classList.remove('active');
      navNotifications.classList.add('active');
      sectionOverview.style.display = 'none';
      sectionNotifications.style.display = '';
      await renderNotifications();
    });
  }
  // --- Tự động chọn khoa khi chọn bác sĩ trong modal tạo lịch hẹn ---
  const doctorSelect = document.getElementById('modal-doctor');
  const departmentSelect = document.getElementById('modal-department');
  const deptText = document.getElementById('doctor-department-text');
  if (doctorSelect && departmentSelect) {
    doctorSelect.addEventListener('change', async function() {
      const doctorId = this.value;
      if (!doctorId) {
        departmentSelect.value = '';
        if (deptText) deptText.textContent = '';
        return;
      }
      // Gọi API lấy khoa chính của bác sĩ
      try {
        const res = await apiFetch(`http://localhost:8000/doctor_departments?doctor_id=${doctorId}`);
        if (!res.ok) throw new Error('Không lấy được khoa');
        const data = await res.json();
        if (data && data.length && data[0].DepartmentId) {
          departmentSelect.value = String(data[0].DepartmentId);
          if (deptText) deptText.textContent = data[0].Department && data[0].Department.Name ? `Khoa: ${data[0].Department.Name}` : '';
        } else {
          departmentSelect.value = '';
          if (deptText) deptText.textContent = '';
        }
      } catch {
        departmentSelect.value = '';
        if (deptText) deptText.textContent = '';
      }
    });
  }
});

async function renderNotifications() {
  const list = document.getElementById('notifications-list');
  if (!list) return;
  list.innerHTML = '<div class="empty-state"><i class="fas fa-spinner fa-spin"></i><p>Đang tải thông báo...</p></div>';
  try {
    const res = await apiFetch('http://localhost:8000/notifications');
    if (!res.ok) throw new Error('Không thể lấy thông báo');
    const data = await res.json();
    if (!data.length) {
      list.innerHTML = '<div class="empty-state"><i class="fas fa-bell-slash"></i><p>Không có thông báo nào.</p></div>';
      return;
    }
    list.innerHTML = data.map(n => `
      <div class="stat-card" style="margin-bottom:1rem;align-items:flex-start;">
        <div class="stat-icon ${n.Type === 'success' ? 'completed' : n.Type === 'info' ? 'in-progress' : 'waiting'}">
          <i class="fas fa-bell"></i>
        </div>
        <div class="stat-content" style="text-align:left;">
          <h4 style="margin:0 0 0.25rem 0;font-size:1.1rem;">${n.Title}</h4>
          <div style="color:#64748b;font-size:0.95rem;">${n.Message}</div>
          <div style="font-size:0.85rem;color:#94a3b8;margin-top:0.5rem;">${formatDateVN(n.CreatedAt)}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Lỗi tải thông báo!</p></div>';
  }
}

// Sửa lại DOMContentLoaded để gọi renderCurrentUserProfile cho non-admin
(function() {
  const oldHandler = window.onload;
  window.addEventListener('DOMContentLoaded', function() {
    const role = localStorage.getItem('role');
    if (role === 'admin') {
      document.getElementById('role-filter-container').style.display = 'block';
      window.renderAdminUserTable();
    } else {
      renderCurrentUserProfile();
    }
    // XÓA đoạn hiển thị vai trò với icon kế bên nút Đăng xuất, trả lại giao diện header như cũ
    const roleInfo = document.getElementById('current-role-info');
    if (roleInfo) roleInfo.remove();
    if (typeof oldHandler === 'function') oldHandler();
  });
})();
