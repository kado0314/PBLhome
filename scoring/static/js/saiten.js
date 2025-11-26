// scoring/static/js/saiten.js
// (内容は共有いただいたコードそのままでOKです)
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');

imageInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        imagePreview.src = '';
        imagePreview.style.display = 'none';
    }
});

const openCameraBtn = document.getElementById('openCameraBtn');
const cameraArea = document.getElementById('cameraArea');
const cameraVideo = document.getElementById('cameraVideo');
const takePhotoBtn = document.getElementById('takePhotoBtn');

let cameraStream = null;

openCameraBtn.addEventListener('click', async () => {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraVideo.srcObject = cameraStream;
        cameraArea.style.display = "block";
        cameraArea.classList.remove("hidden"); // Tailwind対応
        imagePreview.style.display = "none";
    } catch (err) {
        alert("カメラを起動できませんでした: " + err);
    }
});

takePhotoBtn.addEventListener('click', () => {
    if (!cameraStream) return;
    const canvas = document.createElement('canvas');
    canvas.width = cameraVideo.videoWidth;
    canvas.height = cameraVideo.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg");
    imagePreview.src = dataUrl;
    imagePreview.style.display = "block";
    imagePreview.classList.remove("hidden"); // Tailwind対応

    fetch(dataUrl)
        .then(res => res.arrayBuffer())
        .then(buffer => {
            const file = new File([buffer], "camera.jpg", { type: "image/jpeg" });
            const dt = new DataTransfer();
            dt.items.add(file);
            imageInput.files = dt.files;
        });

    cameraStream.getTracks().forEach(track => track.stop());
    cameraArea.style.display = "none";
});
