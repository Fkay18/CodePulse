(() => {
    const pictureInput = document.querySelector('#id_profile_picture');
    const avatarImages = document.querySelectorAll('[data-profile-avatar-image], [data-profile-avatar-small-image]');
    const avatarFallbacks = document.querySelectorAll('[data-profile-avatar-fallback], [data-profile-avatar-small-fallback]');
    const nameInput = document.querySelector('#id_display_name');
    const namePreview = document.querySelector('[data-profile-name]');
    const bioInput = document.querySelector('#id_bio');
    const bioPreview = document.querySelector('[data-profile-bio]');
    const clearPicture = document.querySelector('#id_profile_picture-clear');
    let previewUrl;

    const showInitials = () => {
        avatarImages.forEach((image) => { image.hidden = true; });
        avatarFallbacks.forEach((fallback) => { fallback.hidden = false; });
    };

    if (pictureInput) {
        pictureInput.addEventListener('change', () => {
            const picture = pictureInput.files[0];
            if (!picture) {
                if (clearPicture && clearPicture.checked) showInitials();
                return;
            }
            if (!picture.type.startsWith('image/')) return;

            if (previewUrl) URL.revokeObjectURL(previewUrl);
            previewUrl = URL.createObjectURL(picture);
            avatarImages.forEach((image) => {
                image.src = previewUrl;
                image.hidden = false;
            });
            avatarFallbacks.forEach((fallback) => { fallback.hidden = true; });
        });
    }

    if (clearPicture) clearPicture.addEventListener('change', showInitials);

    if (nameInput && namePreview) {
        nameInput.addEventListener('input', () => {
            namePreview.textContent = nameInput.value.trim() || namePreview.dataset.fallbackName;
            const initial = (nameInput.value.trim() || namePreview.dataset.fallbackName).slice(0, 1).toUpperCase();
            avatarFallbacks.forEach((fallback) => { fallback.textContent = initial; });
        });
    }

    if (bioInput && bioPreview) {
        bioInput.addEventListener('input', () => {
            bioPreview.textContent = bioInput.value.trim() || 'Your biography will appear here.';
        });
    }
})();