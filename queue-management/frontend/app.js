// Địa chỉ API và WebSocket backend
const API_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws/queue';

// Dữ liệu queue thực tế
let queueData = {
    queue: [],
    currentServing: null,
    servedCount: 0,
    waitingCount: 0,
    avgWaitTime: 7
};

function updateCustomerUI() {
    const currentServingElement = document.getElementById('current-serving');
    if (currentServingElement) {
        currentServingElement.textContent = queueData.currentServing ? 
            `Số ${queueData.currentServing.Position}` : '--';
    }
    
    const waitingList = document.getElementById('waiting-list');
    if (waitingList) {
    waitingList.innerHTML = '';
        queueData.queue.forEach(entry => {
        const li = document.createElement('li');
            li.textContent = `Số ${entry.Position}`;
        waitingList.appendChild(li);
    });
    }
    
    const estimateTimeElement = document.getElementById('estimate-time');
    if (estimateTimeElement) {
        estimateTimeElement.textContent = `${queueData.queue.length * queueData.avgWaitTime} phút`;
    }
}

function updateStaffUI() {
    const currentServingElement = document.getElementById('current-serving');
    if (currentServingElement) {
        currentServingElement.textContent = queueData.currentServing ? 
            `Số ${queueData.currentServing.Position}` : '--';
    }
    
    const waitingList = document.getElementById('waiting-list');
    if (waitingList) {
    waitingList.innerHTML = '';
        queueData.queue.forEach(entry => {
        const li = document.createElement('li');
            li.textContent = `Số ${entry.Position}`;
        waitingList.appendChild(li);
    });
    }
}

function updateAdminUI() {
    const servedCountElement = document.getElementById('served-count');
    if (servedCountElement) {
        servedCountElement.textContent = queueData.servedCount;
    }
    
    const avgWaitTimeElement = document.getElementById('avg-wait-time');
    if (avgWaitTimeElement) {
        avgWaitTimeElement.textContent = queueData.avgWaitTime + ' phút';
    }
    
    const adminList = document.getElementById('admin-waiting-list');
    if (adminList) {
    adminList.innerHTML = '';
        queueData.queue.forEach(entry => {
        const li = document.createElement('li');
            li.textContent = `Số ${entry.Position}`;
        adminList.appendChild(li);
    });
}
}

async function setupStaffActions() {
    const nextBtn = document.getElementById('next-btn');
    const doneBtn = document.getElementById('done-btn');
    const skipBtn = document.getElementById('skip-btn');
    
    if (nextBtn) {
        nextBtn.onclick = async () => {
            if (queueData.queue.length > 0) {
                const nextEntry = queueData.queue[0];
                try {
                    await fetch(`${API_URL}/queue_entries/${nextEntry.EntryId}/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'serving' })
                    });
                } catch (error) {
                    console.error('Error updating status:', error);
                }
            }
        };
    }
    
    if (doneBtn) {
        doneBtn.onclick = async () => {
            if (queueData.currentServing) {
                try {
                    await fetch(`${API_URL}/queue_entries/${queueData.currentServing.EntryId}/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'done' })
                    });
                } catch (error) {
                    console.error('Error updating status:', error);
                }
            }
        };
    }
    
    if (skipBtn) {
        skipBtn.onclick = async () => {
            if (queueData.currentServing) {
                try {
                    await fetch(`${API_URL}/queue_entries/${queueData.currentServing.EntryId}/status`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: 'skipped' })
                    });
                } catch (error) {
                    console.error('Error updating status:', error);
                }
            }
        };
    }
}

function updateAllUI() {
    if (window.pageRole === 'customer') updateCustomerUI();
    if (window.pageRole === 'staff') updateStaffUI();
    if (window.pageRole === 'admin') updateAdminUI();
}

function connectWebSocket() {
    let ws;
    try {
        ws = new WebSocket(WS_URL);
        ws.onopen = () => {
            console.log('Đã kết nối WebSocket');
        };
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.currentServing !== undefined) queueData.currentServing = data.currentServing;
                if (data.queue !== undefined) queueData.queue = data.queue;
                if (data.servedCount !== undefined) queueData.servedCount = data.servedCount;
                if (data.waitingCount !== undefined) queueData.waitingCount = data.waitingCount;
                if (data.avgWaitTime !== undefined) queueData.avgWaitTime = data.avgWaitTime;
                updateAllUI();
            } catch (e) {
                console.error('Lỗi dữ liệu WebSocket:', e);
            }
        };
        ws.onerror = (err) => {
            console.warn('WebSocket lỗi:', err);
        };
        ws.onclose = () => {
            console.warn('WebSocket đóng, thử lại sau 3s...');
            setTimeout(connectWebSocket, 3000);
        };
    } catch (e) {
        console.warn('Không thể kết nối WebSocket:', e);
    }
}

// Hàm để lấy dữ liệu từ API
async function fetchQueueData() {
    try {
        const [queuesResponse, statsResponse, entriesResponse] = await Promise.all([
            fetch(`${API_URL}/queues`),
            fetch(`${API_URL}/stats`),
            fetch(`${API_URL}/queue_entries`)
        ]);
        
        if (queuesResponse.ok && statsResponse.ok && entriesResponse.ok) {
            const entries = await entriesResponse.json();
            const stats = await statsResponse.json();
            
            // Cập nhật queue data
            queueData.queue = entries.filter(e => e.Status === 'waiting').map(e => ({
                EntryId: e.EntryId,
                Position: e.Position
            }));
            
            queueData.currentServing = entries.find(e => e.Status === 'serving') ? {
                EntryId: entries.find(e => e.Status === 'serving').EntryId,
                Position: entries.find(e => e.Status === 'serving').Position
            } : null;
            
            queueData.servedCount = stats.servedCount;
            queueData.waitingCount = stats.waitingCount;
            queueData.avgWaitTime = stats.avgWaitTime;
            
            updateAllUI();
        }
    } catch (error) {
        console.error('Error fetching queue data:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Lấy dữ liệu ban đầu từ API
    fetchQueueData();
    
    // Cập nhật UI
    updateAllUI();
    
    // Setup actions cho staff
    if (window.pageRole === 'staff') setupStaffActions();
    
    // Kết nối WebSocket
    connectWebSocket();
    
    // Cập nhật dữ liệu mỗi 30 giây
    setInterval(fetchQueueData, 30000);
});
