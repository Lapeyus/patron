        let catalog = [];
        let filters = {};
        let activeFilters = {};
        let filterOptionCounts = {};
        let dataLoaded = false;
        let scrollLockActive = false;
        let scrollLockY = 0;
        const ENRICHED_DATA_PATH = "catalog.json";
        const MEDIA_BASE_PATH = "";
        const AUTH_SHA256_B64 = "bnU6awo3zRAyyZG6FnzuWW25rcozFi6p5IoLqGxNrtM=";
        const AUTH_ELITE_SHA256_B64 = "GoCwaRtpb+GNvJ6UcivHuyMl12B4van90MF2C9TNmGQ="; 
        const AUTH_STORAGE_KEY = "patron_auth_sha256_b64_v1";
        const LANG_STORAGE_KEY = "patron_lang_v1";
        const ASK_CONTACT_WHATSAPP_E164 = "50684098222";
        const DISCREET_CONTACT_EMAIL = "patron@patroncr.net";
        let currentLang = "es";
        let authLevel = null;  
        const UBICACION_OPTIONS = ["ALAJUELA", "CARTAGO", "GUAPILES", "HEREDIA", "SAN JOSE"];
        const CATEGORY_FILTER_VALUES = {
            nuevo_ingreso: "Nuevos ingresos",
            sin_experiencia: "Sin experiencia",
            cortesia: "Cortesía",
            nuevas_fotos_videos: "Nuevas fotos/videos",
            lista_discreta: "Lista discreta",
        };

        const I18N = {
            es: {
                page: { title: "Catálogo Patrón" },
                app: { title: "Comunidad Patrón" },
                brand: { subtitle: "Catálogo" },
                lang: { aria: "Idioma" },
                controls: {
                    searchPlaceholder: "Buscar...",
                    statsFound: "{count} Perfiles encontrados",
                    loading: "Cargando…",
                    loadError: "No se pudo cargar el catálogo.",
                    retry: "Reintentar",
                },
                nav: {
                    left: "Mover a la izquierda",
                    right: "Mover a la derecha",
                },
                common: {
                    unknown: "Desconocido",
                    yes: "Sí",
                    no: "No",
                },
                ui: {
                    filters: "Filtros",
                    openFiltersAria: "Abrir filtros",
                    closeFiltersAria: "Cerrar filtros",
                },
                filters: {
                    location: "Ubicación",
                    age: "Edad",
                    newArrivals: "Nuevos ingresos",
                    noExperience: "Sin experiencia",
                    courtesy: "Perfiles de cortesía",
                    newMedia: "Perfiles con nuevas fotos - videos",
                    categories: "Categorías",
                    categoryNewArrivalsOnly: "Nuevos ingresos",
                    categoryNoExperienceOnly: "Sin experiencia",
                    categoryCourtesyOnly: "Cortesía",
                    categoryNewMediaOnly: "Nuevas fotos/videos",
                    categoryDiscreetListOnly: "Lista discreta",
                },
                media: {
                    photos: "Fotos",
                    videos: "Videos",
                    reviews: "Reseñas",
                    discreetProfile: "perfil de lista discreta",
                },
                profile: {
                    ageCard: "{age} años",
                    ageSubtitle: "{age} años",
                },
                sections: {
                    extraction: "Perfil",
                    attributes: "Atributos",
                    rates: "Tarifas",
                    services: "Servicios",
                    contact: "Contacto",
                    reviews: "Reseñas",
                },
                reviews: {
                    aria: "Carrusel de reseñas",
                    prev: "Anterior",
                    next: "Siguiente",
                },
                table: {
                    service: "Servicio",
                    amount: "Monto",
                },
                contact: {
                    whatsapp: "WhatsApp",
                    phone: "Tel",
                    email: "Email",
                    social: "Redes",
                    notes: "Notas",
                    whatsappCta: "Abrir WhatsApp",
                    askForContactCta: "Solicitar contacto",
                    discreetEmailCta: "Contacto discreto por email",
                    whatsappMessage: "Hola, vi tu perfil en {app}. ¿Podemos coordinar?",
                    whatsappMessageWithName: "Hola {name}, vi tu perfil en {app}. ¿Podemos coordinar?",
                    askForContactMessage: "Hola Patron, quiero contactar a {profile}.\n- Me llamo # \n-el celular desde donde le escribire es: \n-Fecha aproximada de la cita es: ",
                    discreetEmailSubject: "Solicitud de contacto discreto - {profile}",
                    discreetEmailMessage: "Hola Patron, quiero solicitar contacto discreto de {profile}.\n- Me llamo:\n- Celular:\n- Fecha aproximada de la cita:",
                    call: "Llamar {phone}",
                },
                extraction_labels: {
                    name: "Nombre",
                    age: "Edad",
                    height: "Altura",
                    weight: "Peso",
                    measurements: "Medidas",
                    hair_color: "Color de cabello",
                    eye_color: "Color de ojos",
                    location: "Ubicación",
                    availability: "Disponibilidad",
                    contact: "Contacto",
                    prices: "Tarifas",
                    implants: "Implantes",
                    uber: "Uber",
                    cosmetic_surgeries: "Cirugías cosméticas",
                    other_attributes: "Otros atributos",
                },
                price_slots: {
                    one_hour: "1 hora",
                    two_hours: "2 horas",
                    three_hours: "3 horas",
                    overnight: "Toda la noche",
                },
                durations: {
                    one_hour: { label: "1 hora", short: "1h" },
                    two_hours: { label: "2 horas", short: "2h" },
                    three_hours: { label: "3 horas", short: "3h" },
                    overnight: { label: "Toda la noche", short: "Noche" },
                },
                auth: {
                    ariaLabel: "Autenticación requerida",
                    title: "Acceso",
                    subtitle: "Ingrese la contraseña para ver el catálogo.",
                    passwordPlaceholder: "Contraseña",
                    remember: "Recordar en este dispositivo",
                    unlock: "Entrar",
                    required: "Ingrese la contraseña.",
                    wrong: "Contraseña incorrecta.",
                    error: "Error de autenticación.",
                    webcryptoUnavailable: "WebCrypto no disponible. Abra con https o http://localhost.",
                },
                disclaimer: {
                    ariaLabel: "Aviso legal",
                    title: "AVISO LEGAL",
                    closeAria: "Cerrar",
                    p1: "La comunidad y red social denominada \"Club Patrón\" confirma que todas las personas participantes en la red son mayores de 18 años, actúan de manera voluntaria y están en pleno uso de sus facultades. El operador de este correo electrónico no participa, no media y no obtiene beneficios de los acuerdos realizados por las participantes. Nos oponemos firmemente a la trata de personas, la pornografía infantil y la pedofilia.",
                    p2: "Se advierte a los miembros y destinatarios de este correo que toda comunicación transmitida mediante este medio está protegida bajo el secreto de las comunicaciones según el artículo 24 de la Constitución. La divulgación, exposición, reenvío o compartición de esta comunicación a terceros sin el debido consentimiento constituye un delito de violación de correspondencia o comunicaciones, tipificado en el artículo 196 del Código Penal.",
                    p3: "Asimismo, todas las imágenes, actualizaciones o documentos adjuntos a los correos enviados por \"Club Patrón\" están protegidos bajo derechos reservados de imagen. Cualquier divulgación o uso indebido de estos materiales sin autorización previa puede resultar en un delito de violación de datos personales, conforme al artículo 196 bis del Código Penal.",
                    accept: "Entendido",
                },
            },
            en: {
                page: { title: "Patron Catalog" },
                app: { title: "Patrón Community" },
                brand: { subtitle: "Catalog" },
                lang: { aria: "Language" },
                controls: {
                    searchPlaceholder: "Search...",
                    statsFound: "{count} found",
                    loading: "Loading…",
                    loadError: "Failed to load the catalog.",
                    retry: "Retry",
                },
                nav: {
                    left: "Move left",
                    right: "Move right",
                },
                common: {
                    unknown: "Unknown",
                    yes: "Yes",
                    no: "No",
                },
                ui: {
                    filters: "Filters",
                    openFiltersAria: "Open filters",
                    closeFiltersAria: "Close filters",
                },
                filters: {
                    location: "Location",
                    age: "Age",
                    newArrivals: "New arrivals",
                    noExperience: "No experience",
                    courtesy: "Courtesy profiles",
                    newMedia: "New photos/videos",
                    categories: "Categories",
                    categoryNewArrivalsOnly: "New arrivals only",
                    categoryNoExperienceOnly: "No experience only",
                    categoryCourtesyOnly: "Courtesy only",
                    categoryNewMediaOnly: "New photos/videos only",
                    categoryDiscreetListOnly: "Discreet list",
                },
                media: {
                    photos: "Photos",
                    videos: "Videos",
                    reviews: "Reviews",
                    discreetProfile: "discreet list profile",
                },
                profile: {
                    ageCard: "{age} years old",
                    ageSubtitle: "{age} years old",
                },
                sections: {
                    extraction: "Extraction",
                    attributes: "Attributes",
                    rates: "Rates",
                    services: "Services",
                    contact: "Contact",
                    reviews: "Reviews",
                },
                reviews: {
                    aria: "Reviews carousel",
                    prev: "Previous",
                    next: "Next",
                },
                table: {
                    service: "Service",
                    amount: "Amount",
                },
                contact: {
                    whatsapp: "WhatsApp",
                    phone: "Phone",
                    email: "Email",
                    social: "Social",
                    notes: "Notes",
                    whatsappCta: "Contactela directamente por WhatsApp",
                    askForContactCta: "Ask for contact",
                    discreetEmailCta: "Discreet email contact",
                    whatsappMessage: "Hi, I saw your profile on {app}. Can we coordinate?",
                    whatsappMessageWithName: "Hi {name}, I saw your profile on {app}. Can we coordinate?",
                    askForContactMessage: "I want to contact {profile}\n- my name is\n- the phone number I will write from is\n- approximate date of the appointment is",
                    discreetEmailSubject: "Discreet contact request - {profile}",
                    discreetEmailMessage: "Hi Patron, I want to request discreet contact for {profile}.\n- My name is:\n- Phone number:\n- Approximate appointment date:",
                    call: "Call {phone}",
                },
                extraction_labels: {
                    name: "Name",
                    age: "Age",
                    height: "Height",
                    weight: "Weight",
                    measurements: "Measurements",
                    hair_color: "Hair color",
                    eye_color: "Eye color",
                    location: "Location",
                    availability: "Availability",
                    contact: "Contact",
                    prices: "Rates",
                    implants: "Implants",
                    uber: "Uber",
                    cosmetic_surgeries: "Cosmetic surgeries",
                    other_attributes: "Other attributes",
                },
                price_slots: {
                    one_hour: "1 hour",
                    two_hours: "2 hours",
                    three_hours: "3 hours",
                    overnight: "Overnight",
                },
                durations: {
                    one_hour: { label: "1 hour", short: "1h" },
                    two_hours: { label: "2 hours", short: "2h" },
                    three_hours: { label: "3 hours", short: "3h" },
                    overnight: { label: "Overnight", short: "Night" },
                },
                auth: {
                    ariaLabel: "Authentication required",
                    title: "Access",
                    subtitle: "Enter the password to view the catalog.",
                    passwordPlaceholder: "Password",
                    remember: "Remember on this device",
                    unlock: "Unlock",
                    required: "Enter the password.",
                    wrong: "Wrong password.",
                    error: "Authentication error.",
                    webcryptoUnavailable: "WebCrypto unavailable. Open over https or http://localhost.",
                },
                disclaimer: {
                    ariaLabel: "Legal notice",
                    title: "LEGAL NOTICE",
                    closeAria: "Close",
                    p1: "The community and social network known as \"Club Patrón\" confirms that all participants in the network are over 18 years of age, act voluntarily, and are in full possession of their faculties. The operator of this email does not participate, mediate, or obtain benefits from the agreements reached by the participants. We firmly oppose human trafficking, child pornography, and pedophilia.",
                    p2: "Members and recipients of this email are advised that all communication transmitted through this medium is protected under the secrecy of communications pursuant to Article 24 of the Constitution. The disclosure, exposure, forwarding, or sharing of this communication with third parties without due consent constitutes the crime of violation of correspondence or communications, as defined in Article 196 of the Penal Code.",
                    p3: "Likewise, all images, updates, or documents attached to emails sent by \"Club Patrón\" are protected under reserved image rights. Any disclosure or improper use of these materials without prior authorization may constitute the crime of violation of personal data, pursuant to Article 196 bis of the Penal Code.",
                    accept: "I understand",
                },
            },
        };

        function normalizeLang(lang) {
            const l = (lang || "").toString().toLowerCase();
            if (l.startsWith("en")) return "en";
            return "es";
        }

        function getTranslation(lang, key) {
            const parts = key.split(".");
            let cur = I18N[lang];
            for (const p of parts) {
                if (!cur || typeof cur !== "object") return null;
                cur = cur[p];
            }
            return cur;
        }

        function t(key, vars = {}) {
            const lang = currentLang in I18N ? currentLang : "es";
            let value = getTranslation(lang, key);
            if (value == null && lang !== "es") value = getTranslation("es", key);
            if (value == null) return key;
            if (typeof value !== "string") return value;
            return value.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? "").toString());
        }

        function labelForExtractionKey(key) {
            const map = (I18N[currentLang]?.extraction_labels) || I18N.es.extraction_labels;
            return map?.[key] || key;
        }

        function labelForPriceSlot(key) {
            const map = (I18N[currentLang]?.price_slots) || I18N.es.price_slots;
            return map?.[key] || key;
        }

        function durationLabel(key) {
            const durations = (I18N[currentLang]?.durations) || I18N.es.durations;
            return durations?.[key]?.label || key;
        }

        function durationShort(key) {
            const durations = (I18N[currentLang]?.durations) || I18N.es.durations;
            return durations?.[key]?.short || key;
        }

        function applyTranslations() {
            document.documentElement.lang = currentLang;
            document.title = t("page.title");

            const langAria = t("lang.aria");
            ["langSelect", "auth-lang-select", "disclaimer-lang-select"].forEach(id => {
                const sel = document.getElementById(id);
                if (!sel) return;
                sel.value = currentLang;
                sel.setAttribute("aria-label", langAria);
            });

            const langLabel = document.getElementById("filters-lang-label");
            if (langLabel) langLabel.textContent = currentLang === "en" ? "Language" : "Idioma";

            const appTitle = document.getElementById("app-title");
            if (appTitle) appTitle.textContent = t("app.title");

            const mainAppTitle = document.getElementById("main-app-title");
            if (mainAppTitle) mainAppTitle.textContent = t("app.title");
            const mainAppSubtitle = document.getElementById("main-app-subtitle");
            if (mainAppSubtitle) mainAppSubtitle.textContent = t("brand.subtitle");

            const filtersToggle = document.getElementById("filters-toggle");
            if (filtersToggle) {
                filtersToggle.textContent = t("ui.filters");
                filtersToggle.setAttribute("aria-label", t("ui.openFiltersAria"));
            }
            const filtersClose = document.getElementById("filters-close");
            if (filtersClose) filtersClose.setAttribute("aria-label", t("ui.closeFiltersAria"));

            const search = document.getElementById("searchInput");
            if (search) search.placeholder = t("controls.searchPlaceholder");

            const navLeft = document.getElementById("lb-nav-left");
            const navRight = document.getElementById("lb-nav-right");
            if (navLeft) navLeft.setAttribute("aria-label", t("nav.left"));
            if (navRight) navRight.setAttribute("aria-label", t("nav.right"));

            const authOverlay = document.getElementById("auth-overlay");
            if (authOverlay) authOverlay.setAttribute("aria-label", t("auth.ariaLabel"));
            const authTitle = document.getElementById("auth-title");
            if (authTitle) authTitle.textContent = t("auth.title");
            const authSubtitle = document.getElementById("auth-subtitle");
            if (authSubtitle) authSubtitle.textContent = t("auth.subtitle");
            const authPw = document.getElementById("auth-password");
            if (authPw) authPw.setAttribute("placeholder", t("auth.passwordPlaceholder"));
            const authRemember = document.getElementById("auth-remember-label");
            if (authRemember) authRemember.textContent = t("auth.remember");
            const authSubmit = document.getElementById("auth-submit");
            if (authSubmit) authSubmit.textContent = t("auth.unlock");

            const disclaimerOverlay = document.getElementById("disclaimer-overlay");
            if (disclaimerOverlay) disclaimerOverlay.setAttribute("aria-label", t("disclaimer.ariaLabel"));
            const disclaimerTitle = document.getElementById("disclaimer-title");
            if (disclaimerTitle) disclaimerTitle.textContent = t("disclaimer.title");
            const disclaimerClose = document.getElementById("disclaimer-close");
            if (disclaimerClose) disclaimerClose.setAttribute("aria-label", t("disclaimer.closeAria"));
            const p1 = document.getElementById("disclaimer-p1");
            if (p1) p1.textContent = t("disclaimer.p1");
            const p2 = document.getElementById("disclaimer-p2");
            if (p2) p2.textContent = t("disclaimer.p2");
            const p3 = document.getElementById("disclaimer-p3");
            if (p3) p3.textContent = t("disclaimer.p3");
            const accept = document.getElementById("disclaimer-accept");
            if (accept) accept.textContent = t("disclaimer.accept");
        }

        function setLanguage(lang, { persist = true } = {}) {
            currentLang = normalizeLang(lang);
            if (persist) {
                try { localStorage.setItem(LANG_STORAGE_KEY, currentLang); } catch (_) { /* ignore */ }
            }
            applyTranslations();
            if (dataLoaded) {
                buildFilters();
                render();
            }
        }

        window.setLanguage = setLanguage;

        function initLanguage() {
            let stored = null;
            try { stored = localStorage.getItem(LANG_STORAGE_KEY); } catch (_) { /* ignore */ }
            if (stored) {
                setLanguage(stored, { persist: false });
                return;
            }
            setLanguage("es", { persist: false });
        }
        const EDAD_RANGOS = ["18 - 20 años", "21 - 30 años", "31 - 40 años"];
        const EDAD_RANGOS_SET = new Set(EDAD_RANGOS);
        const FILTER_SPECS = [
            { key: "ubicacion", labelKey: "filters.location" },
            { key: "edad", labelKey: "filters.age" },
            { key: "nuevo_ingreso", labelKey: "filters.newArrivals" },
            { key: "sin_experiencia", labelKey: "filters.noExperience" },
            { key: "cortesia", labelKey: "filters.courtesy" },
            { key: "nuevas_fotos_videos", labelKey: "filters.newMedia" },
            { key: "lista_discreta", labelKey: "filters.categoryDiscreetListOnly" },
        ];
        const GROUPED_CATEGORY_FILTER_KEYS = new Set(["nuevo_ingreso", "sin_experiencia", "cortesia", "nuevas_fotos_videos", "lista_discreta"]);
        const LOCATION_MAP = {
            "alajuela": "Alajuela",
            "alajuela, palmares centro": "Alajuela, Palmares Centro",
            "barrio mexico, san jose": "Barrio México, San José",
            "cartago": "Cartago",
            "cartago y san jose": "Cartago y San José",
            "ciudad colon": "Ciudad Colón",
            "coronado": "Coronado",
            "desamparados san jose costa rica": "Desamparados, San José",
            "escazu": "Escazú",
            "guadalupe, san jose": "Guadalupe, San José",
            "guapiles": "Guápiles",
            "heredia": "Heredia",
            "heredia santa barbara": "Heredia, Santa Bárbara",
            "heredia, san pablo": "Heredia, San Pablo",
            "los yoses san pedro": "Los Yoses, San Pedro",
            "moravia": "Moravia",
            "moravia, san jose": "Moravia, San José",
            "purral": "Purral",
            "sabanilla, san jose": "Sabanilla, San José",
            "san jose": "San José",
            "sabanilla o jaco": "Sabanilla o Jacó",
            "san antonio de desamparados": "San Antonio de Desamparados",
            "san francisco de dos rios": "San Francisco de Dos Ríos",
            "san jose desamparados": "San José, Desamparados",
            "san jose y jaco": "San José y Jacó",
            "san jose, coronado": "San José, Coronado",
            "san jose, coronado-moravia": "San José, Coronado-Moravia",
            "san jose, desamparados": "San José, Desamparados",
            "san jose, san sebastian": "San José, San Sebastián",
            "san jose, santa ana": "San José, Santa Ana",
            "san miguel desamparados": "San Miguel, Desamparados",
            "san rafael de heredia": "San Rafael de Heredia",
            "san ramon": "San Ramón",
            "san sebastian": "San Sebastián",
            "santa ana": "Santa Ana",
            "tibas": "Tibás",
            "la uruca san jose": "La Uruca, San José"
        };

        const AVAILABILITY_LABELS = [
            "24/7",
            "Amplia disponibilidad",
            "Consultar disponibilidad porque trabajo",
            "Coordinar con previo aviso",
            "De 7:00 p. m. en adelante, Nocturno",
            "De 7:00 p. m. en adelante, Viernes a domingo",
            "De domingos a miércoles disponible todo el día",
            "De lunes a Domingo cualquier hora",
            "De lunes a viernes de 9 am a 9 pm máx. Fines de semana a convenir",
            "De lunes a viernes luego de las 3:00 pm y sábados y domingos disponibles",
            "Disponibilida en el día o la noche",
            "Disponibilidad inmediata",
            "Disponibilidad a convenir",
            "Disponibilidad de horario",
            "Disponibilidad negociable (horarios detallados)",
            "Disponible lunes a viernes (tarde o noche)",
            "Disponible todos los días",
            "Disponible todos los días de 9:00 am a 8:00 pm",
            "Disponible todos los días en el día y noche",
            "Disponible todos los días, prefiere mañana y tarde",
            "Domingos a miércoles",
            "Facilidad para trasladarse",
            "Horarios flexibles",
            "Horario: Mañana/Tarde antes de las 4 pm; Noche después de las 8 pm",
            "Jueves a domingo (horarios detallados)",
            "Lunes, martes y miércoles disponibles",
            "Lunes a Domingo",
            "Lunes a viernes mañana y tarde",
            "Lunes y martes horario diurno; viernes y fines de semana vespertino",
            "Lunes a viernes (horarios específicos) y fines de semana",
            "Coordinación flexible todo el día",
            "Puedo a cualquier hora",
            "Puedo todos los días (1, 2 y 3 horas)",
            "Si, solo avisar",
            "Amplia disponibilidad (general)",
            "Tiempo completo de disponibilidad",
            "Toda la semana después de la 1 pm",
            "Todos los días",
            "Todos los días con aviso previo (3 horas)",
            "Todos los días cualquier hora",
            "Todos los días de 12 pm a 12 am",
            "Todos los días y cualquier horario",
            "Todos los días a cualquier hora (coordinar)",
            "Cualquier día de la semana",
            "Cualquier día, evitar noches",
            "Cualquier hora o día con un día de anticipación",
            "De domingo a martes",
            "De lunes a domingo (total disponibilidad)",
            "De lunes a viernes",
            "Depende de mis horarios de estudio",
            "Disponibilidad completa",
            "Disponibilidad completa de jueves a domingo; otros días en la tarde",
            "Disponibilidad inmediata toda la semana",
            "Disponible todos los días",
            "Entre semana mañana y tarde",
            "Inmediata",
            "Inmediata; a convenir",
            "Lunes a Domingo tardes y noches",
            "Lunes a viernes de 2:00 pm a 9:00 pm; fines de semana negociables",
            "Lunes a viernes después de las 4:00 pm; fines de semana todo el día",
            "Martes a viernes mediodía hasta las 8 pm (coordinar con 1 día previo)",
            "Preferible de 5 pm en adelante (coordinar)",
            "Siempre a la comodidad del cliente",
            "Tarde-noche a partir de las 5 pm",
            "Tarde o noche",
            "Todos los días",
            "Todos los días de 10 am a 7 pm",
            "Todos los días de 8 a 10",
            "Todos los días de 11 am a 10 pm"
        ];

        function normalizeKey(value) {
            if (!value) return null;
            return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
        }

        function normalizeLocation(value) {
            if (!value) return null;
            const key = normalizeKey(value);
            return LOCATION_MAP[key] || value.trim();
        }

        const AVAILABILITY_MAP = AVAILABILITY_LABELS.reduce((acc, label) => {
            const key = normalizeKey(label);
            acc[key] = label;
            return acc;
        }, {});

        function normalizeAvailability(value) {
            if (!value) return null;
            const key = normalizeKey(value);
            return AVAILABILITY_MAP[key] || value.trim();
        }

        async function loadData() {
            const statsEl = document.getElementById("stats");
            const gridEl = document.getElementById("grid");
            if (statsEl) statsEl.textContent = t("controls.loading");
            if (gridEl) {
                gridEl.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div><div>${escapeHtml(t("controls.loading"))}</div></div>`;
            }

            try {
                const res = await fetch(ENRICHED_DATA_PATH, { cache: "no-store" });
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                const data = await res.json();
                catalog = transformProfiles(data.profiles || []);
                dataLoaded = true;
                buildFilters();
                render();
            } catch (e) {
                console.error(e);
                if (statsEl) statsEl.textContent = t("controls.loadError");
                if (gridEl) {
                    gridEl.innerHTML = `<div class="load-error"><div>${escapeHtml(t("controls.loadError"))}</div><button class="retry-btn" type="button" onclick="loadData()">${escapeHtml(t("controls.retry"))}</button></div>`;
                }
            }
        }

        function isProfileEnabled(profile) {
            return profile?.enabled !== false;
        }

        function cleanStringArray(value) {
            if (Array.isArray(value)) {
                return value
                    .map(item => (typeof item === "string" ? item.trim() : ""))
                    .filter(Boolean);
            }
            if (typeof value === "string") {
                const trimmed = value.trim();
                return trimmed ? [trimmed] : [];
            }
            return [];
        }

        function normalizeEdadRango(value) {
            const candidates = Array.isArray(value) ? value : [value];
            for (const candidate of candidates) {
                if (typeof candidate !== "string") continue;
                const trimmed = candidate.trim();
                if (EDAD_RANGOS_SET.has(trimmed)) return trimmed;
            }
            return "";
        }

        function normalizeMetadataLocation(value) {
            if (Array.isArray(value)) {
                for (const candidate of value) {
                    if (typeof candidate !== "string") continue;
                    const trimmed = candidate.trim();
                    if (trimmed) return trimmed;
                }
                return "";
            }
            if (typeof value === "string") {
                return value.trim();
            }
            return "";
        }

        function normalizeMetadata(rawMetadata, profile = {}) {
            const metadata = (rawMetadata && typeof rawMetadata === "object" && !Array.isArray(rawMetadata)) ? rawMetadata : {};
            const labels = cleanStringArray(metadata.labels);
            const ubicacion = normalizeMetadataLocation(metadata.ubicacion);
            const edad_rango = normalizeEdadRango(metadata.edad_rango);
            return {
                labels,
                ubicacion,
                edad_rango,
                nuevo_ingreso: !!metadata.nuevo_ingreso,
                sin_experiencia: !!metadata.sin_experiencia,
                cortesia: !!metadata.cortesia,
                nuevas_fotos_videos: !!metadata.nuevas_fotos_videos,
                lista_discreta: !!metadata.lista_discreta || !!profile.discreet_list,
            };
        }

        function toRuntimeProfile(profile, idx) {
            const p = (profile && typeof profile === "object" && !Array.isArray(profile)) ? profile : {};
            const metadata = normalizeMetadata(p.metadata, p);
            const media = Array.isArray(p.media)
                ? p.media.filter(src => typeof src === "string" && src.trim())
                : [];
            const reviews = Array.isArray(p.reviews)
                ? p.reviews.filter(review => typeof review === "string" && review.trim())
                : [];
            return {
                ...p,
                profile: p.profile || `profile_${idx + 1}`,
                metadata,
                media,
                extraction: (p.extraction && typeof p.extraction === "object" && !Array.isArray(p.extraction)) ? p.extraction : {},
                reviews,
                discreet_list: !!p.discreet_list,
            };
        }

        function collectSearchValues(value, target, depth = 0) {
            if (value === null || value === undefined) return;
            if (typeof value === "string") {
                const trimmed = value.trim();
                if (trimmed) target.push(trimmed);
                return;
            }
            if (typeof value === "number" || typeof value === "boolean") {
                target.push(String(value));
                return;
            }
            if (depth >= 3) return;
            if (Array.isArray(value)) {
                value.forEach(item => collectSearchValues(item, target, depth + 1));
                return;
            }
            if (typeof value === "object") {
                Object.values(value).forEach(item => collectSearchValues(item, target, depth + 1));
            }
        }

        function buildSearchBlob(profile, structured, pathMetadata, metadataLabels) {
            const parts = [];
            collectSearchValues(profile.profile, parts);
            collectSearchValues(pathMetadata, parts);
            collectSearchValues(metadataLabels, parts);
            collectSearchValues(profile.metadata, parts);
            collectSearchValues(profile.extraction, parts);
            collectSearchValues(profile.reviews, parts);
            collectSearchValues(structured, parts);
            return normalizeText(parts.join(" "));
        }

        function transformProfiles(profiles = []) {
            return profiles
                .map((profile, idx) => toRuntimeProfile(profile, idx))
                .filter(isProfileEnabled)
                .map(profile => {
                    const structured = mergeStructuredData(profile);
                    const pathMetadata = buildPathMetadata(profile);
                    const metadataLabels = buildMetadataLabels(profile);
                    const filterTokens = buildFilterTokens(profile);
                    const media = resolveMediaAssets(profile);
                    const mediaEntries = [
                        ...media.images.map(src => ({ type: "image", src })),
                        ...media.videos.map(src => ({ type: "video", src })),
                    ];
                    const reviewCount = profile.reviews.length;
                    const searchBlob = buildSearchBlob(profile, structured, pathMetadata, metadataLabels);
                    return {
                        id: profile.profile,
                        structured_data: structured,
                        path_metadata: pathMetadata,
                        images: media.images,
                        videos: media.videos,
                        media_entries: mediaEntries,
                        review_count: reviewCount,
                        search_blob: searchBlob,
                        is_discreet: profile.discreet_list,
                        raw_profile: profile,
                        metadata_labels: metadataLabels,
                        filter_tokens: filterTokens,
                    };
                });
        }

        function mergeStructuredData(profile) {
            const base = profile.merged_structured_data ? JSON.parse(JSON.stringify(profile.merged_structured_data)) : {};
            const extraction = profile.extraction || {};
            base.name = base.name || extraction.name || profile.profile || null;
            base.age = base.age || extraction.age || null;
            const mergedLocation = base.location || extraction.location || null;
            base.location = normalizeLocation(mergedLocation);
            base.raw_text = base.raw_text || (profile.raw_responses?.join("\n\n") || "");
            if (!base.standard_prices) {
                base.standard_prices = { one_hour: null, two_hours: null, three_hours: null, overnight: null };
            }
            if (!Array.isArray(base.prices)) base.prices = [];
            const mergedAvailability = base.availability || extraction.availability || null;
            base.availability = normalizeAvailability(mergedAvailability);
            if (!base.contact) base.contact = {};
            if (extraction.contact && !base.contact.notes) base.contact.notes = extraction.contact;
            if (!base.attributes) base.attributes = {};
            const attrMap = {
                height: extraction.height,
                weight: extraction.weight,
                hair_color: extraction.hair_color,
                eye_color: extraction.eye_color,
            };
            Object.entries(attrMap).forEach(([key, value]) => {
                if (value && !base.attributes[key]) {
                    base.attributes[key] = value;
                }
            });
            if (base.attributes.implants == null && extraction.implants != null) {
                base.attributes.implants = extraction.implants;
            }
            return base;
        }

        function formatExtractionValue(value) {
            if (value === null || value === undefined) return "—";
            if (typeof value === "boolean") return value ? t("common.yes") : t("common.no");
            if (typeof value === "number") return value.toString();
            if (typeof value === "string") return value.trim() ? value.trim() : "—";
            if (typeof value === "object") {
                const keys = Object.keys(value);
                if (!keys.length) return "{}";
                return JSON.stringify(value, null, 2);
            }
            return String(value);
        }

        function escapeHtml(text) {
            return String(text)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\"/g, "&quot;")
                .replace(/'/g, "&#39;");
        }

        const DEFAULT_WHATSAPP_COUNTRY_CODE = "506"; // Costa Rica (used when contact has 8 digits without country code)
        const PHONE_CANDIDATE_REGEX = /(\+?\d[\d\s\-().]{6,}\d)/g;

        function normalizeWhatsAppE164Digits(digits) {
            if (!digits) return null;
            let clean = digits.toString().replace(/\D/g, "");
            if (!clean) return null;
            if (clean.startsWith("00")) clean = clean.slice(2);
            if (clean.length === 8) clean = DEFAULT_WHATSAPP_COUNTRY_CODE + clean;
            if (clean.length < 8 || clean.length > 15) return null;
            return clean;
        }

        function extractWhatsAppInfo(text) {
            if (!text) return null;
            const raw = text.toString().trim();
            if (!raw) return null;

            const matches = raw.match(PHONE_CANDIDATE_REGEX) || [];
            for (const match of matches) {
                const e164 = normalizeWhatsAppE164Digits(match);
                if (e164) return { e164, display: raw };
            }

            const fallback = normalizeWhatsAppE164Digits(raw);
            if (fallback) return { e164: fallback, display: raw };
            return null;
        }

        function stripWhatsAppPrefix(text) {
            if (!text) return "";
            return text.toString().replace(/^\s*whats?app\s*[:\-]?\s*/i, "").trim();
        }

        function buildWhatsAppPrefillMessage(profileName) {
            const app = t("app.title");
            const name = (profileName || "").toString().trim();
            if (name && name !== t("common.unknown")) {
                return t("contact.whatsappMessageWithName", { name, app });
            }
            return t("contact.whatsappMessage", { app });
        }

        function buildAskForContactPrefillMessage(profileLabel) {
            const profile = (profileLabel || "").toString().trim() || t("common.unknown");
            return t("contact.askForContactMessage", { profile });
        }

        function buildDiscreetEmailLink(profileLabel) {
            const profile = (profileLabel || "").toString().trim() || t("common.unknown");
            const subject = t("contact.discreetEmailSubject", { profile });
            const body = t("contact.discreetEmailMessage", { profile });
            const query = `subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
            return `mailto:${DISCREET_CONTACT_EMAIL}?${query}`;
        }

        function buildWhatsAppLink(e164Digits, message) {
            const phone = normalizeWhatsAppE164Digits(e164Digits);
            if (!phone) return null;
            const text = (message || "").toString();
            const qs = text ? `?text=${encodeURIComponent(text)}` : "";
            return `https://wa.me/${phone}${qs}`;
        }

        function renderExtractionSection(extraction, context = {}) {
            const ex = extraction || {};
            const prices = (ex.prices && typeof ex.prices === "object") ? ex.prices : {};
            const orderedKeys = [
                "name",
                "age",
                "height",
                "weight",
                "hair_color",
                "eye_color",
                "location",
                "availability",
                "contact",
                "prices",
                "implants",
                "uber",
                "cosmetic_surgeries",
                "other_attributes",
            ];
            const priceSlotKeys = ["one_hour", "two_hours", "three_hours", "overnight"];

            function renderPriceSlots(slotObj) {
                const rows = priceSlotKeys.map(key => {
                    const value = slotObj?.[key] ?? null;
                    return `<tr><td>${escapeHtml(labelForPriceSlot(key))}</td><td>${escapeHtml(formatExtractionValue(value))}</td></tr>`;
                }).join("");
                return `<table class="price-table" style="font-size:12px;"><tbody>${rows}</tbody></table>`;
            }

            function renderOtherAttributes(obj) {
                if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
                    return escapeHtml(formatExtractionValue(obj));
                }
                const entries = Object.entries(obj).filter(([k, v]) => {
                    if (!k) return false;
                    if (v === null || v === undefined) return false;
                    const txt = typeof v === "string" ? v.trim() : String(v).trim();
                    return txt.length > 0;
                });
                if (!entries.length) return "—";
                const rows = entries
                    .sort(([a], [b]) => a.localeCompare(b, undefined, { sensitivity: "base" }))
                    .map(([k, v]) => {
                        const label = k.replace(/_/g, " ");
                        const formatted = formatExtractionValue(v);
                        const safe = escapeHtml(formatted);
                        const isObj = typeof v === "object" && v !== null;
                        const valueHtml = isObj ? `<pre style="margin:0; white-space:pre-wrap;">${safe}</pre>` : safe;
                        return `<tr><td>${escapeHtml(label)}</td><td>${valueHtml}</td></tr>`;
                    })
                    .join("");
                return `<table class="price-table kv-table" style="font-size:12px;"><tbody>${rows}</tbody></table>`;
            }

            const rows = orderedKeys.map(key => {
                const label = escapeHtml(labelForExtractionKey(key));
                let value = null;
                if (key === "prices") {
                    value = prices;
                    return `<div class="lb-attr"><span class="k">${label}</span><span class="v">${renderPriceSlots(prices)}</span></div>`;
                }
                if (key === "contact") {
                    value = ex?.[key] ?? null;
                    if (typeof value === "string" && value.trim()) {
                        const info = extractWhatsAppInfo(value);
                        if (info) {
                            const msg = buildWhatsAppPrefillMessage(context.profileName);
                            const link = buildWhatsAppLink(info.e164, msg);
                            if (link) {
                                return `<div class="lb-attr"><span class="k">${label}</span><span class="v"><a href="${link}" target="_blank" rel="noopener noreferrer">${escapeHtml(value.trim())}</a></span></div>`;
                            }
                        }
                    }
                }
                if (key === "other_attributes") {
                    value = ex?.[key] ?? null;
                    return `<div class="lb-attr"><span class="k">${label}</span><span class="v">${renderOtherAttributes(value)}</span></div>`;
                }
                value = ex?.[key] ?? null;
                const formatted = formatExtractionValue(value);
                const isObject = typeof value === "object" && value !== null;
                const safeFormatted = escapeHtml(formatted);
                return `<div class="lb-attr"><span class="k">${label}</span><span class="v">${isObject ? `<pre style="margin:0; white-space:pre-wrap;">${safeFormatted}</pre>` : safeFormatted}</span></div>`;
            }).join("");

            return `<div class="lb-section"><h3>${escapeHtml(t("sections.extraction"))}</h3><div class="lb-attr-grid">${rows}</div></div>`;
        }

        function buildPathMetadata(profile) {
            const metadata = profile.metadata || {};
            const values = [
                ...(metadata.ubicacion ? [metadata.ubicacion] : []),
                ...(metadata.edad_rango ? [metadata.edad_rango] : []),
                ...cleanStringArray(metadata.labels),
            ];
            const seen = new Set();
            return values.filter(value => {
                const key = value.toLowerCase();
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
        }

        function buildMetadataLabels(rawProfile) {
            const metadata = rawProfile?.metadata || {};
            const labels = [];

            const ubicacion = normalizeMetadataLocation(metadata.ubicacion);
            if (ubicacion) labels.push(ubicacion);

            const edadRango = normalizeEdadRango(metadata.edad_rango);
            if (edadRango) labels.push(edadRango);

            if (metadata.nuevo_ingreso) labels.push(CATEGORY_FILTER_VALUES.nuevo_ingreso);
            if (metadata.sin_experiencia) labels.push(CATEGORY_FILTER_VALUES.sin_experiencia);
            if (metadata.cortesia) labels.push(CATEGORY_FILTER_VALUES.cortesia);
            if (metadata.nuevas_fotos_videos) labels.push(CATEGORY_FILTER_VALUES.nuevas_fotos_videos);

            labels.push(...cleanStringArray(metadata.labels));

            const seen = new Set();
            const deduped = [];
            labels.forEach(label => {
                const key = label.toLowerCase();
                if (seen.has(key)) return;
                seen.add(key);
                deduped.push(label);
            });
            return deduped;
        }

        function buildFilterTokens(rawProfile) {
            const metadata = rawProfile.metadata || {};
            const ubicacion = normalizeMetadataLocation(metadata.ubicacion);
            const edadRango = normalizeEdadRango(metadata.edad_rango);
            const nuevosIngresos = !!metadata.nuevo_ingreso;
            const sinExperiencia = !!metadata.sin_experiencia;
            const cortesia = !!metadata.cortesia;
            const nuevasFotosVideos = !!metadata.nuevas_fotos_videos;
            const listaDiscreta = !!metadata.lista_discreta || !!rawProfile.discreet_list;

            return {
                ubicacion: ubicacion ? [ubicacion] : [],
                edad: edadRango ? [edadRango] : [],
                nuevo_ingreso: nuevosIngresos ? [CATEGORY_FILTER_VALUES.nuevo_ingreso] : [],
                sin_experiencia: sinExperiencia ? [CATEGORY_FILTER_VALUES.sin_experiencia] : [],
                cortesia: cortesia ? [CATEGORY_FILTER_VALUES.cortesia] : [],
                nuevas_fotos_videos: nuevasFotosVideos ? [CATEGORY_FILTER_VALUES.nuevas_fotos_videos] : [],
                lista_discreta: listaDiscreta ? [CATEGORY_FILTER_VALUES.lista_discreta] : [],
            };
        }

        const IMAGE_PATH_REGEX = /\.(jpe?g|png|webp|gif)$/i;
        const VIDEO_PATH_REGEX = /\.(mp4|mov|m4v|webm)$/i;

        function resolveMediaAssets(profile) {
            const seen = new Set();
            const images = [];
            const videos = [];
            profile.media.map(src => normalizeMediaPath(src)).filter(Boolean).forEach(path => {
                if (seen.has(path)) return;
                seen.add(path);
                if (IMAGE_PATH_REGEX.test(path)) {
                    images.push(path);
                } else if (VIDEO_PATH_REGEX.test(path)) {
                    videos.push(path);
                }
            });
            return { images, videos };
        }

        function normalizeMediaPath(src) {
            if (!src) return null;
            if (/^https?:\/\//i.test(src)) return src;
            if (src.startsWith("../") || src.startsWith("./")) return src;
            const clean = src.replace(/^\/+/, "");
            return MEDIA_BASE_PATH + clean;
        }

        function getFiltersMountEl() {
            return document.getElementById('filters-content') || document.getElementById('filters');
        }

        function buildFilters() {
            const filtersContainer = getFiltersMountEl();
            if (!filtersContainer) return;
            filtersContainer.querySelectorAll('.filter-group').forEach(group => group.remove());

            filters = {};
            filterOptionCounts = {};
            FILTER_SPECS.forEach(spec => {
                filters[spec.key] = new Set();
                filterOptionCounts[spec.key] = new Map();
                if (!activeFilters[spec.key]) {
                    activeFilters[spec.key] = new Set();
                }
            });

            // Always show curated filter choices even if a category has 0 matches.
            filters.ubicacion = new Set(UBICACION_OPTIONS);
            filters.edad = new Set(EDAD_RANGOS);
            filters.nuevo_ingreso.add(CATEGORY_FILTER_VALUES.nuevo_ingreso);
            filters.sin_experiencia.add(CATEGORY_FILTER_VALUES.sin_experiencia);
            filters.cortesia.add(CATEGORY_FILTER_VALUES.cortesia);
            filters.nuevas_fotos_videos.add(CATEGORY_FILTER_VALUES.nuevas_fotos_videos);
            filters.lista_discreta.add(CATEGORY_FILTER_VALUES.lista_discreta);

            catalog.forEach(item => {
                const tokens = item.filter_tokens || {};
                FILTER_SPECS.forEach(spec => {
                    (tokens[spec.key] || []).forEach(val => {
                        filters[spec.key].add(val);
                        const countMap = filterOptionCounts[spec.key];
                        countMap.set(val, (countMap.get(val) || 0) + 1);
                    });
                });
            });

            FILTER_SPECS.forEach(spec => {
                if (GROUPED_CATEGORY_FILTER_KEYS.has(spec.key)) return;
                renderFilterUI(t(spec.labelKey), filters[spec.key], spec.key);
            });
            renderCategoryToggles();
        }

        function renderFilterUI(label, set, key) {
            if (!set || set.size === 0) return;
            const group = document.createElement('div');
            group.className = 'filter-group';
            const header = document.createElement('h3');
            header.textContent = label;
            group.appendChild(header);
            Array.from(set).sort().forEach(val => {
                const l = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = activeFilters[key]?.has(val);
                checkbox.onchange = () => toggleFilter(key, val);
                l.appendChild(checkbox);
                const count = filterOptionCounts[key]?.get(val) || 0;
                l.appendChild(document.createTextNode(` ${val} (${count})`));
                group.appendChild(l);
            });
            getFiltersMountEl()?.appendChild(group);
        }

        function renderCategoryToggles() {
            const group = document.createElement('div');
            group.className = 'filter-group';
            const header = document.createElement('h3');
            header.textContent = t('filters.categories');
            group.appendChild(header);

            const items = [
                { key: 'nuevo_ingreso', value: CATEGORY_FILTER_VALUES.nuevo_ingreso, labelKey: 'filters.categoryNewArrivalsOnly' },
                { key: 'sin_experiencia', value: CATEGORY_FILTER_VALUES.sin_experiencia, labelKey: 'filters.categoryNoExperienceOnly' },
                { key: 'cortesia', value: CATEGORY_FILTER_VALUES.cortesia, labelKey: 'filters.categoryCourtesyOnly' },
                { key: 'nuevas_fotos_videos', value: CATEGORY_FILTER_VALUES.nuevas_fotos_videos, labelKey: 'filters.categoryNewMediaOnly' },
                { key: 'lista_discreta', value: CATEGORY_FILTER_VALUES.lista_discreta, labelKey: 'filters.categoryDiscreetListOnly' },
            ];

            items.forEach(({ key, value, labelKey }) => {
                const l = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = activeFilters[key]?.has(value) || false;
                checkbox.onchange = () => toggleFilter(key, value);
                l.appendChild(checkbox);
                const count = filterOptionCounts[key]?.get(value) || 0;
                l.appendChild(document.createTextNode(` ${t(labelKey)} (${count})`));
                group.appendChild(l);
            });

            getFiltersMountEl()?.appendChild(group);
        }

        window.toggleFilter = (k, v) => {
            if (!activeFilters[k]) activeFilters[k] = new Set();
            if (activeFilters[k].has(v)) activeFilters[k].delete(v);
            else activeFilters[k].add(v);
            requestRender();
        };

        function syncOverlayLock() {
            const authActive = document.getElementById("auth-overlay")?.classList.contains("active");
            const disclaimerActive = document.getElementById("disclaimer-overlay")?.classList.contains("active");
            const lightboxActive = document.getElementById("lightbox")?.classList.contains("active");
            const filtersActive = document.getElementById("filters")?.classList.contains("active");
            const shouldLock = !!(authActive || disclaimerActive || lightboxActive || filtersActive);
            document.body.classList.toggle("overlay-open", shouldLock);

            const mobile = isMobileLightboxViewport();
            if (!mobile) {
                if (scrollLockActive) {
                    document.body.style.position = "";
                    document.body.style.top = "";
                    document.body.style.left = "";
                    document.body.style.right = "";
                    document.body.style.width = "";
                    window.scrollTo(0, scrollLockY);
                    scrollLockActive = false;
                }
                return;
            }

            if (shouldLock && !scrollLockActive) {
                scrollLockY = window.scrollY || 0;
                document.body.style.position = "fixed";
                document.body.style.top = `-${scrollLockY}px`;
                document.body.style.left = "0";
                document.body.style.right = "0";
                document.body.style.width = "100%";
                scrollLockActive = true;
            } else if (!shouldLock && scrollLockActive) {
                document.body.style.position = "";
                document.body.style.top = "";
                document.body.style.left = "";
                document.body.style.right = "";
                document.body.style.width = "";
                window.scrollTo(0, scrollLockY);
                scrollLockActive = false;
            }
        }

        function openFilters() {
            const authActive = document.getElementById("auth-overlay")?.classList.contains("active");
            const disclaimerActive = document.getElementById("disclaimer-overlay")?.classList.contains("active");
            const lightboxActive = document.getElementById("lightbox")?.classList.contains("active");
            if (authActive || disclaimerActive || lightboxActive) return;

            document.getElementById("filters")?.classList.add("active");
            document.getElementById("filters-backdrop")?.classList.add("active");
            document.body.classList.add("filters-open");
            document.getElementById("filters-toggle")?.setAttribute("aria-expanded", "true");
            syncOverlayLock();
        }

        function closeFilters() {
            document.getElementById("filters")?.classList.remove("active");
            document.getElementById("filters-backdrop")?.classList.remove("active");
            document.body.classList.remove("filters-open");
            document.getElementById("filters-toggle")?.setAttribute("aria-expanded", "false");
            syncOverlayLock();
        }

        window.openFilters = openFilters;
        window.closeFilters = closeFilters;

        function hideDisclaimer() {
            const overlay = document.getElementById("disclaimer-overlay");
            if (!overlay) return;
            overlay.classList.remove("active");
            syncOverlayLock();
        }

        function showDisclaimer() {
            const overlay = document.getElementById("disclaimer-overlay");
            if (!overlay) return;
            overlay.classList.add("active");
            syncOverlayLock();
        }

        function showAuthGate() {
            const overlay = document.getElementById("auth-overlay");
            if (!overlay) return;
            overlay.classList.add("active");
            const error = document.getElementById("auth-error");
            if (error) error.textContent = "";
            const input = document.getElementById("auth-password");
            if (input) {
                input.value = "";
                setTimeout(() => input.focus(), 0);
            }
            syncOverlayLock();
        }

        function hideAuthGate() {
            const overlay = document.getElementById("auth-overlay");
            if (!overlay) return;
            overlay.classList.remove("active");
            syncOverlayLock();
        }

        function getRememberedAuthLevel() {
            try {
                const stored = localStorage.getItem(AUTH_STORAGE_KEY);
                if (!stored) return null;
                if (stored === "elite") return "elite";
                if (stored === "standard") return "standard";
                // Legacy: stored hashes.
                if (stored === AUTH_SHA256_B64) return "standard";
                if (AUTH_ELITE_SHA256_B64 && stored === AUTH_ELITE_SHA256_B64) return "elite";
                return null;
            } catch (_) {
                return null;
            }
        }

        function setRememberedAuth(levelOrNull) {
            try {
                if (!levelOrNull) localStorage.removeItem(AUTH_STORAGE_KEY);
                else localStorage.setItem(AUTH_STORAGE_KEY, levelOrNull);
            } catch (_) { /* ignore */ }
        }

        async function sha256Base64(text) {
            if (!(window.crypto && window.crypto.subtle)) {
                throw new Error(t("auth.webcryptoUnavailable"));
            }
            const bytes = new TextEncoder().encode(text);
            const hashBuffer = await crypto.subtle.digest("SHA-256", bytes);
            const hashBytes = new Uint8Array(hashBuffer);
            let binary = "";
            hashBytes.forEach(b => { binary += String.fromCharCode(b); });
            return btoa(binary);
        }

        function startApp() {
            if (!authLevel) authLevel = "standard";
            showDisclaimer();
            loadData();
        }

        function setAuthError(message) {
            const el = document.getElementById("auth-error");
            if (!el) return;
            el.textContent = message || "";
        }

        function setAuthBusy(busy) {
            const btn = document.getElementById("auth-submit");
            if (btn) btn.disabled = !!busy;
            const input = document.getElementById("auth-password");
            if (input) input.disabled = !!busy;
            const remember = document.getElementById("auth-remember");
            if (remember) remember.disabled = !!busy;
        }

        function initAuthGate() {
            const form = document.getElementById("auth-form");
            const input = document.getElementById("auth-password");
            const remember = document.getElementById("auth-remember");

            if (!form || !input || !remember) {
                // If the gate UI is missing, fail open to avoid breaking the page.
                startApp();
                return;
            }

            const rememberedLevel = getRememberedAuthLevel();
            if (rememberedLevel) {
                authLevel = rememberedLevel;
                hideAuthGate();
                startApp();
                return;
            }

            showAuthGate();

            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                setAuthError("");
                const pw = (input.value || "").trim();
                if (!pw) {
                    setAuthError(t("auth.required"));
                    input.focus();
                    return;
                }

                setAuthBusy(true);
                try {
                    const computed = await sha256Base64(pw);
                    let level = null;
                    if (AUTH_ELITE_SHA256_B64 && computed === AUTH_ELITE_SHA256_B64) {
                        level = "elite";
                    } else if (computed === AUTH_SHA256_B64) {
                        level = "standard";
                    }
                    if (!level) {
                        setAuthError(t("auth.wrong"));
                        input.focus();
                        input.select?.();
                        return;
                    }
                    authLevel = level;
                    setRememberedAuth(remember.checked ? level : null);
                    hideAuthGate();
                    startApp();
                } catch (err) {
                    console.error(err);
                    setAuthError(err?.message || t("auth.error"));
                } finally {
                    setAuthBusy(false);
                }
            });
        }

        const DURATION_SYNONYMS = {
            "1 hora": ["1 hora", "1hr", "1 hr", "1h", "una hora"],
            "2 horas": ["2 horas", "2hr", "2 hrs", "2h", "dos horas"],
            "3 horas": ["3 horas", "3hr", "3 hrs", "3h", "tres horas"],
            "Toda la noche": [
                "toda la noche",
                "noche completa",
                "overnight",
                "9:00 pm a 7:00 am",
                "9 pm a 7 am",
                "9pm a 7am",
                "7 pm a 8 am",
                "9 pm a 6 am"
            ],
        };

        const STANDARD_DURATION_ORDER = [
            { key: "one_hour", canonical: "1 hora" },
            { key: "two_hours", canonical: "2 horas" },
            { key: "three_hours", canonical: "3 horas" },
            { key: "overnight", canonical: "Toda la noche" },
        ];

        function normalizeDurationLabel(label) {
            if (!label) return "";
            const normalized = label.toString().toLowerCase().replace(/\s+/g, " ");
            for (const [canonical, patterns] of Object.entries(DURATION_SYNONYMS)) {
                if (patterns.some(pattern => normalized.includes(pattern))) {
                    return canonical;
                }
            }
            return "";
        }

        function inferCurrency(prices) {
            if (!Array.isArray(prices)) return "CRC";
            for (const item of prices) {
                if (item && typeof item === "object" && item.currency) {
                    return item.currency;
                }
            }
            return "CRC";
        }

        function formatVal(p) {
            const c = (p.currency || '').toUpperCase();
            const s = (c === 'CRC' || c === 'COLONES') ? '₡' : (c === 'USD' ? '$' : c);
            return s + (p.amount ? Number(p.amount).toLocaleString() : '0');
        }

        function formatAmount(amount, currency) {
            return formatVal({ amount, currency });
        }

        function buildStandardPriceEntries(profile) {
            const prices = profile.prices || [];
            const standard = profile.standard_prices || {};
            const fallbackCurrency = inferCurrency(prices);

            return STANDARD_DURATION_ORDER.map(def => {
                const amount = standard[def.key];
                if (amount == null) return null;
                const matched = prices.find(p => normalizeDurationLabel(p.duration) === def.canonical);
                const currency = matched?.currency || fallbackCurrency;
                return {
                    label: durationLabel(def.key),
                    short: durationShort(def.key),
                    value: formatAmount(amount, currency)
                };
            }).filter(Boolean);
        }

        function buildStandardSummary(profile) {
            const entries = buildStandardPriceEntries(profile);
            if (!entries.length) return "";
            return entries.map(entry => `${entry.short} ${entry.value}`).join(' · ');
        }

        let filteredItems_ = []; // Store references for index access
        let currentItemIndex = -1;
        let currentMediaIndex = 0;
        let currentMediaEntries = [];
        let renderScheduled = false;

	        function renderMediaCounter(images, videos, reviewsCount) {
	            const photoCount = Array.isArray(images) ? images.length : 0;
	            const videoCount = Array.isArray(videos) ? videos.length : 0;
                const reviewCount = Number.isFinite(Number(reviewsCount)) ? Number(reviewsCount) : 0;
	            if (!photoCount && !videoCount && !reviewCount) return '';
            const iconPhoto = `<svg class="mc-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>`;
            const iconVideo = `<svg class="mc-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect><polygon points="23 7 16 12 23 17 23 7" fill="currentColor" stroke="none"></polygon></svg>`;
            const iconReview = `<svg class="mc-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>`;
            const parts = [];
            if (photoCount) parts.push(`<span class="mc-item" title="${escapeHtml(t("media.photos"))}">${iconPhoto} ${photoCount}</span>`);
            if (videoCount) parts.push(`<span class="mc-item" title="${escapeHtml(t("media.videos"))}">${iconVideo} ${videoCount}</span>`);
            if (reviewCount) parts.push(`<span class="mc-item" title="${escapeHtml(t("media.reviews"))}">${iconReview} ${reviewCount}</span>`);
	            return `<div class="media-counter">${parts.join('')}</div>`;
	        }

        function hasEliteAccess() {
            return authLevel === "elite";
        }

        function canShowProfileMedia(item) {
            return !(item && item.is_discreet) || hasEliteAccess();
        }

        function discreetIconSvg() {
            return `<svg class="discreet-icon" viewBox="0 0 64 64" aria-hidden="true" fill="currentColor"><path d="M32 34c8.837 0 16-7.163 16-16S40.837 2 32 2 16 9.163 16 18s7.163 16 16 16Zm0 4c-10.667 0-24 5.333-24 16v6h48v-6c0-10.667-13.333-16-24-16Z"/></svg>`;
        }

        function renderDiscreetPlaceholderInner() {
            return `${discreetIconSvg()}<div class="discreet-label">${escapeHtml(t("media.discreetProfile"))}</div>`;
        }

        function normalizeText(text) {
            if (text === null || text === undefined) return "";
            return String(text)
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, " ")
                .replace(/\s+/g, " ")
                .trim();
        }

        function requestRender() {
            if (renderScheduled) return;
            renderScheduled = true;
            requestAnimationFrame(() => {
                renderScheduled = false;
                render();
            });
        }

        window.requestRender = requestRender;

        function render() {
            const searchInputEl = document.getElementById("searchInput");
            const statsEl = document.getElementById("stats");
            const gridEl = document.getElementById("grid");
            if (!searchInputEl || !statsEl || !gridEl) return;

            const queryRaw = searchInputEl.value || "";
            const q = normalizeText(queryRaw);
            const qTokens = q ? q.split(" ").filter(Boolean) : [];

            const filtered = catalog.filter(item => {
                const haystack = item.search_blob || "";
                if (qTokens.length && !qTokens.every(token => haystack.includes(token))) return false;
                const tokens = item.filter_tokens || {};
                let anyCategorySelected = false;
                let categoryMatches = false;
                for (const spec of FILTER_SPECS) {
                    const activeSet = activeFilters[spec.key];
                    if (activeSet && activeSet.size) {
                        const values = tokens[spec.key] || [];
                        if (GROUPED_CATEGORY_FILTER_KEYS.has(spec.key)) {
                            anyCategorySelected = true;
                            if (values.some(val => activeSet.has(val))) categoryMatches = true;
                            continue;
                        }
                        if (!values.some(val => activeSet.has(val))) return false;
                    }
                }
                if (anyCategorySelected && !categoryMatches) return false;
                return true;
            });

            filteredItems_ = filtered;
            statsEl.textContent = t("controls.statsFound", { count: filtered.length });

            gridEl.innerHTML = filtered.map((item, idx) => {
                const d = item.structured_data || {};
                const canShowMedia = canShowProfileMedia(item);
                const primaryMedia = canShowMedia ? item.media_entries?.[0] : null;
                const reviewCount = Number.isFinite(Number(item.review_count))
                    ? Number(item.review_count)
                    : (Array.isArray(item.raw_profile?.reviews) ? item.raw_profile.reviews.filter(r => typeof r === "string" && r.trim()).length : 0);
                const counterHtml = renderMediaCounter(item.images, item.videos, reviewCount);
                let mediaInner = "";
                if (!canShowMedia) {
                    mediaInner = `<div class="discreet-placeholder">${renderDiscreetPlaceholderInner()}</div>`;
                } else if (primaryMedia) {
                    if (primaryMedia.type === "image") {
                        mediaInner = `<img class="main-img" src="${primaryMedia.src}" loading="lazy" decoding="async" fetchpriority="low">`;
                    } else {
                        mediaInner = `<video class="main-img" src="${primaryMedia.src}" muted loop playsinline preload="metadata"></video>`;
                    }
                }
                const mediaMarkup = `<div class="card-img-container">${mediaInner}${counterHtml}</div>`;

                const name = d.name || item.id || t("common.unknown");
                const loc = d.location || "";
                const ageText = (d.age !== null && d.age !== undefined && d.age !== "") ? t("profile.ageCard", { age: d.age }) : "";
                const stdSummary = buildStandardSummary(d);
                const prices = stdSummary || (d.prices || []).map(formatVal).join(" · ");

                const serviceTags = (d.services || []).slice(0, 3).map(s => `<span class="pill">${s}</span>`).join("");
                const metadataLabelHtml = (item.metadata_labels || []).slice(0, 3).map(label => `<span class="pill" style="background:#ffecec;color:#c81d4d;">${label}</span>`).join("");

                return `
                <div class="card" onclick="openProfile(${idx})">
                    ${mediaMarkup}
                    <div class="card-details">
                        <div class="name">${name}</div>
                        ${ageText ? `<div class="age">${ageText}</div>` : ""}
                        ${loc ? `<div class="location">${loc}</div>` : ""}
                        ${prices ? `<div class="price">${prices}</div>` : ""}
                        <div class="tags">${metadataLabelHtml}${serviceTags}</div>
                    </div>
                </div>`;
            }).join("");
        }

        function isMobileLightboxViewport() {
            try {
                return window.matchMedia("(max-width: 800px)").matches;
            } catch (_) {
                return (window.innerWidth || 0) <= 800;
            }
        }

        function setLightboxMediaFullscreen(enabled) {
            const lightbox = document.getElementById("lightbox");
            if (!lightbox) return;
            lightbox.classList.toggle("media-fullscreen", !!enabled);
        }

        function toggleLightboxMediaFullscreen() {
            if (!isMobileLightboxViewport()) return;
            const lightbox = document.getElementById("lightbox");
            if (!lightbox || !lightbox.classList.contains("active")) return;
            lightbox.classList.toggle("media-fullscreen");
        }

        function exitLightboxMediaFullscreen() {
            setLightboxMediaFullscreen(false);
        }

        function getReviewsCarouselEls() {
            const track = document.getElementById("reviews-track");
            if (!track) return null;
            const slides = Array.from(track.children || []);
            return {
                track,
                slides,
                total: slides.length,
                carousel: document.getElementById("reviews-carousel"),
                prevBtn: document.getElementById("reviews-prev"),
                nextBtn: document.getElementById("reviews-next"),
                indicator: document.getElementById("reviews-indicator"),
                dots: document.getElementById("reviews-dots"),
            };
        }

        function getReviewsCarouselIndex(track) {
            const n = Number(track?.dataset?.index || 0);
            return Number.isFinite(n) ? n : 0;
        }

        function updateReviewsCarousel() {
            const els = getReviewsCarouselEls();
            if (!els) return;
            const { track, slides, total, prevBtn, nextBtn, indicator, dots } = els;
            if (!total) return;

            const idxRaw = getReviewsCarouselIndex(track);
            const idx = Math.min(Math.max(idxRaw, 0), total - 1);
            track.dataset.index = String(idx);
            track.style.transform = `translateX(-${idx * 100}%)`;

            if (prevBtn) prevBtn.disabled = total <= 1;
            if (nextBtn) nextBtn.disabled = total <= 1;
            if (indicator) indicator.textContent = total > 1 ? `${idx + 1} / ${total}` : "";

            slides.forEach((slide, i) => {
                slide.setAttribute("aria-hidden", i === idx ? "false" : "true");
            });

            if (dots) {
                const dotBtns = Array.from(dots.querySelectorAll("button.reviews-dot"));
                dotBtns.forEach((btn, i) => btn.classList.toggle("active", i === idx));
            }
        }

        function setReviewsCarouselIndex(index) {
            const els = getReviewsCarouselEls();
            if (!els) return;
            const { track, total } = els;
            if (!total) return;
            const next = ((index % total) + total) % total;
            track.dataset.index = String(next);
            updateReviewsCarousel();
        }

        window.reviewCarouselStep = (delta) => {
            const els = getReviewsCarouselEls();
            if (!els) return;
            const { track, total } = els;
            if (total <= 1) return;
            const idx = getReviewsCarouselIndex(track);
            const step = Number(delta);
            setReviewsCarouselIndex(idx + (Number.isFinite(step) ? step : 0));
        };

        window.reviewCarouselGo = (idx) => {
            const n = Number(idx);
            if (!Number.isFinite(n)) return;
            setReviewsCarouselIndex(n);
        };

        function initReviewsCarousel() {
            const els = getReviewsCarouselEls();
            if (!els) return;
            const { track, slides, total, dots, carousel } = els;
            if (!total) return;

            track.dataset.index = "0";

            if (dots) {
                if (total > 1 && total <= 8) {
                    dots.style.display = "flex";
                    dots.innerHTML = slides.map((_, i) => {
                        const active = i === 0 ? " active" : "";
                        const title = `${t("sections.reviews")} ${i + 1}`;
                        return `<button class="reviews-dot${active}" type="button" title="${escapeHtml(title)}" onclick="reviewCarouselGo(${i})"></button>`;
                    }).join("");
                } else {
                    dots.style.display = "none";
                    dots.innerHTML = "";
                }
            }

            updateReviewsCarousel();

            if (carousel) {
                let startX = null;
                let startY = null;
                let pointerId = null;

                carousel.onpointerdown = (e) => {
                    if (total <= 1) return;
                    pointerId = e.pointerId;
                    startX = e.clientX;
                    startY = e.clientY;
                    try { carousel.setPointerCapture(pointerId); } catch (_) { /* ignore */ }
                };

                carousel.onpointerup = (e) => {
                    if (pointerId == null || e.pointerId !== pointerId) return;
                    const dx = e.clientX - startX;
                    const dy = e.clientY - startY;
                    pointerId = null;
                    startX = null;
                    startY = null;
                    if (Math.abs(dx) < 40) return;
                    if (Math.abs(dx) <= Math.abs(dy)) return;
                    window.reviewCarouselStep(dx < 0 ? 1 : -1);
                };

                carousel.onpointercancel = () => {
                    pointerId = null;
                    startX = null;
                    startY = null;
                };
            }
        }

	        window.openProfile = (idx) => {
	            const item = filteredItems_[idx];
	            if (!item) return;
                exitLightboxMediaFullscreen();
	            const d = item.structured_data || {};

	            // Media
                const canShowMedia = canShowProfileMedia(item);
	            const mediaEntries = canShowMedia ? (item.media_entries || []) : [];
	            currentMediaEntries = mediaEntries;
                const discreetEl = document.getElementById('lb-discreet');
                if (discreetEl) {
                    if (canShowMedia) {
                        discreetEl.classList.remove("active");
                        discreetEl.setAttribute("aria-hidden", "true");
                        discreetEl.innerHTML = "";
                    } else {
                        discreetEl.classList.add("active");
                        discreetEl.setAttribute("aria-hidden", "false");
                        discreetEl.innerHTML = renderDiscreetPlaceholderInner();
                    }
                }
	            const mainImg = document.getElementById('lb-main-img');
	            const mainVideo = document.getElementById('lb-main-video');
	            const thumbs = document.getElementById('lb-thumbs');
                const navLeft = document.getElementById('lb-nav-left');
                const navRight = document.getElementById('lb-nav-right');
                const showNav = canShowMedia && mediaEntries.length > 1;
                if (thumbs) {
                    thumbs.style.display = (canShowMedia && mediaEntries.length > 1) ? '' : 'none';
                }
	            thumbs.innerHTML = (canShowMedia && mediaEntries.length > 1) ? mediaEntries.map((entry, mediaIdx) =>
	                entry.type === "image"
	                    ? `<img src="${entry.src}" class="lb-thumb" loading="lazy" decoding="async" onclick="switchMedia(${mediaIdx})">`
	                    : `<video src="${entry.src}" class="lb-thumb" muted playsinline preload="metadata" onclick="switchMedia(${mediaIdx})"></video>`
	            ).join('') : '';
                if (navLeft) navLeft.style.display = showNav ? 'flex' : 'none';
                if (navRight) navRight.style.display = showNav ? 'flex' : 'none';
	            currentItemIndex = idx;
	            currentMediaIndex = 0;
	            if (canShowMedia && mediaEntries.length) {
	                updateLightboxMedia();
            } else {
                mainVideo.pause();
                mainImg.style.display = "none";
                mainVideo.style.display = "none";
                mainImg.src = "";
                mainVideo.removeAttribute("src");
	            }

	            // Details
	            const name = d.name || item.id || t("common.unknown");
	            const ageText = (d.age !== null && d.age !== undefined && d.age !== '') ? t("profile.ageSubtitle", { age: d.age }) : '';
	            const loc = d.location || '';
            const subtitleParts = [];
            if (loc) subtitleParts.push(loc);
            if (ageText) subtitleParts.push(ageText);
            const subtitle = subtitleParts.join(' • ');

            let html = `
                <div class="lb-header">
                    <h1>${name}</h1>
                    ${subtitle ? `<p>${subtitle}</p>` : ''}
                </div>
            `;

            const extraction = item.raw_profile?.extraction || {};
            html += renderExtractionSection(extraction, { profileName: name });

            // Attributes
            const attrKeys = ['height', 'weight', 'measurements', 'hair_color', 'eye_color', 'implants'];
            let attrHtml = '';
            attrKeys.forEach(k => {
                // Avoid repeating fields already shown in the extraction block.
                if (extraction[k] !== undefined && extraction[k] !== null && extraction[k] !== '') return;
                let v = d.attributes?.[k];
                if (v === true) v = t("common.yes");
                if (v === false) v = t("common.no");
                const label = escapeHtml(labelForExtractionKey(k));
                if (v) attrHtml += `<div class="lb-attr"><span class="k">${label}</span><span class="v">${v}</span></div>`;
            });
            if (attrHtml) html += `<div class="lb-section"><h3>${escapeHtml(t("sections.attributes"))}</h3><div class="lb-attr-grid">${attrHtml}</div></div>`;

            const standardEntries = buildStandardPriceEntries(d);
            const extraPrices = (d.prices || []).filter(p => {
                const canonical = normalizeDurationLabel(p?.duration);
                return !canonical || !STANDARD_DURATION_ORDER.some(def => def.canonical === canonical);
            });

            if (standardEntries.length || extraPrices.length) {
                let tableRows = '';

                standardEntries.forEach(entry => {
                    tableRows += `<tr><td>${entry.label}</td><td>${entry.value}</td></tr>`;
                });

                extraPrices.forEach(p => {
                    tableRows += `<tr><td>${p.duration || t("table.service")}</td><td>${formatVal(p)}</td></tr>`;
                });

                html += `
                    <div class="lb-section">
                        <h3>${escapeHtml(t("sections.rates"))}</h3>
                        <table class="price-table">
                            <thead>
                                <tr><th>${escapeHtml(t("table.service"))}</th><th>${escapeHtml(t("table.amount"))}</th></tr>
                            </thead>
                            <tbody>
                                ${tableRows}
                            </tbody>
                        </table>
                    </div>`;
            }

            // Services
            if (d.services?.length) {
                html += `<div class="lb-section"><h3>${escapeHtml(t("sections.services"))}</h3>
                <div style="display:flex; flex-wrap:wrap; gap:6px;">
                    ${d.services.map(s => `<span class="pill" style="font-size:12px; padding:6px 10px;">${s}</span>`).join('')}
                </div></div>`;
            }

            // Reviews
            const reviews = Array.isArray(item.raw_profile?.reviews) ? item.raw_profile.reviews : [];
            const cleanReviews = reviews.filter(r => typeof r === "string" && r.trim());
            const reviewSlides = cleanReviews
                .map(r => `<li class="review-slide"><div class="review-card"><div class="review-text">${escapeHtml(r.trim())}</div></div></li>`)
                .join("");
            if (reviewSlides) {
                html += `
                    <div class="lb-section">
                        <div class="reviews-head">
                            <h3>${escapeHtml(t("sections.reviews"))}<span class="reviews-count">${cleanReviews.length}</span></h3>
                            <div class="reviews-controls">
                                <button id="reviews-prev" class="reviews-nav-btn" type="button" aria-label="${escapeHtml(t("reviews.prev"))}" onclick="reviewCarouselStep(-1)">‹</button>
                                <span id="reviews-indicator" class="reviews-indicator"></span>
                                <button id="reviews-next" class="reviews-nav-btn" type="button" aria-label="${escapeHtml(t("reviews.next"))}" onclick="reviewCarouselStep(1)">›</button>
                            </div>
                        </div>
                        <div id="reviews-carousel" class="reviews-carousel" role="region" aria-label="${escapeHtml(t("reviews.aria"))}">
                            <ol id="reviews-track" class="reviews-track">${reviewSlides}</ol>
                        </div>
                        <div id="reviews-dots" class="reviews-dots" aria-hidden="true"></div>
                    </div>
                `;
            }

            // Contact
            const contactRows = [];
            const extractionContact = item.raw_profile?.extraction?.contact;
            const notesValue = d.contact?.notes;
            const waInfo =
                extractWhatsAppInfo(d.contact?.whatsapp) ||
                extractWhatsAppInfo(extractionContact) ||
                extractWhatsAppInfo(notesValue);
            const waMsg = waInfo ? buildWhatsAppPrefillMessage(name) : "";
            const waLink = waInfo ? buildWhatsAppLink(waInfo.e164, waMsg) : null;
            const waDisplay = waInfo ? (stripWhatsAppPrefix(waInfo.display) || waInfo.e164) : "";
            const extractionObj = item.raw_profile?.extraction;
            const isExplicitNullContact =
                extractionObj &&
                typeof extractionObj === "object" &&
                ("contact" in extractionObj) &&
                extractionObj.contact === null;
            const profileRef = (item.raw_profile?.profile || "").toString().trim() || name;
            const askForContactLink = (!waLink && isExplicitNullContact)
                ? buildWhatsAppLink(ASK_CONTACT_WHATSAPP_E164, buildAskForContactPrefillMessage(profileRef))
                : null;
            const discreetEmailLink = buildDiscreetEmailLink(profileRef);

            if (waLink) {
                contactRows.push(
                    `<div><strong>${escapeHtml(t("contact.whatsapp"))}:</strong> <a href="${waLink}" target="_blank" rel="noopener noreferrer">${escapeHtml(waDisplay)}</a></div>`
                );
            }
            if (d.contact?.phone) contactRows.push(`<div><strong>${escapeHtml(t("contact.phone"))}:</strong> ${escapeHtml(d.contact.phone)}</div>`);
            if (d.contact?.email) contactRows.push(`<div><strong>${escapeHtml(t("contact.email"))}:</strong> ${escapeHtml(d.contact.email)}</div>`);
            if (d.contact?.social) contactRows.push(`<div><strong>${escapeHtml(t("contact.social"))}:</strong> ${escapeHtml(d.contact.social)}</div>`);

            const notesTrim = (typeof notesValue === "string") ? notesValue.trim() : "";
            const extractionContactTrim = (typeof extractionContact === "string") ? extractionContact.trim() : "";
            if (notesTrim && notesTrim !== extractionContactTrim && (!waInfo || notesTrim !== waInfo.display)) {
                contactRows.push(`<div><strong>${escapeHtml(t("contact.notes"))}:</strong> ${escapeHtml(notesTrim)}</div>`);
            }
            if (contactRows.length) {
                html += `<div class="lb-section"><h3>${escapeHtml(t("sections.contact"))}</h3>${contactRows.join("")}</div>`;
            }
            if (waLink) {
                html += `<a href="${waLink}" target="_blank" rel="noopener noreferrer" class="cta-btn">${escapeHtml(t("contact.whatsappCta"))}</a>`;
            } else if (askForContactLink) {
                html += `<a href="${askForContactLink}" target="_blank" rel="noopener noreferrer" class="cta-btn">${escapeHtml(t("contact.askForContactCta"))}</a>`;
            }
            if (discreetEmailLink) {
                html += `<a href="${discreetEmailLink}" class="cta-btn cta-btn-email">${escapeHtml(t("contact.discreetEmailCta"))}</a>`;
            }
            if (d.contact?.phone) {
                html += `<a href="tel:${d.contact.phone}" style="display:block; text-align:center; margin-top:10px; color:#555; text-decoration:underline;">${escapeHtml(t("contact.call", { phone: d.contact.phone }))}</a>`;
            }

            document.getElementById('lb-details-content').innerHTML = html;
            initReviewsCarousel();
            document.getElementById('lightbox').classList.add('active');
            syncOverlayLock();
	        };

	        window.closeProfile = () => {
                exitLightboxMediaFullscreen();
	            document.getElementById('lightbox').classList.remove('active');
                syncOverlayLock();
	        };

        function updateLightboxMedia() {
            if (currentItemIndex < 0) return;
            if (!currentMediaEntries.length) return;
            const total = currentMediaEntries.length;
            currentMediaIndex = (currentMediaIndex + total) % total;
            const entry = currentMediaEntries[currentMediaIndex];
            const mainImg = document.getElementById('lb-main-img');
            const mainVideo = document.getElementById('lb-main-video');
            if (entry.type === "image") {
                mainVideo.pause();
                mainVideo.style.display = "none";
                mainImg.style.display = "block";
                mainImg.src = entry.src;
            } else {
                mainImg.style.display = "none";
                mainVideo.style.display = "block";
                mainVideo.src = entry.src;
                mainVideo.play().catch(() => {});
            }
            let activeEl = null;
            document.querySelectorAll('#lb-thumbs .lb-thumb').forEach((el, idx) => {
                const isActive = idx === currentMediaIndex;
                el.classList.toggle('active', isActive);
                if (isActive) activeEl = el;
            });
            if (activeEl) {
                activeEl.scrollIntoView({ block: 'nearest', inline: 'center' });
            }
        }

        window.switchMedia = (idx) => {
            currentMediaIndex = idx;
            updateLightboxMedia();
        };

        function cycleMedia(delta) {
            const lightbox = document.getElementById('lightbox');
            if (!lightbox.classList.contains('active')) return;
            if (!(currentMediaEntries && currentMediaEntries.length > 1)) return;
            currentMediaIndex += delta;
            updateLightboxMedia();
        }

        document.addEventListener('keydown', e => {
            const authActive = document.getElementById('auth-overlay')?.classList.contains('active');
            if (authActive) return;
            if (e.key === "Escape" && document.body.classList.contains("filters-open")) {
                closeFilters();
                return;
            }
            const disclaimerActive = document.getElementById('disclaimer-overlay')?.classList.contains('active');
            if (e.key === "Escape") {
                if (disclaimerActive) {
                    hideDisclaimer();
                    return;
                }
                const lightbox = document.getElementById('lightbox');
                if (lightbox?.classList.contains('active') && lightbox.classList.contains('media-fullscreen')) {
                    exitLightboxMediaFullscreen();
                    return;
                }
                closeProfile();
            }
            if (disclaimerActive) return;
            if (e.key === "ArrowRight") {
                e.preventDefault();
                cycleMedia(1);
            } else if (e.key === "ArrowLeft") {
                e.preventDefault();
                cycleMedia(-1);
            }
        });

        let lastLightboxSwipeAt = 0;

        // Swipe media left/right to cycle on mobile.
        (() => {
            const media = document.querySelector('.lb-media');
            if (!media) return;
            let startX = null;
            let startY = null;
            let pointerId = null;

            media.addEventListener('pointerdown', (e) => {
                if (!isMobileLightboxViewport()) return;
                const lightbox = document.getElementById('lightbox');
                if (!lightbox?.classList.contains('active')) return;
                if (!(currentMediaEntries && currentMediaEntries.length > 1)) return;
                pointerId = e.pointerId;
                startX = e.clientX;
                startY = e.clientY;
                try { media.setPointerCapture(pointerId); } catch (_) { /* ignore */ }
            });

            media.addEventListener('pointerup', (e) => {
                if (pointerId == null || e.pointerId !== pointerId) return;
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                pointerId = null;
                startX = null;
                startY = null;
                if (Math.abs(dx) < 50) return;
                if (Math.abs(dx) <= Math.abs(dy)) return;
                lastLightboxSwipeAt = Date.now();
                cycleMedia(dx < 0 ? 1 : -1);
            });

            media.addEventListener('pointercancel', () => {
                pointerId = null;
                startX = null;
                startY = null;
            });
        })();

        // Tap main image to go full-screen on mobile (ignore if it was a swipe).
        document.getElementById('lb-main-img')?.addEventListener('click', () => {
            if (Date.now() - lastLightboxSwipeAt < 400) return;
            toggleLightboxMediaFullscreen();
        });

        // Disclaimer controls
        document.getElementById("disclaimer-overlay")?.addEventListener("click", () => hideDisclaimer());
        document.getElementById("disclaimer-close")?.addEventListener("click", () => hideDisclaimer());
        document.getElementById("disclaimer-accept")?.addEventListener("click", () => hideDisclaimer());

        window.addEventListener("resize", () => syncOverlayLock());

        initLanguage();
        initAuthGate();
