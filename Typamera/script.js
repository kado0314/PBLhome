// Typamera/script.js

// --- DOM要素の取得 ---
const webcam = document.getElementById('webcam');
const statusElement = document.getElementById('status');
const targetWordElement = document.getElementById('target-word');
const typingInput = document.getElementById('typing-input');
const scoreElement = document.getElementById('score');
const timerElement = document.getElementById('timer');
const feedbackElement = document.getElementById('feedback');
const startButton = document.getElementById('startButton');

// モーダル用DOM要素
const detailsButton = document.getElementById('detailsButton');
const detailsModal = document.getElementById('detailsModal');
const closeButton = document.getElementsByClassName('closeButton')[0];
const classListContainer = document.getElementById('classListContainer');

// --- 定数とゲーム状態 ---
const GAME_DURATION = 60;
let model;
let targetWord = '';
let score = 0;
let time = GAME_DURATION;
let gameInterval;
let detectionInterval;
let stream = null; 
let isGameRunning = false;
let isTargetLocked = false;

// ▼▼▼ COCO-SSD 90クラスの英語・日本語対応表 ▼▼▼
const COCO_CLASSES = {
    'person': '人', 'bicycle': '自転車', 'car': '車', 'motorcycle': 'バイク', 'airplane': '飛行機',
    'bus': 'バス', 'train': '電車', 'truck': 'トラック', 'boat': '船', 'traffic light': '信号',
    'fire hydrant': '消火栓', 'stop sign': '一時停止標識', 'parking meter': 'パーキングメーター', 'bench': 'ベンチ',
    'bird': '鳥', 'cat': '猫', 'dog': '犬', 'horse': '馬', 'sheep': '羊',
    'cow': '牛', 'elephant': '象', 'bear': '熊', 'zebra': 'シマウマ', 'giraffe': 'キリン',
    'backpack': 'リュック', 'umbrella': '傘', 'handbag': 'ハンドバッグ', 'tie': 'ネクタイ', 'suitcase': 'スーツケース',
    'frisbee': 'フリスビー', 'skis': 'スキー板', 'snowboard': 'スノーボード', 'sports ball': 'ボール', 'kite': '凧',
    'baseball bat': 'バット', 'baseball glove': 'グローブ', 'skateboard': 'スケートボード', 'surfboard': 'サーフボード',
    'tennis racket': 'テニスラケット', 'bottle': 'ボトル', 'wine glass': 'ワイングラス', 'cup': 'コップ', 'fork': 'フォーク',
    'knife': 'ナイフ', 'spoon': 'スプーン', 'bowl': 'ボウル', 'banana': 'バナナ', 'apple': 'リンゴ',
    'sandwich': 'サンドイッチ', 'orange': 'オレンジ', 'broccoli': 'ブロッコリー', 'carrot': 'ニンジン', 'hot dog': 'ホットドッグ',
    'pizza': 'ピザ', 'donut': 'ドーナツ', 'cake': 'ケーキ', 'chair': '椅子', 'couch': 'ソファ',
    'potted plant': '植木鉢', 'bed': 'ベッド', 'dining table': 'テーブル', 'toilet': 'トイレ', 'tv': 'テレビ',
    'laptop': 'ノートパソコン', 'mouse': 'マウス', 'remote': 'リモコン', 'keyboard': 'キーボード', 'cell phone': '携帯電話',
    'microwave': '電子レンジ', 'oven': 'オーブン', 'toaster': 'トースター', 'sink': '流し台', 'refrigerator': '冷蔵庫',
    'book': '本', 'clock': '時計', 'vase': '花瓶', 'scissors': 'はさみ', 'teddy bear': 'テディベア',
    'hair drier': 'ドライヤー', 'toothbrush': '歯ブラシ'
};

const ALLOWED_CLASSES = Object.keys(COCO_CLASSES);

// --- 1. 初期化とモデルロード ---
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        webcam.srcObject = null;
    }
    // Tailwindではhiddenクラスで制御しても良いが、ここはdisplayプロパティで
    webcam.style.display = 'none';
}

async function initializeApp() {
    statusElement.textContent = 'カメラを起動し、モデルをロード中です...';
    startButton.disabled = true;
    detailsButton.disabled = true;

    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.srcObject = stream;
        await new Promise(resolve => webcam.onloadedmetadata = resolve);

        model = await cocoSsd.load();
        
        statusElement.textContent = '準備完了！「ゲームスタート」を押してください。';
        startButton.disabled = false;
        detailsButton.disabled = false;
        webcam.style.display = 'block'; 
        
        populateClassList();
        
    } catch (error) {
        console.error('初期化に失敗しました:', error);
        statusElement.textContent = 'エラー: カメラを許可し、ページをリロードしてください。';
    }
}

// --- 2. ゲームのリセットと開始 ---
function resetGame() {
    clearInterval(gameInterval);
    clearInterval(detectionInterval);
    
    score = 0;
    time = GAME_DURATION;
    targetWord = '---';
    isGameRunning = false;

    scoreElement.textContent = score;
    timerElement.textContent = time;
    targetWordElement.textContent = targetWord;
    
    typingInput.value = '';
    typingInput.disabled = true;
    feedbackElement.textContent = '';
    
    startButton.textContent = 'ゲームスタート';
    startButton.disabled = false;
    detailsButton.disabled = false;
}

function startGame() {
    if (isGameRunning || !model) return;
    isGameRunning = true;
    
    startButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>ゲーム実行中...';
    startButton.disabled = true;
    detailsButton.disabled = true;
    typingInput.disabled = false;
    typingInput.focus();
    webcam.style.display = 'block';

    gameInterval = setInterval(() => {
        time--;
        timerElement.textContent = time;
        if (time <= 0) {
            endGame();
        }
    }, 1000);
    
    detectionInterval = setInterval(detectObjects, 3000);
    detectObjects(true);
    statusElement.textContent = 'ゲーム開始！カメラに映るものを入力してください。';
}

// --- 3. 物体検出 ---
async function detectObjects(forceNewWord = false) {
    if (!model || !stream) return;

    const predictions = await model.detect(webcam);
    
    const detectedClasses = predictions
        .filter(p => p.score > 0.6 && ALLOWED_CLASSES.includes(p.class))
        .map(p => p.class);

    if (detectedClasses.length > 0) {
        statusElement.textContent = `${detectedClasses.length}種類のお題候補を検出しました。`;
        
        if (forceNewWord || targetWord === '---' || !detectedClasses.includes(targetWord)) {
            setNewTargetWord(detectedClasses);
            isTargetLocked = true;
        }
    } else {
        statusElement.textContent = 'お題が見つかりません。カメラに何か映してください。';
        if (targetWord !== '---') {
            targetWord = '---';
            targetWordElement.textContent = targetWord;
        }
    }
}

// --- 4. お題の設定 ---
function setNewTargetWord(detectedClasses) {
    if (detectedClasses.length > 0) {
        const randomIndex = Math.floor(Math.random() * detectedClasses.length);
        const newWord = detectedClasses[randomIndex];
        
        targetWord = newWord;
        targetWordElement.textContent = targetWord;
        feedbackElement.textContent = 'New Target!';
        
        // アニメーション用クラスの付け外し
        targetWordElement.classList.remove('text-pink-500');
        void targetWordElement.offsetWidth; // リフロー発生
        targetWordElement.classList.add('text-pink-500');

        typingInput.value = '';
        typingInput.focus();
    }
}

// --- 5. タイピング処理 ---
typingInput.addEventListener('input', () => {
    if (targetWord === '---' || !isGameRunning) return;
    const typedText = typingInput.value.toLowerCase().trim(); // 空白削除と小文字化
    
    if (typedText === targetWord) {
        score++;
        scoreElement.textContent = score;
        feedbackElement.textContent = `⭕ Excellent!`;
        feedbackElement.className = "mt-2 text-lg font-bold min-h-[1.5em] text-green-400";
        
        isTargetLocked = false;
        detectObjects(true);
    } else if (targetWord.startsWith(typedText)) {
        feedbackElement.textContent = 'Typing...';
        feedbackElement.className = "mt-2 text-lg font-bold min-h-[1.5em] text-blue-400";
    } else {
        feedbackElement.textContent = '❌ Miss!';
        feedbackElement.className = "mt-2 text-lg font-bold min-h-[1.5em] text-red-400";
    }
});

typingInput.addEventListener('paste', (e) => e.preventDefault());
typingInput.addEventListener('copy', (e) => e.preventDefault());
typingInput.addEventListener('cut', (e) => e.preventDefault());
typingInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && (e.key === 'v' || e.key === 'V' || e.key === 'x' || e.key === 'X')) {
        e.preventDefault();
    }
});

// --- 6. ゲーム終了 ---
function endGame() {
    statusElement.textContent = `Finish! Score: ${score}`;
    alert(`ゲーム終了！あなたのスコアは ${score}点です。`);
    resetGame();
}

// --- 7. イベントリスナー ---
startButton.addEventListener('click', startGame);
window.addEventListener('beforeunload', stopCamera);

// --- 8. モーダル処理 ---
function populateClassList() {
    let htmlContent = '';
    for (const [english, japanese] of Object.entries(COCO_CLASSES)) {
        htmlContent += `<p class="bg-white/5 p-2 rounded border-l-4 border-amber-500"><strong class="text-amber-300">${english}</strong>: ${japanese}</p>`;
    }
    classListContainer.innerHTML = htmlContent;
}

function filterClassList() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    const items = document.querySelectorAll("#classListContainer p");

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(input) ? "block" : "none";
    });
}

detailsButton.addEventListener('click', () => {
    detailsModal.style.display = 'block';
});

closeButton.addEventListener('click', () => {
    detailsModal.style.display = 'none';
});

window.addEventListener('click', (event) => {
    if (event.target == detailsModal) {
        detailsModal.style.display = 'none';
    }
});


// ▼▼▼ ハンバーガーメニュー制御 (Tailwind対応) ▼▼▼
const hamburger = document.getElementById('hamburgerMenu');
const sidebar = document.getElementById('sidebar');

hamburger.addEventListener('click', () => {
    // Tailwindの -translate-x-full クラスをトグルすることで出し入れ
    sidebar.classList.toggle('-translate-x-full');
    hamburger.classList.toggle('open');
});

// 初期化
initializeApp();
