(function() {
    function initIbatixTheme() {
        // Vérifier si la page est bien la nôtre et éviter la double exécution
        const app = document.querySelector('.ibatix-app');
        if (!app || app.dataset.initialized) return;
        app.dataset.initialized = 'true';

        // ─── HAMBURGER MENU ───
        const burger = document.querySelector('.nav-burger');
        const mobileMenu = document.querySelector('.mobile-menu');
        const mobileLinks = document.querySelectorAll('.mobile-menu a');

        function toggleMenu(open) {
            if(!burger || !mobileMenu) return;
            burger.classList.toggle('open', open);
            mobileMenu.classList.toggle('open', open);
            burger.setAttribute('aria-expanded', open);
            document.body.style.overflow = open ? 'hidden' : '';
        }

        if(burger) {
            burger.addEventListener('click', () => {
                toggleMenu(!burger.classList.contains('open'));
            });
        }

        mobileLinks.forEach(link => {
            link.addEventListener('click', () => toggleMenu(false));
        });

        // ─── SCROLL REVEAL (Correction de l'invisibilité) ───
        const reveals = document.querySelectorAll('.reveal');
        if (reveals.length > 0) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((e, i) => {
                    if (e.isIntersecting) {
                        e.target.style.transitionDelay = (i * 0.08) + 's';
                        e.target.classList.add('visible');
                        observer.unobserve(e.target);
                    }
                });
            }, { threshold: 0.12 });
            reveals.forEach(el => observer.observe(el));
        }

        // ─── COUNTERS ───
        const counters = document.querySelectorAll('.counter');
        if (counters.length > 0) {
            const counterObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) return;
                    const el = entry.target;
                    const target = parseInt(el.dataset.target);
                    const duration = 1400;
                    const step = target / (duration / 16);
                    let current = 0;
                    const tick = () => {
                        current = Math.min(current + step, target);
                        el.textContent = Math.floor(current).toLocaleString('fr-FR');
                        if (current < target) requestAnimationFrame(tick);
                    };
                    tick();
                    counterObserver.unobserve(el);
                });
            }, { threshold: 0.5 });
            counters.forEach(el => counterObserver.observe(el));
        }

        // ─── MODULE SWITCHER (Correction du click) ───
        const moduleData = {
            crm: {
                title: 'CRM & Prospection',
                desc: "Gérez l'intégralité de votre cycle de vente, de la première prise de contact à la signature du devis. Suivez vos leads, automatisez vos relances et analysez vos performances commerciales.",
                chips: ['Pipeline de vente', 'Suivi des leads', 'Relances automatiques', 'Historique client', 'Rapports commerciaux', 'Import/export contacts']
            },
            devis: {
                title: 'Devis & Facturation',
                desc: "Générez des devis conformes en quelques minutes. Signature électronique sur tablette, envoi par SMS ou email, et transformation automatique en facture.",
                chips: ['Devis personnalisés', 'Signature tablette', 'Envoi SMS/Email', 'Transformation en facture', 'Bibliothèque articles', 'Relances paiement']
            },
            chantier: {
                title: 'Gestion de chantier',
                desc: "Planifiez et suivez tous vos chantiers depuis un tableau de bord unifié. Géolocalisation, horodatage, gestion des réserves et réception de travaux dématérialisée.",
                chips: ['Planning visuel', 'Géolocalisation GPS', 'Gestion des réserves', 'PV de réception', 'Sous-traitance', 'Rapport de visite']
            },
            primes: {
                title: 'Primes énergétiques',
                desc: "Calcul automatique de toutes les aides disponibles : CEE, MaPrimeRénov', primes régionales et locales. Les montants sont intégrés directement dans vos devis.",
                chips: ['Calcul CEE', "MaPrimeRénov'", 'Primes régionales', 'Simulation instantanée', 'Dépôt de dossiers', 'Suivi des remboursements']
            },
            compta: {
                title: 'Comptabilité & Achats',
                desc: "Plan comptable français intégré. Gérez vos achats, stocks, fournisseurs et suivez votre trésorerie en temps réel, sans double saisie.",
                chips: ['Plan comptable FR', 'Gestion des stocks', 'Commandes fournisseurs', 'Trésorerie live', 'Exports comptables', 'Rapprochement bancaire']
            },
            conformite: {
                title: 'Conformité & Documents',
                desc: "Génération automatique de tous les documents réglementaires : Cerfa, attestations, rapports. L'IA vérifie la conformité de chaque dossier avant envoi.",
                chips: ['Génération Cerfa', 'Contrôle IA', 'Archivage sécurisé', 'Traçabilité', 'Mises à jour auto', 'Coffre-fort numérique']
            }
        };

        const moduleItems = document.querySelectorAll('.module-item');
        const display = document.getElementById('moduleDisplay');

        if (moduleItems.length > 0 && display) {
            moduleItems.forEach(item => {
                item.addEventListener('click', () => {
                    document.querySelectorAll('.module-item').forEach(i => i.classList.remove('active'));
                    item.classList.add('active');
                    const data = moduleData[item.dataset.module];
                    if(!data) return;

                    display.style.opacity = '0';
                    display.style.transform = 'translateY(8px)';

                    setTimeout(() => {
                        const h3 = display.querySelector('h3');
                        const p = display.querySelector('p');
                        const chips = display.querySelector('.module-chips');

                        if(h3) h3.textContent = data.title;
                        if(p) p.textContent = data.desc;
                        if(chips) chips.innerHTML = data.chips.map(c => `<span class="chip">${c}</span>`).join('');

                        display.style.transition = 'opacity 0.3s, transform 0.3s';
                        display.style.opacity = '1';
                        display.style.transform = 'translateY(0)';
                    }, 180);
                });
            });
        }

        // ─── MODAL DEMO (POPUP) ───
        const modal = document.getElementById('demoModal');
        const openBtns = document.querySelectorAll('.open-demo');
        const closeBtn = document.querySelector('.demo-modal-close');
        const overlay = document.querySelector('.demo-modal-overlay');

        function openModal(e) {
            e.preventDefault();
            if(modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden'; // Empêche le scroll en arrière-plan
            }
        }

        function closeModal() {
            if(modal) {
                modal.classList.remove('active');
                document.body.style.overflow = ''; // Réactive le scroll
            }
        }

        // Ajouter l'événement à tous les boutons "Demander une démo"
        openBtns.forEach(btn => {
            btn.addEventListener('click', openModal);
        });

        // Fermer au clic sur la croix ou à côté de la modale
        if(closeBtn) closeBtn.addEventListener('click', closeModal);
        if(overlay) overlay.addEventListener('click', closeModal);

        // Fermer avec la touche Echap
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
                closeModal();
            }
        });

        // ─── NAV SCROLL ───
        window.addEventListener('scroll', () => {
            const nav = document.querySelector('.ibatix-app nav');
            if (nav) {
                nav.style.background = window.scrollY > 60
                  ? 'rgba(13,26,19,0.95)'
                  : 'rgba(13,26,19,0.7)';
            }
        });
    }

    // Exécution robuste pour Odoo
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initIbatixTheme);
    } else {
        // Le DOM est déjà chargé (cas fréquent avec le chargement de module d'Odoo)
        initIbatixTheme();
    }
})();