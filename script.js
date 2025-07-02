document.addEventListener('DOMContentLoaded', () => {
    // --- Scroll Fade-in Animation ---
    const sections = document.querySelectorAll('.content-section');

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    sections.forEach(section => {
        observer.observe(section);
    });

    // --- Hero Image Swapping Animation ---
    const heroGrid = document.querySelector('.hero-image-grid');
    if (heroGrid) {
        const memberImages = {
            'マミヨ': ['マミヨ/アセット 8@4x.png', 'マミヨ/アセット 9@4x.png', 'マミヨ/アセット 10@4x.png'],
            'RamBaar': ['RamBaar/アセット 14@4x.png', 'RamBaar/アセット 15@4x.png', 'RamBaar/アセット 16@4x.png'],
            'つくも': ['つくも/アセット 11@4x.png', 'つくも/アセット 12@4x.png', 'つくも/アセット 13@4x.png'],
            'やすよ': ['やすよ/アセット 5@4x.png', 'やすよ/アセット 6@4x.png', 'やすよ/アセット 7@4x.png'],
            '村上': ['村上/アセット 2@4x.png', '村上/アセット 3@4x.png', '村上/アセット 4@4x.png']
        };
        const chairImageSource = "素材/写真素材/ヒーロー/椅子_ロゴ無し.png";
        const memberNames = Object.keys(memberImages);
        let isPersonSlotOdd = true; // true: 奇数スロットが人物, false: 偶数スロットが人物

        function shuffle(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        }

        function getRandomImage(memberName) {
            const images = memberImages[memberName];
            const randomIndex = Math.floor(Math.random() * images.length);
            // Note: The path now includes the member's name as a folder
            return `素材/写真素材/ヒーロー/${images[randomIndex]}`;
        }

        function swapImages() {
            const slots = Array.from(heroGrid.querySelectorAll('.hero-image-slot'));
            const shuffledMembers = shuffle([...memberNames]);

            // Determine which slots get people and which get chairs
            const personSlots = slots.filter((_, i) => (isPersonSlotOdd ? (i + 1) % 2 !== 0 : (i + 1) % 2 === 0));
            const chairSlots = slots.filter((_, i) => (isPersonSlotOdd ? (i + 1) % 2 === 0 : (i + 1) % 2 !== 0));

            // Fade out
            slots.forEach(slot => slot.style.opacity = 0);

            setTimeout(() => {
                // Assign images to person slots
                personSlots.forEach((slot, i) => {
                    const memberName = shuffledMembers[i];
                    const img = slot.querySelector('img');
                    img.src = getRandomImage(memberName);
                    img.alt = memberName;
                });

                // Assign images to chair slots
                chairSlots.forEach(slot => {
                    const img = slot.querySelector('img');
                    img.src = chairImageSource;
                    img.alt = '椅子';
                });

                // Fade in
                slots.forEach(slot => slot.style.opacity = 1);

                // Flip the state for the next run
                isPersonSlotOdd = !isPersonSlotOdd;
            }, 500); // Match CSS transition duration
        }

        setInterval(swapImages, 3000); // Swap every 3 seconds
    }

    // --- Lightbox Gallery ---
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        const lightboxImg = document.getElementById('lightbox-img');
        const galleryItems = document.querySelectorAll('.gallery-item');
        const galleryImages = Array.from(galleryItems).map(item => item.querySelector('img').src);
        let currentIndex = 0;

        const showImage = (index) => {
            lightboxImg.src = galleryImages[index];
            currentIndex = index;
            lightbox.style.display = 'block';
        };

        galleryItems.forEach((item, index) => {
            item.addEventListener('click', () => showImage(index));
        });

        document.querySelector('.lightbox-close').addEventListener('click', () => {
            lightbox.style.display = 'none';
        });

        document.querySelector('.lightbox-prev').addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + galleryImages.length) % galleryImages.length;
            showImage(currentIndex);
        });

        document.querySelector('.lightbox-next').addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % galleryImages.length;
            showImage(currentIndex);
        });

        // Close lightbox on background click
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                lightbox.style.display = 'none';
            }
        });
    }

    // --- Member Modal ---
    const memberCards = document.querySelectorAll('.member-card');
    const memberModal = document.getElementById('member-modal');

    if (memberCards.length > 0 && memberModal) {
        const modalImg = document.getElementById('member-modal-img');
        const modalName = document.getElementById('member-modal-name');
        const modalProfile = document.getElementById('member-modal-profile');
        const closeModal = document.querySelector('.member-modal-close');

        const memberProfiles = {
            mamiyo: {
                name: 'マミヨ',
                profile: 'ダミーテキストダミーテキストダミーテキストダミーテキストダミーテキスト'
            },
            rambaar: {
                name: 'RamBaar',
                profile: 'ダミーテキストダミーテキストダミーテキストダミーテキストダミーテキスト'
            },
            tsukumo: {
                name: '惺光 玖拾玖',
                profile: 'ダミーテキストダミーテキストダミーテキストダミーテキストダミーテキスト'
            },
            yasuyo: {
                name: '恭世',
                profile: 'ダミーテキストダミーテキストダミーテキストダミーテキストダミーテキスト'
            },
            murakami: {
                name: '村上 良之',
                profile: 'ダミーテキストダミーテキストダミーテキストダミーテキストダミーテキスト'
            }
        };

        memberCards.forEach(card => {
            card.addEventListener('click', () => {
                const memberId = card.dataset.member;
                const memberData = memberProfiles[memberId];
                const memberImgSrc = card.querySelector('.member-photo').src;

                if (memberData) {
                    modalImg.src = memberImgSrc;
                    modalName.textContent = memberData.name;
                    modalProfile.textContent = memberData.profile;
                    memberModal.style.display = 'flex';
                }
            });
        });

        const closeMemberModal = () => {
            memberModal.style.display = 'none';
        }

        closeModal.addEventListener('click', closeMemberModal);

        memberModal.addEventListener('click', (e) => {
            if (e.target === memberModal) {
                closeMemberModal();
            }
        });
    }
});