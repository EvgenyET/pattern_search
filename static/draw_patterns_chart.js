// draw_patterns_chart.js

/**
 * Отрисовка вкладки «Паттерны» (вкладка 2)
 * @param {Array} original - Образец оригинального паттерна
 * @param {Array} matches - Массив найденных совпадений паттернов
 */
function drawCandlestickPatterns(original, matches) {
    const canvas = document.getElementById('candlestick-chart');

    // Настраиваем размер холста под количество паттернов, чтобы все поместились вертикально
    adjustCanvasSize(canvas, 1200, matches.length * 350);
    const ctx = canvas.getContext('2d');

    matches.forEach((patternObj, index) => {
        const pattern = patternObj.candles;        // Свечи, составляющие найденный паттерн
        const yOffset = index * 350 + 50;           // Вертикальное смещение для каждого паттерна

        // === Левая колонка: Оригинальный паттерн ===
        ctx.font = "16px Arial";
        ctx.fillStyle = "black";
        // Отрисовываем оригинальный паттерн слева
        drawCandlestick(ctx, original, 50, yOffset, 500, 200, `Оригинальный паттерн ${index + 1}`, false, drawCandlePattern);

        // === Правая колонка: Совпадение ===
        // Формируем расширенный паттерн, включая будущие свечи, если showFutureCandles = true
        const extendedPattern = [...pattern]; // Начинаем с копии свечей найденного паттерна

        if (showFutureCandles) {
            const futureStart = patternObj.start_index + pattern.length; // Индекс начала будущих свечей
            const futureEnd = futureStart + futureCandlesCount;       // Индекс конца будущих свечей
            if (futureStart < globalChartData.length) {
                const futureSlice = globalChartData.slice(futureStart, futureEnd); // Вырезаем будущие свечи из глобальных данных
                extendedPattern.push(...futureSlice); // Добавляем будущие свечи к расширенному паттерну
            }
        }

        // Определяем количество свечей паттерна для подсветки (обводки)
        // Подсветка свечей паттерна происходит ТОЛЬКО если showFutureCandles = true
        const highlightCount = showFutureCandles ? pattern.length : 0;

        ctx.font = "16px Arial";
        ctx.fillStyle = "black";
        // Отрисовываем найденное совпадение справа, с возможностью отображения будущих свечей
        drawCandlestick(
            ctx,
            extendedPattern,
            650,
            yOffset,
            500,
            200,
            `Совпадение ${index + 1}`, // Заголовок для совпадения
            false,
            drawCandlePattern, // Используем функцию отрисовки свечей для паттернов
            highlightCount    // Количество свечей для подсветки (обводки)
        );
    });
}

/**
 * Универсальная функция отрисовки свечного графика
 * @param {CanvasRenderingContext2D} ctx - Контекст 2D рисования
 * @param {Array} data - Данные для отрисовки свечей
 * @param {number} startX - X координата начала графика
 * @param {number} startY - Y координата начала графика
 * @param {number} width - Ширина графика
 * @param {number} height - Высота графика
 * @param {string} title - Заголовок графика
 * @param {boolean} useLogScale - Использовать логарифмическую шкалу цен или нет
 * @param {function} drawCandleFunction - Функция для отрисовки отдельной свечи
 * @param {number} highlightCount - Количество свечей для выделения (обводки)
 */
function drawCandlestick(ctx, data, startX, startY, width, height, title, useLogScale, drawCandleFunction, highlightCount = 0) {
    const candleSpace = width / data.length; // Вычисляем ширину, доступную для каждой свечи
    const prices = data.map(d => [d.open, d.high, d.low, d.close]).flat(); // Извлекаем все цены из данных
    const minPrice = Math.min(...prices); // Находим минимальную цену для масштабирования
    const maxPrice = Math.max(...prices); // Находим максимальную цену для масштабирования

    ctx.font = "16px Arial";
    ctx.fillText(title, startX, startY - 20); // Рисуем заголовок графика

    data.forEach((candle, i) => {
        const x = startX + i * candleSpace; // X координата для текущей свечи
        // Вычисляем Y координаты для open, high, low, close цены, масштабируя их под высоту графика
        const yOpen = startY + scalePrice(candle.open, minPrice, maxPrice, height, useLogScale);
        const yHigh = startY + scalePrice(candle.high, minPrice, maxPrice, height, useLogScale);
        const yLow = startY + scalePrice(candle.low, minPrice, maxPrice, height, useLogScale);
        const yClose = startY + scalePrice(candle.close, minPrice, maxPrice, height, useLogScale);

        const color = candle.close > candle.open ? 'green' : 'red'; // Цвет свечи зависит от направления цены

        // Определяем, нужно ли выделять свечу (обводить), проверяя индекс
        const highlight = (i < highlightCount);

        // Отрисовываем свечу, используя переданную функцию отрисовки свечи
        drawCandleFunction(ctx, x, yOpen, yHigh, yLow, yClose, candleSpace - 1, color, highlight);
    });
}

/**
 * Отрисовка свечи для вкладки «Паттерны».
 * @param {CanvasRenderingContext2D} ctx - Контекст 2D рисования
 * @param {number} x - X координата для начала отрисовки свечи
 * @param {number} yOpen - Y координата для цены открытия
 * @param {number} yHigh - Y координата для максимальной цены
 * @param {number} yLow - Y координата для минимальной цены
 * @param {number} yClose - Y координата для цены закрытия
 * @param {number} candleWidth - Ширина, доступная для свечи
 * @param {string} color - Цвет свечи (зеленый или красный)
 * @param {boolean} highlight - Нужно ли выделять свечу обводкой
 */
function drawCandlePattern(ctx, x, yOpen, yHigh, yLow, yClose, candleWidth, color, highlight = false) {
    // Тело свечи
    const bodyWidth = candleWidth - 4; // Ширина тела немного меньше общей ширины свечи для создания зазора
    const finalWidth = (bodyWidth < 1) ? 1 : bodyWidth; // Минимальная ширина тела - 1 пиксель

    // Фитиль свечи
    ctx.beginPath();
    ctx.moveTo(x + finalWidth / 2, yHigh);   // Начало фитиля (верхняя точка)
    ctx.lineTo(x + finalWidth / 2, yLow);    // Конец фитиля (нижняя точка)
    ctx.strokeStyle = color;                  // Цвет фитиля
    ctx.stroke();                             // Рисуем фитиль

    // Тело свечи
    ctx.fillStyle = color;                    // Цвет тела свечи
    const bodyTop = Math.min(yOpen, yClose);  // Верхняя Y координата тела (меньшая из open и close)
    const bodyHeight = Math.abs(yClose - yOpen); // Высота тела свечи (разница между open и close)
    ctx.fillRect(x, bodyTop, finalWidth, bodyHeight); // Рисуем тело свечи

    // Обводка тела свечи, если требуется highlight = true
    if (highlight) {
        ctx.save(); // Сохраняем текущие настройки контекста
        ctx.strokeStyle = patternHighlightColor; // Цвет обводки из настроек
        ctx.lineWidth = 2;                      // Толщина линии обводки
        ctx.strokeRect(x, bodyTop, finalWidth, bodyHeight); // Рисуем обводку вокруг тела свечи
        ctx.restore(); // Восстанавливаем настройки контекста
    }
}