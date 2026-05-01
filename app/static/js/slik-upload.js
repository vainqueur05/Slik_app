const SLIK_UPLOAD = (function() {
  const CLOUD_NAME = 'dnns2lagp';
  const UPLOAD_PRESET = 'slik_unsigned';

  let state = { file: null, type: null, uploading: false, uploaded: false, cloudinaryUrl: '', cloudinaryId: '' };

  function init(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const tenantSlug = options.tenantSlug || '';
    const btnSaveId = options.btnSaveId;
    const autoSave = options.autoSave || false;
    const saveUrl = options.saveUrl || '';
    const saveField = options.saveField || 'photo_url';

    container.innerHTML = `
      <div class="slik-upload-widget" style="border:2px dashed #555; border-radius:12px; padding:20px; text-align:center; background:#111;">
        <div class="drop-zone" id="${containerId}-drop" style="cursor:pointer;">
          <i class="bi bi-cloud-upload" style="font-size:2rem; color:#aaa;"></i>
          <p style="color:#aaa; margin:8px 0;">Glisse ta photo/vidéo ici</p>
          <button type="button" class="bg-[#D4AF37] text-black px-4 py-2 rounded-full font-bold hover:bg-yellow-500 transition" id="${containerId}-btn-choose">
            <i class="bi bi-folder2-open"></i> Choisir un fichier
          </button>
          <input type="file" id="${containerId}-file" accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime" hidden>
        </div>
        <div class="preview-container" id="${containerId}-preview" style="display:none; margin-top:15px;"></div>
        <div class="progress-container" id="${containerId}-progress" style="display:none; margin-top:10px;">
          <div style="background:#333; border-radius:20px; height:6px; width:100%;">
            <div id="${containerId}-progress-fill" style="background:#3b82f6; height:100%; width:0%; border-radius:20px; transition: width 0.2s;"></div>
          </div>
          <p id="${containerId}-progress-text" style="color:#3b82f6; font-size:0.8rem; margin-top:4px;">0%</p>
        </div>
        <div class="status-message" id="${containerId}-status" style="margin-top:8px; font-size:0.9rem;"></div>
        <div class="error-message" id="${containerId}-error" style="margin-top:8px; font-size:0.9rem; color:#ef4444;"></div>
      </div>
      <input type="hidden" id="${containerId}-cloudinary-id" name="photo_cloudinary_id">
      <input type="hidden" id="${containerId}-cloudinary-url" name="${saveField}">
    `;

    const dropZone = document.getElementById(`${containerId}-drop`);
    const fileInput = document.getElementById(`${containerId}-file`);
    const previewContainer = document.getElementById(`${containerId}-preview`);
    const progressFill = document.getElementById(`${containerId}-progress-fill`);
    const progressText = document.getElementById(`${containerId}-progress-text`);
    const statusEl = document.getElementById(`${containerId}-status`);
    const errorEl = document.getElementById(`${containerId}-error`);
    const hiddenId = document.getElementById(`${containerId}-cloudinary-id`);
    const hiddenUrl = document.getElementById(`${containerId}-cloudinary-url`);
    const progressContainer = document.getElementById(`${containerId}-progress`);
    const btnSave = btnSaveId ? document.getElementById(btnSaveId) : null;
    const btnChoose = document.getElementById(`${containerId}-btn-choose`);

    // Activer le bouton Enregistrer par défaut
    if (btnSave) btnSave.disabled = false;

    // Bouton "Choisir un fichier"
    btnChoose.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = '#D4AF37'; });
    dropZone.addEventListener('dragleave', () => dropZone.style.borderColor = '#555');
    dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.style.borderColor = '#555'; handleFile(e.dataTransfer.files[0]); });
    fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

    function updateProgress(percent) {
      progressFill.style.width = percent + '%';
      progressText.textContent = percent + '%';
    }

    async function handleFile(file) {
      if (!file) return;
      state.file = file;
      state.type = file.type.startsWith('video') ? 'video' : 'image';
      state.uploaded = false;
      errorEl.textContent = '';
      statusEl.textContent = '';
      const allowed = ['image/jpeg','image/png','image/webp','video/mp4','video/quicktime'];
      if (!allowed.includes(file.type)) { errorEl.textContent = 'Format non supporté'; return; }

      previewContainer.style.display = 'block';
      previewContainer.innerHTML = '';
      if (state.type === 'image') {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.style.maxWidth = '100%'; img.style.maxHeight = '200px'; img.style.borderRadius = '8px';
        previewContainer.appendChild(img);
      } else {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.controls = true;
        video.style.maxWidth = '100%'; video.style.maxHeight = '200px';
        video.onloadedmetadata = () => {
          if (video.duration > 60) { errorEl.textContent = 'Vidéo trop longue (max 60s)'; state.file = null; previewContainer.style.display = 'none'; return; }
        };
        previewContainer.appendChild(video);
      }

      if (btnSave) btnSave.disabled = true; // désactiver pendant l'upload
      await uploadFile(file, updateProgress);
    }

    async function uploadFile(originalFile, onProgress) {
      try {
        let fileToUpload = originalFile;
        if (state.type === 'image' && originalFile.size > 2 * 1024 * 1024) {
          fileToUpload = await compressImage(originalFile, 0.8);
        }

        state.uploading = true;
        progressContainer.style.display = 'block';

        const formData = new FormData();
        formData.append('file', fileToUpload);
        formData.append('upload_preset', UPLOAD_PRESET);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/auto/upload`);
        xhr.upload.onprogress = e => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)); };

        await new Promise((resolve, reject) => {
          xhr.onload = () => {
            if (xhr.status === 200) {
              const resp = JSON.parse(xhr.responseText);
              state.cloudinaryId = resp.public_id;
              state.cloudinaryUrl = resp.secure_url || resp.url;
              state.uploaded = true;
              hiddenId.value = state.cloudinaryId;
              hiddenUrl.value = state.cloudinaryUrl;
              statusEl.innerHTML = 'Upload réussi';
              onProgress(100);
              if (btnSave) btnSave.disabled = false; // réactiver après succès
              if (autoSave && saveUrl) {
                fetch(saveUrl, {
                  method: 'POST',
                  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                  body: 'cloudinary_id=' + encodeURIComponent(state.cloudinaryId) + '&' + saveField + '=' + encodeURIComponent(state.cloudinaryUrl)
                }).then(() => { if (window.showToast) window.showToast('Sauvegardé'); });
              }
              resolve();
            } else {
              reject(new Error('Erreur Cloudinary'));
              if (btnSave) btnSave.disabled = true; // laisser désactivé en cas d'échec
            }
          };
          xhr.onerror = () => {
            reject(new Error('Erreur réseau'));
            if (btnSave) btnSave.disabled = true;
          };
          xhr.send(formData);
        });
      } catch (err) {
        errorEl.textContent = 'Échec upload. Réessaie.';
        state.uploaded = false;
        if (btnSave) btnSave.disabled = true;
      } finally {
        state.uploading = false;
      }
    }

    function compressImage(file, quality) {
      return new Promise(resolve => {
        const reader = new FileReader();
        reader.onload = e => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width; canvas.height = img.height;
            canvas.getContext('2d').drawImage(img, 0, 0);
            canvas.toBlob(blob => resolve(new File([blob], file.name, { type: 'image/jpeg' })), 'image/jpeg', quality);
          };
          img.src = e.target.result;
        };
        reader.readAsDataURL(file);
      });
    }
  }

  return { init };
})();