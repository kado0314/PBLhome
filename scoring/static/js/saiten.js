// scoring/static/js/saiten.js

// DOM要素の取得
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const fileNameDisplay = document.getElementById('fileName'); // 追加
const toggleCameraBtn = document.getElementById('toggleCameraBtn'); // 名前変更
const cameraArea = document.getElementById('cameraArea');
const cameraVideo = document.getElementById('cameraVideo');
const takePhotoBtn = document.getElementById('takePhotoBtn');
const scoringForm = document.getElementById('scoringForm'); // 追加
const loadingOverlay = document.getElementById('loadingOverlay'); // 追加
const submitBtn = document.getElementById('submitBtn'); // 追加
const hamburger = document.getElementById('hamburgerMenu');
const sidebar = document.getElementById('sidebar');

let cameraStream = null;

// --- ファイル選択時の処理 ---
imageInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        // ファイル名を表示
        fileNameDisplay.textContent = file.name;
        // プレビュー表示
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

// --- カメラ関連の関数 ---

// カメラを停止する関数
function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    cameraVideo.srcObject = null;
    cameraArea.classList.add('hidden');
    // ボタンの表示を戻す
    toggleCameraBtn.innerHTML = '<i class="fa-solid fa-camera mr-2"></i><span>カメラ起動</span>';
    toggleCameraBtn.classList.remove('bg-gray-600', 'hover:bg-gray-500');
    toggleCameraBtn.classList.add('from-pink-600', 'to-rose-600', 'hover:from-pink-500', 'hover:to-rose-500');
}

// カメラを起動する関数
async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraVideo.srcObject = cameraStream;
        cameraArea.classList.remove('hidden');
        imagePreview.classList.add('hidden'); // プレビューは隠す
        
        // ボタンの表示を「閉じる」に変更
        toggleCameraBtn.innerHTML = '<i class="fa-solid fa-xmark mr-2"></i><span>カメラを閉じる</span>';
        toggleCameraBtn.classList.remove('from-pink-600', 'to-rose-600', 'hover:from-pink-500', 'hover:to-rose-500');
        toggleCameraBtn.classList.add('bg-gray-600', 'hover:bg-gray-500');

    } catch (err) {
        alert("カメラを起動できませんでした: " + err);
    }
}

// ① カメラ起動/終了ボタンのトグル処理
toggleCameraBtn.addEventListener('click', () => {
    if (cameraStream) {
        stopCamera(); // 起動中なら停止
    } else {
        startCamera(); // 停止中なら起動
    }
});

// ② 「撮影する」ボタンの処理
takePhotoBtn.addEventListener('click', () => {
    if (!cameraStream) return;

    const canvas = document.createElement('canvas');
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // 映像が反転しているので、Canvasにも反転して描画
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/jpeg");

    // プレビュー表示
    imagePreview.src = dataUrl;
    imagePreview.classList.remove('hidden');
    fileNameDisplay.textContent = "カメラで撮影した画像";

    // input[type=file] にデータをセット
    fetch(dataUrl)
        .then(res => res.arrayBuffer())
        .then(buffer => {
            const file = new File([buffer], "camera.jpg", { type: "image/jpeg" });
            const dt = new DataTransfer();
            dt.items.add(file);
            imageInput.files = dt.files;
        });

    // 撮影したらカメラを自動停止
    stopCamera();
});


// --- フォーム送信時の処理 (ローディング表示) ---
scoringForm.addEventListener('submit', function(event) {
    // 画像が選択されていない場合は送信しない（HTMLのrequired属性でもいいが念のため）
    if (!imageInput.files.length) {
        alert("画像を選択するか、カメラで撮影してください。");
        event.preventDefault();
        return;
    }

    // ローディング表示
    loadingOverlay.classList.remove('hidden');
    // 送信ボタンを無効化して二重送信防止
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-3"></i>採点中...';
    submitBtn.classList.add('opacity-70', 'cursor-not-allowed');
});


// --- ハンバーガーメニュー制御 ---
hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('-translate-x-full');
    hamburger.classList.toggle('open');
});
