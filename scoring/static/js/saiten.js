// scoring/static/js/saiten.js

const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const fileNameDisplay = document.getElementById('fileName');
const toggleCameraBtn = document.getElementById('toggleCameraBtn');
const cameraArea = document.getElementById('cameraArea');
const cameraVideo = document.getElementById('cameraVideo');
const takePhotoBtn = document.getElementById('takePhotoBtn');
const scoringForm = document.getElementById('scoringForm');
const loadingOverlay = document.getElementById('loadingOverlay');
const submitBtn = document.getElementById('submitBtn');
const hamburger = document.getElementById('hamburgerMenu');
const sidebar = document.getElementById('sidebar');

// ランキング用
const openRankingViewBtn = document.getElementById('openRankingViewBtn'); // 新設
const rankingViewModal = document.getElementById('rankingViewModal');     // 新設
const closeRankingViewBtn = document.getElementById('closeRankingViewBtn'); // 新設
const showRegisterModalBtn = document.getElementById('showRegisterModalBtn'); // 名前変更
const registerModal = document.getElementById('registerModal');           // 名前変更
const cancelRegisterBtn = document.getElementById('cancelRegisterBtn');   // 名前変更
const confirmRegisterBtn = document.getElementById('confirmRegisterBtn'); // 名前変更
const rankingTableBody = document.getElementById('rankingTableBody');
const deleteEntryBtn = document.getElementById('deleteEntryBtn');

let cameraStream = null;

// ... (カメラ・ファイル関連の既存コードはそのまま) ...
imageInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        fileNameDisplay.textContent = file.name;
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    } else {
        fileNameDisplay.textContent = "ファイルを選択してください";
        imagePreview.src = '';
        imagePreview.classList.add('hidden');
    }
});

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    cameraVideo.srcObject = null;
    cameraArea.classList.add('hidden');
    toggleCameraBtn.innerHTML = '<i class="fa-solid fa-camera mr-2"></i><span>カメラ起動</span>';
    toggleCameraBtn.classList.remove('bg-gray-600', 'hover:bg-gray-500');
    toggleCameraBtn.classList.add('from-pink-600', 'to-rose-600', 'hover:from-pink-500', 'hover:to-rose-500');
}

async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraVideo.srcObject = cameraStream;
        cameraArea.classList.remove('hidden');
        imagePreview.classList.add('hidden');
        toggleCameraBtn.innerHTML = '<i class="fa-solid fa-xmark mr-2"></i><span>カメラを閉じる</span>';
        toggleCameraBtn.classList.remove('from-pink-600', 'to-rose-600', 'hover:from-pink-500', 'hover:to-rose-500');
        toggleCameraBtn.classList.add('bg-gray-600', 'hover:bg-gray-500');
    } catch (err) {
        alert("カメラを起動できませんでした: " + err);
    }
}

toggleCameraBtn.addEventListener('click', () => {
    if (cameraStream) stopCamera();
    else startCamera();
});

takePhotoBtn.addEventListener('click', () => {
    if (!cameraStream) return;
    const canvas = document.createElement('canvas');
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg");
    imagePreview.src = dataUrl;
    imagePreview.classList.remove('hidden');
    fileNameDisplay.textContent = "カメラで撮影した画像";
    fetch(dataUrl)
        .then(res => res.arrayBuffer())
        .then(buffer => {
            const file = new File([buffer], "camera.jpg", { type: "image/jpeg" });
            const dt = new DataTransfer();
            dt.items.add(file);
            imageInput.files = dt.files;
        });
    stopCamera();
});

scoringForm.addEventListener('submit', function(event) {
    if (!imageInput.files.length) {
        alert("画像を選択するか、カメラで撮影してください。");
        event.preventDefault();
        return;
    }
    loadingOverlay.classList.remove('hidden');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-3"></i>採点中...';
    submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
});

hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('-translate-x-full');
    hamburger.classList.toggle('open');
});

// ▼▼▼ ランキング関連処理 ▼▼▼

// ランキングデータ取得
async function fetchRanking() {
    rankingTableBody.innerHTML = '<tr><td colspan="4" class="text-center py-4">読み込み中...</td></tr>';
    try {
        const res = await fetch('/scoring/api/ranking');
        const data = await res.json();
        
        rankingTableBody.innerHTML = '';
        if (data.length === 0) {
            rankingTableBody.innerHTML = '<tr><td colspan="4" class="text-center py-4">データがありません</td></tr>';
            return;
        }
        
        data.forEach((entry, index) => {
            let rankIcon = `<span class="font-bold text-gray-400">${index + 1}</span>`;
            if (index === 0) rankIcon = '<i class="fa-solid fa-crown text-yellow-400 text-xl"></i>';
            if (index === 1) rankIcon = '<i class="fa-solid fa-crown text-gray-300 text-xl"></i>';
            if (index === 2) rankIcon = '<i class="fa-solid fa-crown text-amber-600 text-xl"></i>';

            const row = `
                <tr class="border-b border-gray-700 hover:bg-white/5 transition">
                    <td class="px-4 py-3 text-center">${rankIcon}</td>
                    <td class="px-4 py-3 font-bold text-white">${entry.name}</td>
                    <td class="px-4 py-3 text-pink-400 font-mono text-lg">${entry.score}</td>
                    <td class="px-4 py-3 text-sm text-gray-500">${entry.date}</td>
                </tr>
            `;
            rankingTableBody.insertAdjacentHTML('beforeend', row);
        });
    } catch (e) {
        console.error("Ranking Fetch Error:", e);
        rankingTableBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-red-400">読み込みエラー</td></tr>';
    }
}

// ① 「ランキングを見る」ボタン
if (openRankingViewBtn) {
    openRankingViewBtn.addEventListener('click', () => {
        rankingViewModal.classList.remove('hidden');
        fetchRanking(); // 開くたびに最新データを取得
    });
}

// ② ランキング閲覧モーダルを閉じる
if (closeRankingViewBtn) {
    closeRankingViewBtn.addEventListener('click', () => {
        rankingViewModal.classList.add('hidden');
    });
}

// ③ 登録ボタン（結果画面）
if (showRegisterModalBtn) {
    showRegisterModalBtn.addEventListener('click', () => {
        registerModal.classList.remove('hidden');
    });
}

// ④ 登録キャンセル
if (cancelRegisterBtn) {
    cancelRegisterBtn.addEventListener('click', () => {
        registerModal.classList.add('hidden');
    });
}

// ⑤ 登録実行
if (confirmRegisterBtn) {
    confirmRegisterBtn.addEventListener('click', async () => {
        const name = document.getElementById('rankName').value;
        const pass = document.getElementById('rankPass').value;
        const scoreElement = document.getElementById('currentScoreValue');
        
        if (!name) {
            alert('ニックネームを入力してください');
            return;
        }
        
        const score = scoreElement ? scoreElement.getAttribute('data-score') : 0;
        confirmRegisterBtn.disabled = true;
        confirmRegisterBtn.textContent = '送信中...';

        try {
            const res = await fetch('/scoring/api/ranking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, score: score, delete_pass: pass })
            });
            
            const result = await res.json();
            if (result.success) {
                alert('ランキングに登録しました！');
                registerModal.classList.add('hidden'); // 登録画面閉じる
                showRegisterModalBtn.classList.add('hidden'); // ボタン消す
                
                // すぐにランキング一覧を表示する
                rankingViewModal.classList.remove('hidden');
                fetchRanking();
                
            } else {
                alert('登録に失敗しました: ' + (result.message || '不明なエラー'));
            }
        } catch (e) {
            alert('通信エラーが発生しました');
        } finally {
            confirmRegisterBtn.disabled = false;
            confirmRegisterBtn.textContent = '同意して登録';
        }
    });
}

// ⑥ 削除実行
if (deleteEntryBtn) {
    deleteEntryBtn.addEventListener('click', async () => {
        const name = document.getElementById('delName').value;
        const pass = document.getElementById('delPass').value;
        
        if(!name || !pass) {
            alert('名前と削除パスを入力してください');
            return;
        }
        
        if(!confirm(`本当に「${name}」のデータを削除しますか？`)) return;

        try {
            const res = await fetch('/scoring/api/ranking/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, delete_pass: pass })
            });
            const result = await res.json();
            alert(result.message);
            if(result.success) fetchRanking();
        } catch(e) {
            alert('通信エラー');
        }
    });
}
