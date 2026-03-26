/* ═══════════════════════════════════════════════════════════════
   FaceAttend — Premium Dashboard JavaScript
   ═══════════════════════════════════════════════════════════════ */

// ─── Particles System ────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particlesCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  const PARTICLE_COUNT = 40;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 2 + 0.5;
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.speedY = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.3 + 0.05;
      this.fadeDir = Math.random() > 0.5 ? 1 : -1;
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      this.opacity += this.fadeDir * 0.002;
      if (this.opacity > 0.35) this.fadeDir = -1;
      if (this.opacity < 0.03) this.fadeDir = 1;
      if (this.x < -10 || this.x > canvas.width + 10 || this.y < -10 || this.y > canvas.height + 10) {
        this.reset();
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(176, 228, 204, ${this.opacity})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(64, 138, 113, ${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }
  animate();
})();

// ─── Toast Notification System ─────────────────────────────────
let toastContainer = null;
function showToast(message, type = 'info', duration = 3500) {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }

  const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span style="font-size:1.1rem">${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Live Clock ──────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('liveClock');
  if (!el) return;
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  }
  tick();
  setInterval(tick, 1000);
}
startClock();

// ─── Sidebar Toggle ──────────────────────────────────────────────
(function initSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
    });
  }
})();

// ─── Role Tabs (Auth Pages) ──────────────────────────────────────
(function initRoleTabs() {
  const tabs = document.querySelectorAll('.role-tab');
  const roleInput = document.getElementById('roleInput');
  const studentFields = document.getElementById('studentFields');

  if (!tabs.length || !roleInput) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const role = tab.dataset.role;
      roleInput.value = role;
      if (studentFields) {
        studentFields.style.display = role === 'student' ? 'block' : 'none';
        const rollInput = studentFields.querySelector('input');
        if (rollInput) rollInput.required = role === 'student';
      }
    });
  });
})();

// ─── Tab Switching ───────────────────────────────────────────────
(function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      document.querySelectorAll('.report-panel').forEach(p => p.style.display = 'none');
      const panel = document.getElementById(tabId);
      if (panel) panel.style.display = 'block';

      // Load weekly if needed
      if (tabId === 'weeklyReport') loadWeeklyReport();
    });
  });
})();

// ─── Animated Counter ────────────────────────────────────────────
function animateCounter(element, target, suffix = '') {
  if (!element) return;
  const start = 0;
  const duration = 1200;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (target - start) * eased);
    element.textContent = current + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ─── Progress Ring Animation ─────────────────────────────────────
(function animateRings() {
  document.querySelectorAll('.ring-fill').forEach(ring => {
    const pct = parseFloat(ring.dataset.percentage) || 0;
    const circumference = 2 * Math.PI * 80; // r=80
    const offset = circumference - (pct / 100) * circumference;
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference;
    setTimeout(() => {
      ring.style.strokeDashoffset = offset;
    }, 300);
  });
})();

// ─── Chart.js Helpers ────────────────────────────────────────────
const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      labels: { color: 'rgba(176, 228, 204, 0.6)', font: { family: 'Inter', size: 11 } }
    }
  },
  scales: {
    x: {
      ticks: { color: 'rgba(176, 228, 204, 0.4)', font: { family: 'Inter', size: 10 } },
      grid: { color: 'rgba(64, 138, 113, 0.08)' }
    },
    y: {
      ticks: { color: 'rgba(176, 228, 204, 0.4)', font: { family: 'Inter', size: 10 } },
      grid: { color: 'rgba(64, 138, 113, 0.08)' }
    }
  }
};

function createGradient(ctx, color1, color2) {
  const grad = ctx.createLinearGradient(0, 0, 0, 300);
  grad.addColorStop(0, color1);
  grad.addColorStop(1, color2);
  return grad;
}

// Dashboard charts (staff)
function initDashboardCharts(stats) {
  if (!stats || typeof Chart === 'undefined') return;

  // Weekly Trend Bar Chart
  const barCtx = document.getElementById('weeklyBarChart');
  if (barCtx) {
    const grad = createGradient(barCtx.getContext('2d'), 'rgba(64,138,113,0.8)', 'rgba(64,138,113,0.1)');
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: stats.week_labels,
        datasets: [
          {
            label: 'Present',
            data: stats.week_present,
            backgroundColor: grad,
            borderColor: '#408A71',
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: 'Absent',
            data: stats.week_absent,
            backgroundColor: 'rgba(255,107,107,0.2)',
            borderColor: 'rgba(255,107,107,0.5)',
            borderWidth: 1,
            borderRadius: 6,
          }
        ]
      },
      options: { ...chartDefaults, plugins: { ...chartDefaults.plugins } }
    });
  }

  // Attendance Line Chart
  const lineCtx = document.getElementById('weeklyLineChart');
  if (lineCtx) {
    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: stats.week_labels,
        datasets: [{
          label: 'Present',
          data: stats.week_present,
          borderColor: '#408A71',
          backgroundColor: 'rgba(64,138,113,0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#B0E4CC',
          pointBorderColor: '#408A71',
          pointRadius: 4,
          pointHoverRadius: 7,
        }]
      },
      options: { ...chartDefaults }
    });
  }

  // Pie Chart
  const pieCtx = document.getElementById('todayPieChart');
  if (pieCtx) {
    const presentCount = stats.present_today || 0;
    const absentCount = stats.absent_today || 0;
    new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: ['Present', 'Absent'],
        datasets: [{
          data: [presentCount, absentCount],
          backgroundColor: ['rgba(64,138,113,0.7)', 'rgba(255,107,107,0.5)'],
          borderColor: ['#408A71', '#ff6b6b'],
          borderWidth: 2,
          hoverOffset: 8,
        }]
      },
      options: {
        responsive: true,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: 'rgba(176, 228, 204, 0.6)', font: { family: 'Inter', size: 11 }, padding: 16 }
          }
        }
      }
    });
  }
}

// ─── Monthly Report ──────────────────────────────────────────────
let barChartInstance = null, lineChartInstance = null, pieChartInstance = null;

async function generateMonthlyReport() {
  const month = document.getElementById('reportMonth')?.value;
  const year = document.getElementById('reportYear')?.value;
  const dept = document.getElementById('reportDept')?.value || '';

  if (!month || !year) { showToast('Select month and year', 'warning'); return; }

  try {
    const res = await fetch(`/api/report/monthly?month=${month}&year=${year}&dept=${dept}`);
    const data = await res.json();

    if (!data.success) { showToast('No data found', 'warning'); return; }

    // Show output
    const output = document.getElementById('monthlyReportOutput');
    if (output) output.style.display = 'block';

    // Title
    const title = document.getElementById('mTitle');
    if (title) title.textContent = `${data.month_name} ${data.year} — Attendance Report`;

    // Summary
    animateCounter(document.getElementById('mTotal'), data.summary.total_working_days);
    animateCounter(document.getElementById('mPresent'), data.summary.present_days);
    animateCounter(document.getElementById('mAbsent'), data.summary.absent_days);
    animateCounter(document.getElementById('mPct'), data.summary.percentage, '%');

    // Charts
    if (typeof Chart !== 'undefined') {
      if (barChartInstance) barChartInstance.destroy();
      if (lineChartInstance) lineChartInstance.destroy();
      if (pieChartInstance) pieChartInstance.destroy();

      const barCtx = document.getElementById('barChart');
      if (barCtx) {
        barChartInstance = new Chart(barCtx, {
          type: 'bar',
          data: {
            labels: data.daily_labels,
            datasets: [
              { label: 'Present', data: data.daily_present, backgroundColor: 'rgba(64,138,113,0.6)', borderColor: '#408A71', borderWidth: 1, borderRadius: 4 },
              { label: 'Absent', data: data.daily_absent, backgroundColor: 'rgba(255,107,107,0.3)', borderColor: 'rgba(255,107,107,0.5)', borderWidth: 1, borderRadius: 4 }
            ]
          },
          options: chartDefaults
        });
      }

      const lineCtx = document.getElementById('lineChart');
      if (lineCtx) {
        lineChartInstance = new Chart(lineCtx, {
          type: 'line',
          data: {
            labels: data.daily_labels,
            datasets: [{
              label: 'Attendance %',
              data: data.daily_percentage,
              borderColor: '#B0E4CC',
              backgroundColor: 'rgba(176,228,204,0.08)',
              fill: true, tension: 0.4,
              pointBackgroundColor: '#B0E4CC',
              pointBorderColor: '#285A48',
              pointRadius: 3,
            }]
          },
          options: { ...chartDefaults,
            scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, min: 0, max: 100 } }
          }
        });
      }

      const pieCtx = document.getElementById('pieChart');
      if (pieCtx) {
        pieChartInstance = new Chart(pieCtx, {
          type: 'doughnut',
          data: {
            labels: ['Present', 'Absent'],
            datasets: [{
              data: [data.summary.present_days, data.summary.absent_days],
              backgroundColor: ['rgba(64,138,113,0.7)', 'rgba(255,107,107,0.5)'],
              borderColor: ['#408A71', '#ff6b6b'],
              borderWidth: 2, hoverOffset: 8,
            }]
          },
          options: { responsive: true, cutout: '65%', plugins: { legend: { position: 'bottom', labels: { color: 'rgba(176,228,204,0.6)', font: { family: 'Inter', size: 11 }, padding: 16 } } } }
        });
      }
    }

    // Table
    const tbody = document.getElementById('monthlyTableBody');
    if (tbody) {
      if (data.records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><p>No records for this period</p></td></tr>';
      } else {
        tbody.innerHTML = data.records.map(r => `
          <tr>
            <td>${r.date}</td>
            <td>${r.student_name}</td>
            <td>${r.roll_no}</td>
            <td>${r.time}</td>
            <td><span class="badge badge-${r.status}">${r.status}</span></td>
          </tr>
        `).join('');
      }
    }

    showToast('Report generated', 'success');
  } catch (err) {
    showToast('Failed to generate report', 'error');
    console.error(err);
  }
}

function downloadMonthlyPDF() {
  const month = document.getElementById('reportMonth')?.value;
  const year = document.getElementById('reportYear')?.value;
  if (!month || !year) { showToast('Generate a report first', 'warning'); return; }
  window.open(`/api/report/monthly/pdf?month=${month}&year=${year}`, '_blank');
  showToast('Opening PDF...', 'info');
}

// ─── Weekly Report ───────────────────────────────────────────────
async function loadWeeklyReport() {
  try {
    const res = await fetch('/api/report/weekly');
    const data = await res.json();
    const tbody = document.getElementById('weeklyReportBody');
    if (!tbody) return;

    if (data.records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted)">No records this week</td></tr>';
    } else {
      tbody.innerHTML = data.records.map(r => `
        <tr>
          <td>${r.student_name}</td>
          <td>${r.roll_no}</td>
          <td>${r.department}</td>
          <td>${r.date}</td>
          <td>${r.time}</td>
          <td><span class="badge badge-${r.status}">${r.status}</span></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Weekly report error:', err);
  }
}

// ─── Download Reports ────────────────────────────────────────────
function downloadReport(type) {
  const date = document.getElementById('reportDate')?.value || '';
  window.open(`/api/report/download?type=${type}&date=${date}`, '_blank');
  showToast(`Downloading ${type} report...`, 'info');
}

// ─── Camera / Face Recognition ───────────────────────────────────
let cameraStream = null;
let recognitionInterval = null;
let captureCount = 0;
const MAX_CAPTURES = 5;

// Face Capture Page
(function initFaceCapture() {
  const startBtn = document.getElementById('startCameraBtn');
  const captureBtn = document.getElementById('captureBtn');
  const doneBtn = document.getElementById('doneBtn');
  const video = document.getElementById('cameraFeed');
  const canvas = document.getElementById('captureCanvas');

  if (!startBtn || !video) return;
  // Only run on face capture page
  if (!captureBtn) return;

  startBtn.addEventListener('click', async () => {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } });
      video.srcObject = cameraStream;
      startBtn.style.display = 'none';
      if (captureBtn) captureBtn.style.display = 'inline-flex';
      showToast('Camera started! Position your face', 'success');
    } catch (err) {
      showToast('Camera access denied', 'error');
    }
  });

  if (captureBtn) {
    captureBtn.addEventListener('click', async () => {
      if (!canvas || !video) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg', 0.8);

      captureBtn.disabled = true;
      captureBtn.textContent = '⏳ Saving...';

      try {
        const res = await fetch('/api/save-face', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: imageData })
        });
        const data = await res.json();

        if (data.success) {
          captureCount++;
          const counter = document.getElementById('captureCounter');
          if (counter) counter.textContent = `${captureCount}/${MAX_CAPTURES}`;
          const progress = document.getElementById('captureProgress');
          if (progress) progress.style.width = `${(captureCount / MAX_CAPTURES) * 100}%`;

          showToast(`Face ${captureCount}/${MAX_CAPTURES} captured!`, 'success');

          if (captureCount >= MAX_CAPTURES) {
            captureBtn.style.display = 'none';
            if (doneBtn) doneBtn.style.display = 'inline-flex';
            if (cameraStream) cameraStream.getTracks().forEach(t => t.stop());
            showToast('All faces captured! You can proceed.', 'success');
          } else {
            captureBtn.disabled = false;
            captureBtn.textContent = '📸 Capture Face';
          }
        } else {
          showToast(data.message || 'Capture failed', 'error');
          captureBtn.disabled = false;
          captureBtn.textContent = '📸 Capture Face';
        }
      } catch {
        showToast('Network error', 'error');
        captureBtn.disabled = false;
        captureBtn.textContent = '📸 Capture Face';
      }
    });
  }

  if (doneBtn) {
    doneBtn.addEventListener('click', () => {
      window.location.href = '/student/dashboard';
    });
  }
})();

// Face Recognition (Staff)
(function initRecognition() {
  const startBtn = document.getElementById('startRecognition');
  const stopBtn = document.getElementById('stopRecognition');
  const video = document.getElementById('cameraFeed');
  const canvas = document.getElementById('captureCanvas');
  const statusEl = document.getElementById('recognitionStatus');

  if (!startBtn || !stopBtn || !video) return;
  // Only on take-attendance page (has startRecognition btn)
  if (!document.getElementById('subjectSelect')) return;

  startBtn.addEventListener('click', async () => {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } });
      video.srcObject = cameraStream;
      startBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      if (statusEl) statusEl.innerHTML = '<span style="color:var(--success)">● Scanning...</span>';
      showToast('Camera started — scanning faces', 'success');

      // Auto-scan every 3 seconds
      recognitionInterval = setInterval(() => recognizeFace(video, canvas), 3000);
    } catch (err) {
      showToast('Camera access denied', 'error');
    }
  });

  stopBtn.addEventListener('click', () => {
    if (cameraStream) cameraStream.getTracks().forEach(t => t.stop());
    if (recognitionInterval) clearInterval(recognitionInterval);
    startBtn.style.display = 'inline-flex';
    stopBtn.style.display = 'none';
    if (statusEl) statusEl.innerHTML = '<span style="color:var(--text-muted)">⏸ Camera stopped</span>';
    showToast('Recognition stopped', 'info');
  });
})();

async function recognizeFace(video, canvas) {
  if (!video || !canvas) return;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const imageData = canvas.toDataURL('image/jpeg', 0.8);

  const subject = document.getElementById('subjectSelect')?.value || 'General';
  const statusEl = document.getElementById('recognitionStatus');

  try {
    if (statusEl) statusEl.innerHTML = '<span style="color:var(--warning)">⟳ Analyzing...</span>';

    const res = await fetch('/api/recognize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: imageData, subject })
    });
    const data = await res.json();

    if (data.success) {
      addRecognizedStudent(data);
      showToast(data.message, data.already_marked ? 'info' : 'success');
      if (statusEl) statusEl.innerHTML = '<span style="color:var(--success)">● Scanning...</span>';
    } else {
      if (statusEl) statusEl.innerHTML = '<span style="color:var(--success)">● Scanning...</span>';
    }
  } catch {
    if (statusEl) statusEl.innerHTML = '<span style="color:var(--danger)">● Connection error</span>';
  }
}

function addRecognizedStudent(data) {
  const container = document.getElementById('recognizedStudents');
  if (!container) return;

  // Remove empty state
  const emptyState = container.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  // Check duplicate
  if (container.querySelector(`[data-name="${data.student_name}"]`)) return;

  const item = document.createElement('div');
  item.className = 'recognized-item';
  item.dataset.name = data.student_name;
  item.innerHTML = `
    <div class="r-avatar">${data.student_name[0]}</div>
    <div class="r-info">
      <h4>${data.student_name}</h4>
      <p>${data.roll_no} · ${data.department} · Confidence: ${data.confidence}%</p>
    </div>
    <div class="r-badge">${data.already_marked ? 'Already Marked' : '✓ Marked'}</div>
  `;
  container.insertBefore(item, container.firstChild);
}

// ─── Scroll Animations (IntersectionObserver) ────────────────────
(function initScrollAnimations() {
  const elements = document.querySelectorAll('.animate-in');
  if (!elements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  elements.forEach(el => {
    el.style.animationPlayState = 'paused';
    // Immediate play for visible elements
    if (el.getBoundingClientRect().top < window.innerHeight) {
      el.style.animationPlayState = 'running';
    } else {
      observer.observe(el);
    }
  });
})();

// ─── Auto Refresh Dashboard ──────────────────────────────────────
(function autoRefreshDashboard() {
  // Only on staff dashboard
  if (!document.getElementById('presentCount')) return;

  setInterval(async () => {
    try {
      const res = await fetch('/api/dashboard-stats');
      const stats = await res.json();
      const pc = document.getElementById('presentCount');
      const ac = document.getElementById('absentCount');
      if (pc) pc.textContent = stats.present_today;
      if (ac) pc.textContent = stats.absent_today;
    } catch { /* silent */ }
  }, 60000);
})();
