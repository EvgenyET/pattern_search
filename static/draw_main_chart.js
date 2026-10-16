// draw_main_chart.js

/**
 * Отрисовка общего графика (вкладка 1)
 * @param {Array} data - Данные для отрисовки свечей
 * @param {Array} matches - Массив найденных паттернов для выделения
 * @param {Array} patternSample - Образец паттерна для выделения фиолетовым
 */
function drawMainChart(data, matches, patternSample) {
    const canvas = document.getElementById('main-chart');

    // Ограничение количества свечей для производительности (отображаем последние 10000)
    const maxCandles = 4000;
    let trimmedData = data;
    if (data.length > maxCandles) {
        trimmedData = data.slice(-maxCandles); // Берем последние maxCandles свечей
    }

    // Вычисляем смещение, чтобы правильно отобразить паттерны, индексы которых относятся к полному набору данных
    const offset = data.length - trimmedData.length;
    // Фильтруем совпадения, чтобы оставить только те, что попадают в отображаемый диапазон данных
    let trimmedMatches = matches.filter(m => m.start_index >= offset);

    // Настраиваем размер холста и очищаем его перед отрисовкой
    adjustCanvasSize(canvas, 1200, 800);

    const ctx = canvas.getContext('2d');
    ctx.save(); // Сохраняем текущее состояние контекста для возможности восстановления

    // Применяем трансформации панорамирования и масштабирования
    ctx.translate(panX, panY);
    ctx.scale(zoomLevel, zoomLevel);

    // Отрисовываем свечи общего графика
    drawCandlestick(ctx, trimmedData, 50, 50, 1100, 700, "Общий график", true, drawCandleMain);

    // Рисуем выделенные паттерны (совпадения) синим цветом, без учета будущих свечей
    drawHighlightedPatterns(ctx, trimmedData, trimmedMatches, drawCandleMain, 'blue', offset);

    // Рисуем образец паттерна фиолетовым цветом
    const patternGlobalIndex = data.length - patternSample.length; // Индекс начала образца паттерна в глобальных данных
    drawHighlightedPatterns(
        ctx,
        trimmedData,
        [{
            start_index: patternGlobalIndex,
            candles: patternSample
        }],
        drawCandleMain,
        'purple',
        offset,
        'Образец паттерна' // Добавляем подпись для образца паттерна
    );

    ctx.restore(); // Восстанавливаем состояние контекста, убирая трансформации для следующей отрисовки
}

/**
 * Выделение паттернов на общем графике цветом
 * @param {CanvasRenderingContext2D} ctx - Контекст 2D рисования
 * @param {Array} data - Данные графика
 * @param {Array} patterns - Массив паттернов для выделения
 * @param {function} drawCandleFunction - Функция отрисовки свечи
 * @param {string} color - Цвет выделения
 * @param {number} offset - Смещение для корректировки индексов паттернов
 * @param {string} customLabel - Пользовательская подпись для паттерна (необязательно)
 */
function drawHighlightedPatterns(ctx, data, patterns, drawCandleFunction, color, offset = 0, customLabel = null) {
    const candleWidth = 1100 / data.length; // Ширина одной свечи на графике
    const minPrice = Math.min(...data.map(d => d.low));   // Минимальная цена на графике
    const maxPrice = Math.max(...data.map(d => d.high));  // Максимальная цена на графике

    patterns.forEach((patternObj, patternIndex) => {
        const adjustedIndex = patternObj.start_index - offset; // Корректируем индекс начала паттерна с учетом смещения
        const pattern = patternObj.candles;                  // Свечи, составляющие паттерн

        pattern.forEach((candle, i) => {
            const x = 50 + (adjustedIndex + i) * candleWidth; // X координата для отрисовки свечи

            // Вычисляем Y координаты для open, high, low, close цены, масштабируя их под высоту графика
            const yOpen = 50 + scalePrice(candle.open, minPrice, maxPrice, 700, true);
            const yHigh = 50 + scalePrice(candle.high, minPrice, maxPrice, 700, true);
            const yLow = 50 + scalePrice(candle.low, minPrice, maxPrice, 700, true);
            const yClose = 50 + scalePrice(candle.close, minPrice, maxPrice, 700, true);

            // Отрисовываем свечу с заданным цветом выделения
            drawCandleFunction(ctx, x, yOpen, yHigh, yLow, yClose, candleWidth - 0.1, color);
        });

        // Отображаем подписи паттернов, если включена опция showPatternLabels
        if (showPatternLabels) {
            const labelX = 50 + adjustedIndex * candleWidth; // X координата для подписи
            const labelY = 50 + scalePrice(pattern[0].high, minPrice, maxPrice, 700, true); // Y координата для подписи (выше первой свечи паттерна)

            ctx.font = "12px Arial";
            ctx.fillStyle = color;
            const labelText = customLabel || `Паттерн ${patternIndex + 1}`; // Текст подписи, либо пользовательский, либо номер паттерна
            ctx.fillText(labelText, labelX, labelY - 10); // Рисуем текст подписи на холсте
        }
    });
}


/**
 * Функция отрисовки свечи (основной график) с учетом масштабирования и зазоров.
 * @param {CanvasRenderingContext2D} ctx - Контекст 2D рисования
 * @param {number} x - X координата для начала отрисовки свечи
 * @param {number} yOpen - Y координата для цены открытия
 * @param {number} yHigh - Y координата для максимальной цены
 * @param {number} yLow - Y координата для минимальной цены
 * @param {number} yClose - Y координата для цены закрытия
 * @param {number} baseWidth - Базовая ширина, доступная для свечи
 * @param {string} color - Цвет свечи (зеленый или красный)
 */
function drawCandleMain(ctx, x, yOpen, yHigh, yLow, yClose, baseWidth, color) {
    ctx.save(); // Сохраняем текущее состояние контекста
    ctx.lineWidth = 1 / zoomLevel; // Устанавливаем толщину линии с учетом масштаба, чтобы линии оставались 1px на экране
    ctx.fillStyle = color;

    // Новая логика расчета ширины тела свечи с ограничением зазора между телами не более 1 пикселя.
    // Определяем доступное пространство для одной свечи в пикселях (с учетом текущего зума)
    const deviceCandleSpace = baseWidth * zoomLevel;
    const minBodyWidthPixels = 3; // минимальная ширина тела свечи в пикселях
    let gap = 1; // максимальный зазор между телами свечей в пикселях

    // Если доступное пространство меньше минимально необходимого (тело + зазор)
    if (deviceCandleSpace < minBodyWidthPixels + gap) {
        gap = Math.max(0, deviceCandleSpace - minBodyWidthPixels); // Уменьшаем зазор до 0, если места совсем мало
    }

    // Итоговая ширина тела в пикселях
    let deviceBodyWidth = deviceCandleSpace - gap;
    if (deviceBodyWidth < minBodyWidthPixels) {
        deviceBodyWidth = minBodyWidthPixels; // Тело не может быть меньше минимальной ширины
    }

    // Переводим ширину тела обратно в логические координаты (без учета зума)
    const targetBodyWidth = deviceBodyWidth / zoomLevel;

    // Центрирование тела в пределах базовой ширины свечи
    const bodyX = x + (baseWidth - targetBodyWidth) / 2;
    const bodyY = Math.min(yOpen, yClose);
    const bodyHeight = Math.abs(yClose - yOpen);
    ctx.fillRect(bodyX, bodyY, targetBodyWidth, bodyHeight); // Рисуем тело свечи

    // Отрисовка фитилей (оставляем 1px толщиной независимо от зума)
    ctx.strokeStyle = color;
    ctx.lineWidth = 1 / zoomLevel; // Толщина фитиля также 1px на экране
    ctx.beginPath();
    const wickX = bodyX + targetBodyWidth / 2; // Центр фитиля совпадает с центром тела
    ctx.moveTo(wickX, yHigh); // Верхний фитиль от максимума цены
    ctx.lineTo(wickX, yLow);  // Нижний фитиль до минимума цены
    ctx.stroke(); // Рисуем фитиль

    ctx.restore(); // Восстанавливаем состояние контекста
}