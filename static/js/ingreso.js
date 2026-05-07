/* ============================================================
   DATOS DE LIBROS POR CARRERA (simulado — reemplazar con BD)
   ============================================================ */
const LIBROS = {
    "ISC": [
        { titulo: "Clean Code", autor: "Robert C. Martin", emoji: "💻", tema: "Programación" },
        { titulo: "The Pragmatic Programmer", autor: "Hunt & Thomas", emoji: "🛠️", tema: "Ingeniería de SW" },
        { titulo: "Diseño de Compiladores", autor: "Aho, Lam, Sethi", emoji: "⚙️", tema: "Compiladores" },
        { titulo: "Estructura de Datos", autor: "Cormen et al.", emoji: "📊", tema: "Algoritmos" },
        { titulo: "Python Crash Course", autor: "Eric Matthes", emoji: "🐍", tema: "Python" },
    ],
    "ISE": [
        { titulo: "Sistemas Embebidos con ARM", autor: "Joseph Yiu", emoji: "🔌", tema: "Hardware" },
        { titulo: "Electrónica Digital", autor: "Morris Mano", emoji: "⚡", tema: "Electrónica" },
        { titulo: "Microcontroladores PIC", autor: "Myke Predko", emoji: "🔧", tema: "Microcontroladores" },
    ],
    "IIA": [
        { titulo: "Inteligencia Artificial", autor: "Russell & Norvig", emoji: "🤖", tema: "IA" },
        { titulo: "Machine Learning", autor: "Aurélien Géron", emoji: "🧠", tema: "ML" },
        { titulo: "Deep Learning", autor: "Goodfellow et al.", emoji: "🔬", tema: "Deep Learning" },
    ],
    "IGA": [
        { titulo: "Gestión de la Calidad", autor: "William Edwards Deming", emoji: "📋", tema: "Gestión" },
        { titulo: "Administración", autor: "Stephen Robbins", emoji: "📈", tema: "Administración" },
    ],
    "DEFAULT": [
        { titulo: "El Arte de Comunicar", autor: "Thich Nhat Hanh", emoji: "🗣️", tema: "Comunicación" },
        { titulo: "Hábitos Atómicos", autor: "James Clear", emoji: "⭐", tema: "Desarrollo personal" },
        { titulo: "El Principito", autor: "Antoine de Saint-Exupéry", emoji: "🌹", tema: "Clásico" },
        { titulo: "Sapiens", autor: "Yuval Noah Harari", emoji: "🌍", tema: "Historia" },
    ]
};

// Variable global para controlar el temporizador de auto-cierre
let autoCloseTimer;
const TIEMPO_AUTO_CIERRE_MS = 6000; // 6 segundos

/* ============================================================
   LÓGICA PRINCIPAL — consulta real a Flask/MySQL
   ============================================================ */
async function intentarIngreso() {
    const nombre  = document.getElementById('inputNombre').value.trim();
    const control = document.getElementById('inputControl').value.trim();

    if (!nombre && !control) {
        sacudirFormulario();
        return;
    }

    // Estado de carga en el botón
    const btn = document.querySelector('.btn-primary');
    btn.disabled = true;
    btn.innerHTML = '<i class="ph ph-circle-notch ph-spin"></i> Buscando...';

    ocultarNotifError();

    try {
        const resp = await fetch('/buscar_alumno', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ no_control: control, nombre: nombre })
        });
        const data = await resp.json();

        if (data.encontrado) {
            mostrarBienvenida(data.alumno);
        } else {
            mostrarError();
        }
    } catch (err) {
        mostrarError();
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="ph ph-sign-in"></i> Ingresar';
    }
}

function mostrarError() {
    const el = document.getElementById('notifError');
    el.classList.remove('show');
    void el.offsetWidth; // reflow para re-animar
    el.classList.add('show');
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function ocultarNotifError() {
    document.getElementById('notifError').classList.remove('show');
}

function sacudirFormulario() {
    const card = document.querySelector('.form-card');
    card.style.animation = 'none';
    void card.offsetWidth;
    card.style.animation = 'shake 0.4s ease';
}

/* ---- Bienvenida ---- */
function mostrarBienvenida(usuario) {
    const carrera = usuario.carrera.toUpperCase();
    const pool    = LIBROS[carrera] || LIBROS["DEFAULT"];
    const libro   = pool[Math.floor(Math.random() * pool.length)];

    // Iniciales del avatar
    const iniciales = usuario.nombre.split(' ').slice(0,2).map(p => p[0]).join('');
    document.getElementById('wcAvatar').textContent  = iniciales;
    document.getElementById('wcNombre').textContent  = usuario.nombre;
    document.getElementById('wcMeta').textContent    = `${usuario.control} · ${usuario.carrera}`;

    // Libro
    document.getElementById('wcBookCover').textContent  = libro.emoji;
    document.getElementById('wcBookTitle').textContent  = libro.titulo;
    document.getElementById('wcBookAuthor').textContent = libro.autor;
    document.getElementById('wcBookBadge').innerHTML    =
        `<i class="ph ph-tag"></i> ${libro.tema}`;

    // Estilo de la portada según carrera
    const colores = {
        ISC: ['#1B396A','#2d64c8'], IIA: ['#4a1780','#7b4fd4'],
        ISE: ['#0f5a3a','#1d9e6e'], IGA: ['#7a3a00','#c9730a'],
        DEFAULT: ['#4a3200','#C9A84C']
    };
    const [c1, c2] = colores[carrera] || colores.DEFAULT;
    document.getElementById('wcBookCover').style.background =
        `linear-gradient(135deg, ${c1}, ${c2})`;

    // Lanzar partículas
    lanzarParticulas();

    // Mostrar overlay
    const overlay = document.getElementById('welcomeOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Iniciar temporizador y barra de progreso
    iniciarAutoCierre(TIEMPO_AUTO_CIERRE_MS);
}

function iniciarAutoCierre(duracion) {
    const barraFill = document.getElementById('wcTimerFill');
    
    // Reiniciar la barra visual
    if (barraFill) {
        barraFill.style.transition = 'none';
        barraFill.style.width = '100%';
        
        // Forzar reflow para que aplique el reseteo antes de animar
        void barraFill.offsetWidth; 
        
        // Iniciar animación
        barraFill.style.transition = `width ${duracion}ms linear`;
        barraFill.style.width = '0%';
    }

    // Limpiar cualquier timer anterior y crear uno nuevo
    clearTimeout(autoCloseTimer);
    autoCloseTimer = setTimeout(() => {
        cerrarBienvenida();
    }, duracion);
}

function cerrarBienvenida() {
    clearTimeout(autoCloseTimer); // Detener timer si el usuario cierra manualmente

    const overlay = document.getElementById('welcomeOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    
    // Limpiar form
    document.getElementById('inputNombre').value  = '';
    document.getElementById('inputControl').value = '';
    document.getElementById('inputCarrera').value = '';
}

// Cerrar con Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarBienvenida();
});

// Cerrar al click fuera
document.getElementById('welcomeOverlay').addEventListener('click', function(e) {
    if (e.target === this) cerrarBienvenida();
});

/* ---- Partículas ---- */
function lanzarParticulas() {
    const container = document.getElementById('wcParticles');
    container.innerHTML = '';
    const colors = ['#C9A84C','#e8c96d','#fff','#7eaaee','#4caf8c'];
    for (let i = 0; i < 22; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.cssText = `
            left: ${10 + Math.random() * 80}%;
            bottom: ${Math.random() * 30}%;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            width:  ${4 + Math.random() * 6}px;
            height: ${4 + Math.random() * 6}px;
            animation-delay: ${Math.random() * 0.6}s;
            animation-duration: ${0.8 + Math.random() * 0.8}s;
        `;
        container.appendChild(p);
    }
}

/* ============================================================
   RESTO DE LÓGICA (dropdown, reloj, tema)
   ============================================================ */
function toggleDropdown() {
    document.getElementById("adminDropdown").classList.toggle("show");
}
window.onclick = function(event) {
    if (!event.target.closest('.admin-dropdown-container'))
        document.querySelectorAll(".dropdown-menu").forEach(d => d.classList.remove('show'));
}

function updateClock() {
    const now = new Date();
    const sidebarClock = document.getElementById('sidebarClock');
    if (sidebarClock) {
        sidebarClock.textContent =
            String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
    }
}
updateClock();
setInterval(updateClock, 30000);

const THEME_KEY = 'lumina_theme';
function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem(THEME_KEY, t);
}
function toggleTheme() {
    applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}
(function() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved) applyTheme(saved);
    else if (window.matchMedia('(prefers-color-scheme: dark)').matches) applyTheme('dark');
})();