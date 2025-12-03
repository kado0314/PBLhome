// scoring/static/js/saiten.js

const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const fileNameDisplay = document.getElementById('fileName');
const toggleCameraBtn = document.getElementById('toggleCameraBtn');
const cameraArea = document.getElementById('cameraArea');
const cameraVideo = document.getElementById('cameraVideo');
const takePhotoBtn = document.getElementById('takePhotoBtn');
const switchCameraBtn = document.getElementById('switchCameraBtn'); // 追加
const scoringForm = document.getElementById('scoringForm');
const loadingOverlay = document.getElementById('loadingOverlay');
const submitBtn = document.getElementById('submitBtn');
const hamburger = document.getElementById('hamburgerMenu');
const sidebar = document.getElementById('sidebar');

// ランキング用
const openRankingViewBtn = document.getElementById('openRankingViewBtn');
const rankingViewModal = document.getElementById('rankingViewModal');
const closeRankingViewBtn = document.getElementById('closeRankingViewBtn');
const showRegisterModalBtn = document.getElementById('showRegisterModalBtn');
const registerModal = document.getElementById('registerModal');
const cancelRegisterBtn = document.getElementById('cancelRegisterBtn');
const confirmRegisterBtn = document.getElementById('confirmRegisterBtn');
const rankingTableBody = document.getElementById('rankingTableBody');
const deleteEntryBtn = document.getElementById('deleteEntryBtn');

let cameraStream = null;
let currentFacingMode = 'environment'; // デフォルトは外カメ

// ファイル選択
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

// ▼▼▼ カメラ起動・切り替えロジック ▼▼▼
async function startCamera() {
    // 既存のストリームがあれば停止
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
    }

    try {
        const constraints = { 
            video: { 
                facingMode: currentFacingMode 
            } 
        };
        
        cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        cameraVideo.srcObject = cameraStream;
        cameraArea.classList.remove('hidden');
        imagePreview.classList.add('hidden');
        
        // インカメの時だけ左右反転させる
        if (currentFacingMode === 'user') {
            cameraVideo.style.transform = "scaleX(-1)";
        } else {
            cameraVideo.style.transform = "none";
        }

        toggleCameraBtn.innerHTML = '<i class="fa-solid fa-xmark mr-2"></i><span>カメラを閉じる</span>';
        toggleCameraBtn.classList.remove('from-pink-600', 'to-rose-600', 'hover:from-pink-500', 'hover:to-rose-500');
        toggleCameraBtn.classList.add('bg-gray-600', 'hover:bg-gray-500');
    } catch (err) {
        alert("カメラを起動できませんでした: " + err);
        // エラー時はボタン状態を戻す
        stopCamera();
    }
}

// カメラ起動トグル
toggleCameraBtn.addEventListener('click', () => {
    if (cameraStream) stopCamera();
    else startCamera();
});

// カメラ切り替えボタン
if (switchCameraBtn) {
    switchCameraBtn.addEventListener('click', () => {
        // user <-> environment を切り替え
        currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
        startCamera(); // 再起動
    });
}

takePhotoBtn.addEventListener('click', () => {
    if (!cameraStream) return;
    const canvas = document.createElement('canvas');
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // インカメの時だけCanvasも反転
    if (currentFacingMode === 'user') {
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
    }
    
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

// ▼▼▼ ランキング関連 ▼▼▼

async function fetchRanking() {
    if(!rankingTableBody) return;
    try {
        const res = await fetch('/scoring/api/ranking');
        const data = await res.json();
        
        rankingTableBody.innerHTML = '';
        if (data.length === 0) {
            rankingTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4">データがありません</td></tr>';
            return;
        }
        
        data.forEach((entry, index) => {
            let rankIcon = `<span class="font-bold text-gray-400">${index + 1}</span>`;
            if (index === 0) rankIcon = '<i class="fa-solid fa-crown text-yellow-400 text-xl"></i>';
            if (index === 1) rankIcon = '<i class="fa-solid fa-crown text-gray-300 text-xl"></i>';
            if (index === 2) rankIcon = '<i class="fa-solid fa-crown text-amber-600 text-xl"></i>';

            let imageCell = '<span class="text-gray-600">-</span>';
            if (entry.image_url) {
                imageCell = `<a href="${entry.image_url}" target="_blank">
                                <img src="${entry.image_url}" alt="img" class="w-16 h-16 object-cover rounded-lg border border-gray-700 hover:border-pink-500 transition">
                             </a>`;
            }

            const row = `
                <tr class="border-b border-gray-700 hover:bg-white/5 transition">
                    <td class="px-4 py-3 text-center">${rankIcon}</td>
                    <td class="px-4 py-3 text-center">${imageCell}</td>
                    <td class="px-4 py-3 font-bold text-white">${entry.name}</td>
                    <td class="px-4 py-3 text-pink-400 font-mono text-lg">${entry.score}</td>
                    <td class="px-4 py-3 text-sm text-gray-500">${entry.date}</td>
                </tr>
            `;
            rankingTableBody.insertAdjacentHTML('beforeend', row);
        });
    } catch (e) {
        console.error("Ranking Fetch Error:", e);
        rankingTableBody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-red-400">読み込みエラー</td></tr>';
    }
}

// ページ読み込み時の処理
document.addEventListener('DOMContentLoaded', () => {
    fetchRanking();

    const scoreElement = document.getElementById('currentScoreValue');
    if (scoreElement) {
        setTimeout(() => {
            scoreElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }, 300);
    }
});

if (openRankingViewBtn) {
    openRankingViewBtn.addEventListener('click', () => {
        rankingViewModal.classList.remove('hidden');
        fetchRanking();
    });
}

if (closeRankingViewBtn) {
    closeRankingViewBtn.addEventListener('click', () => {
        rankingViewModal.classList.add('hidden');
    });
}

if (showRegisterModalBtn) {
    showRegisterModalBtn.addEventListener('click', () => {
        registerModal.classList.remove('hidden');
    });
}

if (cancelRegisterBtn) {
    cancelRegisterBtn.addEventListener('click', () => {
        registerModal.classList.add('hidden');
    });
}

if (confirmRegisterBtn) {
    confirmRegisterBtn.addEventListener('click', async () => {
        const name = document.getElementById('rankName').value;
        const pass = document.getElementById('rankPass').value;
        const scoreElement = document.getElementById('currentScoreValue');
        
        const resultImage = document.getElementById('resultImage');
        let imageData = null;
        if (resultImage) {
            imageData = resultImage.src;
        } else {
            console.error("画像が見つかりません (id='resultImage' missing)");
        }

        if (!name) {
            alert('ニックネームを入力してください');
            return;
        }

        const validPattern = /^[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+$/;
        if (!validPattern.test(name)) {
            alert('ニックネームには「文字」と「数字」のみ使用できます。\n（記号やスペースは使えません）');
            return;
        }
        if (pass && !/^[a-zA-Z0-9]+$/.test(pass)) {
            alert('パスワードは「半角英数字」のみ使用できます。');
            return;
        }
        
        const score = scoreElement ? scoreElement.getAttribute('data-score') : 0;
        confirmRegisterBtn.disabled = true;
        confirmRegisterBtn.textContent = '送信＆アップロード中...';

        try {
            const res = await fetch('/scoring/api/ranking', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: name, 
                    score: score, 
                    delete_pass: pass,
                    image_data: imageData 
                })
            });
            
            const result = await res.json();
            if (result.success) {
                alert('ランキングに登録しました！');
                registerModal.classList.add('hidden');
                if(showRegisterModalBtn) showRegisterModalBtn.classList.add('hidden');
                rankingViewModal.classList.remove('hidden');
                fetchRanking();
            } else {
                alert('登録に失敗しました: ' + (result.message || '入力内容を確認してください'));
            }
        } catch (e) {
            alert('通信エラーが発生しました');
        } finally {
            confirmRegisterBtn.disabled = false;
            confirmRegisterBtn.textContent = '同意して登録';
        }
    });
}

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
