// Privacy/main.js

// DOM要素の取得
const video = document.getElementById('webcamVideo');
const canvas = document.getElementById('processingCanvas');
const ctx = canvas.getContext('2d');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const thresholdSlider = document.getElementById('thresholdSlider');
const thresholdValueSpan = document.getElementById('thresholdValue');
const notificationTitleInput = document.getElementById('notificationTitle');
const notificationBodyInput = document.getElementById('notificationBody');
const cooldownTimeSecInput = document.getElementById('cooldownTimeSec');
const statusDisplay = document.getElementById('statusDisplay');
const recDot = document.getElementById('recDot'); // 追加: 録画マーク

let lastFrameData = null;
let monitoringInterval = null;
let isMonitoring = false;
let chartInstance = null;

let lastNotificationTime = 0;
let hasNotifiedSinceStart = false; 

const MAX_DATA_POINTS = 50;

// =================================================================
// ユーティリティ/UI表示
// =================================================================

function updateStatusDisplay(isCooldown = false) {
    statusDisplay.className = "mt-6 p-4 rounded-lg border-2 text-center font-bold transition-colors"; // クラスリセット

    if (!isMonitoring) {
        statusDisplay.textContent = '監視停止中です';
        statusDisplay.classList.add('bg-gray-900', 'border-gray-700', 'text-gray-400');
        if(recDot) recDot.classList.add('hidden');
        return;
    }
    
    if(recDot) recDot.classList.remove('hidden');

    if (hasNotifiedSinceStart) {
        statusDisplay.textContent = '!!! 検出済み - 監視を停止してください !!!';
        statusDisplay.classList.add('status-danger');
        return;
    }

    if (isCooldown) {
        const cooldownTime = parseInt(cooldownTimeSecInput.value) || 5;
        const elapsed = Date.now() - lastNotificationTime;
        const remaining = Math.max(0, cooldownTime * 1000 - elapsed);
        
        statusDisplay.textContent = `通知クールダウン中... (${(remaining / 1000).toFixed(1)}秒 残り)`;
        statusDisplay.classList.add('cooldown-active');
    } else {
        statusDisplay.textContent = '監視中 - 異常なし';
        statusDisplay.classList.add('bg-indigo-900/50', 'border-indigo-500', 'text-indigo-200');
    }
}

// グラフ関連
thresholdSlider.addEventListener('input', () => {
    const value = parseInt(thresholdSlider.value);
    thresholdValueSpan.textContent = value;
    if (chartInstance) {
        const newThreshold = value;
        const dataSet = chartInstance.data.datasets[0].data;
        chartInstance.data.datasets[1].data = Array(dataSet.length).fill(newThreshold);
        chartInstance.update();
    }
});

function initializeChart(initialThreshold) {
    if (chartInstance) chartInstance.destroy();
    
    const ctxChart = document.getElementById('changeChart').getContext('2d');
    const thresholdLineValue = initialThreshold;
    
    chartInstance = new Chart(ctxChart, {
        type: 'line',
        data: {
            labels: Array(MAX_DATA_POINTS).fill(''),
            datasets: [{
                label: '変化レベル',
                data: [],
                borderColor: '#6366f1', // Indigo-500
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.2,
                fill: true,
                pointRadius: 0
            }, {
                label: 'しきい値',
                data: Array(MAX_DATA_POINTS).fill(thresholdLineValue),
                borderColor: '#ef4444', // Red-500
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            animation: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { display: false } // ラベル非表示
                },
                y: {
                    min: 0,
                    max: 200, 
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#9ca3af' }, // text-gray-400
                    title: {
                        display: true,
                        text: 'Pixel Difference',
                        color: '#6b7280'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e5e7eb' } // text-gray-200
                }
            },
            responsive: true,
            maintainAspectRatio: false,
        }
    });
}

function updateChart(averageChangeMagnitude) {
    if (!chartInstance) return;
    
    const dataSet = chartInstance.data.datasets[0].data;
    dataSet.push(averageChangeMagnitude);
    
    if (dataSet.length > MAX_DATA_POINTS) {
        dataSet.shift();
    }
    
    const currentThreshold = parseInt(thresholdSlider.value);
    chartInstance.data.datasets[1].data = Array(dataSet.length).fill(currentThreshold);
    
    chartInstance.update();
}


// =================================================================
// 通知機能 (Notification API)
// =================================================================

function showNotification(targetUrl) {
    const title = notificationTitleInput.value || '【通知タイトルなし】';
    const body = notificationBodyInput.value || '動きを検出しました。';

    const notification = new Notification(title, {
        body: body,
        icon: 'https://github.com/kado0314/PBLcamera/blob/main/static/image/huku.png?raw=true' 
    });

    notification.onclick = function() {
        notification.close();
        const selectedAction = document.querySelector('input[name="openAction"]:checked').value;
        if (selectedAction === 'window') {
            window.open(targetUrl, 'NotificationWindow', 'width=800,height=600,noopener=yes');
        } else {
            window.open(targetUrl, '_blank');
        }
    };
}

function triggerNotificationLocal() {
    if (hasNotifiedSinceStart) {
        updateStatusDisplay(false); 
        return;
    }
    
    const currentTime = Date.now();
    const cooldownTimeSec = parseInt(cooldownTimeSecInput.value) || 5;
    const cooldownTimeMS = cooldownTimeSec * 1000;

    if (currentTime - lastNotificationTime < cooldownTimeMS) {
        updateStatusDisplay(true); 
        return; 
    }

    const notificationUrl = document.getElementById('notificationUrl').value || 'https://www.google.com/';

    const sendAndSetFlag = () => {
        showNotification(notificationUrl);
        lastNotificationTime = currentTime;
        console.log(`!!! 通知送信: ${cooldownTimeSec}秒クールダウン !!!`);
    };

    if (Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                sendAndSetFlag();
            }
        });
    } else if (Notification.permission === 'granted') {
        sendAndSetFlag();
    }
}


// =================================================================
// 監視ロジック
// =================================================================

startButton.addEventListener('click', () => {
    if (isMonitoring) return;

    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    const initialThreshold = parseInt(thresholdSlider.value);
    initializeChart(initialThreshold);

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                startMonitoring();
                startButton.disabled = true;
                startButton.classList.add('opacity-50', 'cursor-not-allowed');
                stopButton.disabled = false;
                stopButton.classList.remove('cursor-not-allowed');
                stopButton.classList.add('bg-red-600', 'hover:bg-red-500', 'text-white');
                stopButton.classList.remove('bg-gray-600', 'text-gray-400');
            };
        })
        .catch(err => {
            console.error("Webカメラアクセスエラー:", err);
            alert("Webカメラへのアクセスを許可してください。");
        });
});

stopButton.addEventListener('click', () => {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }
    lastFrameData = null;
    isMonitoring = false;
    
    startButton.disabled = false;
    startButton.classList.remove('opacity-50', 'cursor-not-allowed');
    stopButton.disabled = true;
    stopButton.classList.add('cursor-not-allowed', 'bg-gray-600', 'text-gray-400');
    stopButton.classList.remove('bg-red-600', 'hover:bg-red-500', 'text-white');

    lastNotificationTime = 0;
    hasNotifiedSinceStart = false; 
    updateStatusDisplay(); 
});

function startMonitoring() {
    isMonitoring = true;
    lastFrameData = null;
    lastNotificationTime = 0;
    hasNotifiedSinceStart = false; 
    monitoringInterval = setInterval(processFrame, 100); 
    updateStatusDisplay(); 
}

function processFrame() {
    if (!isMonitoring) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const currentFrameData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

    if (!lastFrameData) {
        lastFrameData = new Uint8ClampedArray(currentFrameData);
        updateStatusDisplay(false); 
        return;
    }

    let totalMagnitude = 0; 
    const pixelCount = (canvas.width * canvas.height);

    for (let i = 0; i < currentFrameData.length; i += 4) {
        const diffR = Math.abs(currentFrameData[i] - lastFrameData[i]);
        const diffG = Math.abs(currentFrameData[i + 1] - lastFrameData[i + 1]);
        const diffB = Math.abs(currentFrameData[i + 2] - lastFrameData[i + 2]);
        
        totalMagnitude += (diffR + diffG + diffB);
    }

    const averageChangeMagnitude = totalMagnitude / pixelCount;
    updateChart(averageChangeMagnitude); 

    const thresholdValue = parseInt(thresholdSlider.value);
    
    const cooldownTimeSec = parseInt(cooldownTimeSecInput.value) || 5;
    const cooldownTimeMS = cooldownTimeSec * 1000;
    const isCooldownActive = Date.now() - lastNotificationTime < cooldownTimeMS;

    if (averageChangeMagnitude > thresholdValue) {
        if (!isCooldownActive) {
            console.log(`>>> 通知トリガー発動!`);
            triggerNotificationLocal(); 
        } else {
            updateStatusDisplay(true); 
        }
        lastFrameData = new Uint8ClampedArray(currentFrameData);
    } else {
        lastFrameData = new Uint8ClampedArray(currentFrameData);
        if (!isCooldownActive && isMonitoring) {
            updateStatusDisplay(false);
        } else if (isCooldownActive) {
             updateStatusDisplay(true); 
        }
    }
}
