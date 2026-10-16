// main_logic.js

// =============================
// Настройки:
// =============================
let futureCandlesCount = 50;          // Сколько будущих свечей дорисовывать
let patternHighlightColor = '#0000FF'; // Цвет обводки паттерна
// =============================

// Флаг, показываем ли будущие свечи (false — нет, true — да).
let showFutureCandles = false;

// Кнопка для переключения «Показать будущее»
document.getElementById('toggle-future').addEventListener('click', () => {
    // Меняем флаг
    showFutureCandles = !showFutureCandles;
    // Перерисовываем вторую вкладку (Паттерны)
    drawCandlestickPatterns(globalPatternSample, globalMatches);
});

// Переключение вкладок
document.getElementById('btn-tab-1').addEventListener('click', () => switchTab('tab-1', 'btn-tab-1'));
document.getElementById('btn-tab-2').addEventListener('click', () => switchTab('tab-2', 'btn-tab-2'));

// Управление подписями паттернов
let showPatternLabels = true;
document.getElementById('toggle-labels').addEventListener('click', () => {
    showPatternLabels = !showPatternLabels;
    drawMainChart(globalChartData, globalMatches, globalPatternSample);
});

// Переменные для масштабирования и панорамирования
let zoomLevel = 1;        // Уровень зума
let panX = 0, panY = 0;   // Смещение по осям X и Y
let isDragging = false;   // Состояние перетаскивания мышью
let lastMouseX, lastMouseY;

// События масштабирования кнопками
document.getElementById('zoom-in').addEventListener('click', () => {
    zoomLevel *= 1.2;
    drawMainChart(globalChartData, globalMatches, globalPatternSample);
});

document.getElementById('zoom-out').addEventListener('click', () => {
    zoomLevel /= 1.2;
    drawMainChart(globalChartData, globalMatches, globalPatternSample);
});

// Управление панорамированием (перетаскивание мышью)
const canvas = document.getElementById('main-chart');
canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    lastMouseX = e.offsetX;
    lastMouseY = e.offsetY;
});

canvas.addEventListener('mousemove', (e) => {
    if (isDragging) {
        const dx = e.offsetX - lastMouseX;
        const dy = e.offsetY - lastMouseY;

        panX += dx;
        panY += dy;

        lastMouseX = e.offsetX;
        lastMouseY = e.offsetY;

        drawMainChart(globalChartData, globalMatches, globalPatternSample);
    }
});

canvas.addEventListener('mouseup', () => {
    isDragging = false;
});

canvas.addEventListener('mouseleave', () => {
    isDragging = false;
});

/**
 * Обработка событий масштабирования колесиком мыши
 */
canvas.addEventListener('wheel', (e) => {
    e.preventDefault(); // Предотвращаем прокрутку страницы

    const zoomIntensity = 0.1;
    const delta = e.deltaY < 0 ? 1 + zoomIntensity : 1 - zoomIntensity;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    panX = mouseX - ((mouseX - panX) / zoomLevel) * (zoomLevel * delta);
    panY = mouseY - ((mouseY - panY) / zoomLevel) * (zoomLevel * delta);

    zoomLevel *= delta;

    drawMainChart(globalChartData, globalMatches, globalPatternSample);
}, { passive: false });

// Функция переключения вкладок
function switchTab(tabId, btnId) {
    // Скрываем все вкладки и деактивируем все кнопки
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));

    // Активируем нужную вкладку и кнопку
    document.getElementById(tabId).classList.add('active');
    document.getElementById(btnId).classList.add('active');
}

// Глобальные переменные для хранения данных графика
let globalChartData = [];
let globalMatches = [];
let globalPatternSample = [];

/**
 * Загрузка JSON данных из файла 'candlestick_patterns.json'
 */
fetch('candlestick_patterns.json')
    .then(response => response.json())
    .then(data => {
        // Сохраняем загруженные данные в глобальные переменные
        globalChartData = data.main_chart.prices;
        globalMatches = data.matches;
        globalPatternSample = data.original_pattern;

        // Отрисовываем графики для первой и второй вкладок после загрузки данных
        drawMainChart(globalChartData, globalMatches, globalPatternSample); // Первая вкладка - Основной график
        drawCandlestickPatterns(globalPatternSample, globalMatches);       // Вторая вкладка - Паттерны
    });

// Настройка и очистка холста
function adjustCanvasSize(canvas, width, height) {
    // Устанавливаем размеры холста
    canvas.width = width;
    canvas.height = height;
    // Получаем контекст 2D рисования
    const ctx = canvas.getContext('2d');
    // Очищаем холст
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// Масштабирование цены для отрисовки на графике
function scalePrice(price, min, max, height, useLogScale) {
    if (useLogScale) {
        // Логарифмическое масштабирование
        return height - ((Math.log(price) - Math.log(min))) / (Math.log(max) - Math.log(min)) * height;
    }
    // Линейное масштабирование
    return ((max - price) / (max - min)) * height;
}

// Глобальные переменные для хранения исходных состояний зума и панорамирования
let initialZoomLevel = 1; // Начальный уровень зума
let initialPanX = 0;      // Начальное смещение по X
let initialPanY = 0;      // Начальное смещение по Y

// Кнопка сброса состояния графика
document.getElementById('reset-chart').addEventListener('click', resetChartState);

// Функция сброса масштаба и панорамирования графика к исходным значениям
function resetChartState() {
    zoomLevel = initialZoomLevel;
    panX = initialPanX;
    panY = initialPanY;
    drawMainChart(globalChartData, globalMatches, globalPatternSample);
}